#!/usr/bin/env python3
"""Resolve the references that Crossref's bibliographic search could not match.

Crossref search struggles with some very highly cited papers and does not index
venues such as JMLR at all.  This script takes the keys left UNRESOLVED by
``build_bibliography.py``, looks them up in OpenAlex by title, verifies the
first-author surname and publication year, and appends verified BibTeX entries
to ``references.bib``.

An OpenAlex API key is required and is read from ``OPENALEX_API_KEY``.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from difflib import SequenceMatcher

API = "https://api.openalex.org/works"
KEY = os.environ.get("OPENALEX_API_KEY")

# key, title, expected first-author surname (empty for consortium papers), year
PENDING: list[tuple[str, str, str, int]] = [
    ("sayers2024", "Database resources of the National Center for Biotechnology Information", "Sayers", 2024),
    ("uniprot2023", "UniProt: the Universal Protein Knowledgebase in 2023", "", 2023),
    ("burley2023", "RCSB Protein Data Bank (RCSB.org): delivery of experimentally-determined PDB structures alongside one million computed structure models of proteins from artificial intelligence/machine learning", "Burley", 2023),
    ("cunningham2022", "Ensembl 2022", "Cunningham", 2022),
    ("ashburner2000", "Gene ontology: tool for the unification of biology", "Ashburner", 2000),
    ("go2023", "The Gene Ontology knowledgebase in 2023", "", 2023),
    ("milacic2024", "The Reactome Pathway Knowledgebase 2024", "Milacic", 2024),
    ("nurk2022", "The complete sequence of a human genome", "Nurk", 2022),
    ("lander2001", "Initial sequencing and analysis of the human genome", "Lander", 2001),
    ("venter2001", "The Sequence of the Human Genome", "Venter", 2001),
    ("jumper2021", "Highly accurate protein structure prediction with AlphaFold", "Jumper", 2021),
    ("baek2021", "Accurate prediction of protein structures and interactions using a three-track neural network", "Baek", 2021),
    ("abramson2024", "Accurate structure prediction of biomolecular interactions with AlphaFold 3", "Abramson", 2024),
    ("gentleman2004", "Bioconductor: open software development for computational biology and bioinformatics", "Gentleman", 2004),
    ("harris2020", "Array programming with NumPy", "Harris", 2020),
    ("virtanen2020", "SciPy 1.0: fundamental algorithms for scientific computing in Python", "Virtanen", 2020),
    ("wilkinson2016", "The FAIR Guiding Principles for scientific data management and stewardship", "Wilkinson", 2016),
    ("1000g2015", "A global reference for human genetic variation", "", 2015),
    ("tate2019", "COSMIC: the Catalogue Of Somatic Mutations In Cancer", "Tate", 2019),
    ("alexandrov2020", "The repertoire of mutational signatures in human cancer", "Alexandrov", 2020),
    ("robertson2017", "Comprehensive Molecular Characterization of Muscle-Invasive Bladder Cancer", "Robertson", 2017),
    ("icgc2020", "Pan-cancer analysis of whole genomes", "", 2020),
    ("whirlcarrillo2021", "An Evidence-Based Framework for Evaluating Pharmacogenomics Knowledge for Personalized Medicine", "Whirl-Carrillo", 2021),
    ("tegally2022", "The evolving SARS-CoV-2 epidemic in Africa: Insights from rapidly expanding genomic surveillance", "Tegally", 2022),
    ("h3africa2014", "Enabling the genomic revolution in Africa", "", 2014),
]

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP = {"a", "an", "the", "of", "for", "and", "in", "to", "on", "with", "using", "from", "by"}


def tokens(text: str) -> list[str]:
    plain = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return TOKEN_RE.findall(re.sub(r"<[^>]+>", " ", plain))


def title_score(expected: str, found: str) -> float:
    exp_t = [t for t in tokens(expected) if t not in STOP]
    got_t = [t for t in tokens(found) if t not in STOP]
    if not exp_t or not got_t:
        return 0.0
    containment = len(set(exp_t) & set(got_t)) / min(len(set(exp_t)), len(set(got_t)))
    n = min(len(" ".join(exp_t)), len(" ".join(got_t)))
    prefix = SequenceMatcher(None, " ".join(exp_t)[:n], " ".join(got_t)[:n]).ratio()
    return 0.6 * containment + 0.4 * prefix


def fetch(title: str) -> list[dict]:
    params = {"filter": f"title.search:{title}", "per-page": "8", "api_key": KEY}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    delay = 2.0
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "practical-bioinformatics-book/1.0"})
            with urllib.request.urlopen(req, timeout=60) as fh:
                return json.load(fh)["results"]
        except Exception as exc:  # noqa: BLE001
            if attempt == 4:
                raise
            time.sleep(delay)
            delay *= 1.8
    return []


def escape(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return (text.replace("&", r"\&").replace("%", r"\%")
            .replace("_", r"\_").replace("#", r"\#"))


def to_bibtex(key: str, work: dict) -> str:
    authors = " and ".join(
        f"{a['author']['display_name'].split()[-1]}, {' '.join(a['author']['display_name'].split()[:-1])}".strip(", ")
        for a in work.get("authorships", [])[:40]
        if a.get("author", {}).get("display_name")
    )
    venue = ""
    loc = work.get("primary_location") or {}
    if loc.get("source"):
        venue = loc["source"].get("display_name", "")
    biblio = work.get("biblio") or {}
    pages = ""
    if biblio.get("first_page"):
        pages = biblio["first_page"]
        if biblio.get("last_page") and biblio["last_page"] != biblio["first_page"]:
            pages += f"--{biblio['last_page']}"
    fields = [
        f"  author = {{{authors}}}",
        f"  title = {{{{{escape(work['title'])}}}}}",
        f"  year = {{{work['publication_year']}}}",
    ]
    if venue:
        fields.append(f"  journal = {{{escape(venue)}}}")
    if biblio.get("volume"):
        fields.append(f"  volume = {{{biblio['volume']}}}")
    if biblio.get("issue"):
        fields.append(f"  number = {{{biblio['issue']}}}")
    if pages:
        fields.append(f"  pages = {{{pages}}}")
    if work.get("doi"):
        fields.append(f"  doi = {{{work['doi'].replace('https://doi.org/', '')}}}")
    return f"@article{{{key},\n" + ",\n".join(fields) + "\n}\n"


def main() -> int:
    if not KEY:
        print("OPENALEX_API_KEY is not set; cannot resolve the remaining references.")
        return 1
    resolved, failed, rows = [], [], []
    for key, title, surname, year in PENDING:
        try:
            works = fetch(title)
        except Exception as exc:  # noqa: BLE001
            failed.append((key, f"query error: {exc}"))
            continue
        best, best_score = None, 0.0
        for work in works:
            if not work.get("title") or not work.get("publication_year"):
                continue
            if abs(work["publication_year"] - year) > 1:
                continue
            if surname:
                names = [tokens(a["author"]["display_name"])[-1]
                         for a in work.get("authorships", [])
                         if tokens(a.get("author", {}).get("display_name", ""))]
                if tokens(surname)[-1] not in names:
                    continue
            score = title_score(title, work["title"])
            if score > best_score:
                best, best_score = work, score
        if best is None or best_score < 0.85:
            failed.append((key, f"best match {best_score:.2f}: "
                                f"{(best or {}).get('title', 'none')[:70]}"))
            time.sleep(0.4)
            continue
        resolved.append(to_bibtex(key, best))
        rows.append((key, (best.get("doi") or "").replace("https://doi.org/", ""),
                     best["publication_year"], round(best_score, 3), best["title"][:90]))
        time.sleep(0.4)

    if resolved:
        with open("references.bib", "a") as fh:
            fh.write("\n% --- resolved via OpenAlex ---------------------------------------\n")
            fh.write("\n".join(resolved))
    with open("scripts/bibliography_report.tsv", "a") as fh:
        for row in rows:
            fh.write("\t".join(str(c) for c in row) + "\tOpenAlex\n")
        for key, why in failed:
            fh.write(f"{key}\tSTILL-UNRESOLVED\t\t\t{why}\n")
    print(f"OpenAlex resolved {len(resolved)}/{len(PENDING)}")
    for row in rows:
        print(f"  {row[0]:<20} {row[1]:<32} {row[3]}  {row[4][:60]}")
    if failed:
        print("\nstill unresolved:")
        for key, why in failed:
            print(f"  {key}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Add or correct bibliography entries, with the publication venue verified.

Two entries in the first build of ``references.bib`` resolved to digest items in
*Yearbook of Paediatric Endocrinology* that share a title with the article the
book actually cites. This script resolves each entry against OpenAlex, **checks
that the venue matches the expectation**, and only then writes it, replacing any
existing entry with the same key. Entries are finished by fetching the
registration agency's own BibTeX for the chosen DOI.

Requires OPENALEX_API_KEY.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher

API = "https://api.openalex.org/works"
KEY = os.environ.get("OPENALEX_API_KEY")
UA = {"User-Agent": "practical-bioinformatics-book/1.0"}

# key, title, first-author surname, year, venue substring that must appear
WANTED: list[tuple[str, str, str, int, str]] = [
    # --- corrections: these two resolved to the wrong publication ------------
    ("liao2023", "A draft human pangenome reference", "Liao", 2023, "Nature"),
    ("karczewski2020", "The mutational constraint spectrum quantified from variation in humans",
     "Karczewski", 2020, "Nature"),
    # --- gaps reported by the chapter authors --------------------------------
    # The NCBI and PharmGKB resource papers. Neither was surfaced by the earlier
    # Crossref pass, and both need the venue check below to avoid the annual
    # NAR database issues and the review literature that share their wording.
    ("sayers2021", "Database resources of the national center for biotechnology information",
     "Sayers", 2021, "Nucleic Acids Research"),
    ("whirlcarrillo2021", "An Evidence-Based Framework for Evaluating Pharmacogenomics Knowledge for Personalized Medicine",
     "Whirl-Carrillo", 2021, "Clinical Pharmacology"),
    ("virtanen2020", "SciPy 1.0: fundamental algorithms for scientific computing in Python",
     "Virtanen", 2020, "Nature Methods"),
    ("gotoh1982", "An improved algorithm for matching biological sequences", "Gotoh", 1982,
     "Journal of Molecular Biology"),
    ("li2018minimap2", "Minimap2: pairwise alignment for nucleotide sequences", "Li", 2018,
     "Bioinformatics"),
    ("arita2021", "The international nucleotide sequence database collaboration", "Arita", 2021,
     "Nucleic Acids Research"),
    ("mckinney2010", "Data Structures for Statistical Computing in Python", "McKinney", 2010,
     "Proceedings of the Python in Science Conference"),
    ("csardi2006", "The igraph software package for complex network research", "Csardi", 2006,
     "InterJournal"),
    ("blondel2008", "Fast unfolding of communities in large networks", "Blondel", 2008,
     "Journal of Statistical Mechanics"),
    ("girvan2002", "Community structure in social and biological networks", "Girvan", 2002,
     "Proceedings of the National Academy of Sciences"),
    ("broido2019", "Scale-free networks are rare", "Broido", 2019, "Nature Communications"),
    ("mcinnes2018", "UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction",
     "McInnes", 2018, ""),
    ("ambroise2002", "Selection bias in gene extraction on the basis of microarray gene-expression data",
     "Ambroise", 2002, "Proceedings of the National Academy of Sciences"),
    ("simon2003", "Pitfalls in the use of DNA microarray data for diagnostic and prognostic classification",
     "Simon", 2003, "Journal of the National Cancer Institute"),
    ("brooks2011", "Conservation of an RNA regulatory map between Drosophila and mammals", "Brooks", 2011,
     "Genome Research"),
    ("fraser1995", "The Minimal Gene Complement of Mycoplasma genitalium", "Fraser", 1995, "Science"),
    ("noble2009", "A Quick Guide to Organizing Computational Biology Projects", "Noble", 2009,
     "PLoS Computational Biology"),
    ("erlich2018", "Identity inference of genomic data using long-range familial searches", "Erlich", 2018,
     "Science"),
    ("carroll2020", "The CARE Principles for Indigenous Data Governance", "Carroll", 2020,
     "Data Science Journal"),
    ("fortuno2021", "Specifications of the ACMG/AMP variant interpretation guidelines for germline TP53 variants",
     "Fortuno", 2021, "Human Mutation"),
    ("giacomelli2018", "Mutational processes shape the landscape of TP53 mutations in human cancer",
     "Giacomelli", 2018, "Nature Genetics"),
    ("kato2003", "Understanding the function-structure and function-mutation relationships of p53 tumor suppressor protein by high-resolution missense mutation analysis",
     "Kato", 2003, "Proceedings of the National Academy of Sciences"),
]

# Works with no registered DOI. Searching for these returns unrelated records that
# happen to share wording, so they are written from the publisher's own listing.
MANUAL: dict[str, str] = {
    "csardi2006": """@article{csardi2006,
  author = {Csardi, Gabor and Nepusz, Tamas},
  title = {{The igraph software package for complex network research}},
  year = {2006},
  journal = {InterJournal, Complex Systems},
  pages = {1695},
  note = {No DOI is registered for this article}
}
""",
    "dayhoff1978": """@incollection{dayhoff1978,
  author = {Dayhoff, Margaret O. and Schwartz, Robert M. and Orcutt, Bruce C.},
  title = {{A model of evolutionary change in proteins}},
  booktitle = {Atlas of Protein Sequence and Structure},
  volume = {5},
  number = {Suppl. 3},
  pages = {345--352},
  publisher = {National Biomedical Research Foundation},
  address = {Washington, DC},
  year = {1978},
  note = {No DOI is registered for this volume}
}
""",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP = {"a", "an", "the", "of", "for", "and", "in", "to", "on", "with", "using", "from", "by"}


# OpenAlex returns names such as "Whirl\u2010Carrillo" with a Unicode hyphen.
# Stripping to ASCII would delete it and fuse the two name parts into one token,
# so dashes are normalised to a plain hyphen first and then act as separators.
DASHES = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\u00ad"), "-")


def tokens(text: str) -> list[str]:
    plain = (text or "").translate(DASHES)
    plain = unicodedata.normalize("NFKD", plain).encode("ascii", "ignore").decode().lower()
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


def venue_of(work: dict) -> str:
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    return source.get("display_name", "") or ""


def query_forms(title: str) -> list[str]:
    """Query strings to try, in order.

    OpenAlex rejects a title.search filter containing a comma and treats a hyphen
    as an operator, but stripping punctuation also breaks titles whose distinctive
    tokens are numeric ("SciPy 1.0", "141,456"). So each title is tried as written,
    then with commas removed, then with all punctuation reduced to spaces.
    """
    forms = [title, title.replace(",", "")]
    forms.append(re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ]+", " ", title)).strip())
    out = []
    for form in forms:
        if form and form not in out:
            out.append(form)
    return out


def search_one(query: str) -> list[dict]:
    params = {"filter": f"title.search:{query}", "per-page": "15", "api_key": KEY}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    delay = 2.0
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as fh:
                return json.load(fh)["results"]
        except urllib.error.HTTPError as exc:
            if exc.code == 400:
                return []          # malformed filter for this form; caller tries the next
            if attempt == 3:
                raise
            time.sleep(delay)
            delay *= 1.8
        except Exception:  # noqa: BLE001
            if attempt == 3:
                raise
            time.sleep(delay)
            delay *= 1.8
    return []


def bibtex_for(doi: str) -> str | None:
    headers = dict(UA)
    headers["Accept"] = "application/x-bibtex; charset=utf-8"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(
                urllib.request.Request("https://doi.org/" + doi, headers=headers), timeout=45
            ) as fh:
                text = fh.read().decode("utf-8", "replace")
            return text if "@" in text and re.search(r"title\s*=", text, re.I) else None
        except Exception:  # noqa: BLE001
            time.sleep(1.5 * (attempt + 1))
    return None


def rekey(bibtex: str, key: str) -> str:
    body = re.sub(r"^@(\w+)\s*\{[^,]*,", lambda m: f"@{m.group(1).lower()}{{{key},",
                  bibtex.strip(), count=1)
    return body + "\n"


def from_openalex(key: str, work: dict) -> str:
    authors = " and ".join(
        f"{a['author']['display_name'].split()[-1]}, {' '.join(a['author']['display_name'].split()[:-1])}".strip(", ")
        for a in work.get("authorships", [])[:30]
        if a.get("author", {}).get("display_name")
    )
    biblio = work.get("biblio") or {}
    fields = [f"  author = {{{authors}}}",
              f"  title = {{{{{work['title']}}}}}",
              f"  year = {{{work['publication_year']}}}"]
    if venue_of(work):
        fields.append(f"  journal = {{{venue_of(work)}}}")
    for src, dst in (("volume", "volume"), ("issue", "number")):
        if biblio.get(src):
            fields.append(f"  {dst} = {{{biblio[src]}}}")
    if biblio.get("first_page"):
        pages = biblio["first_page"]
        if biblio.get("last_page") and biblio["last_page"] != biblio["first_page"]:
            pages += f"--{biblio['last_page']}"
        fields.append(f"  pages = {{{pages}}}")
    if work.get("doi"):
        fields.append(f"  doi = {{{work['doi'].replace('https://doi.org/', '')}}}")
    return f"@article{{{key},\n" + ",\n".join(fields) + "\n}\n"



def split_entries(bib: str) -> tuple[str, list[tuple[str, str]]]:
    """Split a .bib file into its header and a list of (key, text) pairs.

    Entries are delimited by a line starting with ``@``, not by a closing brace:
    BibTeX served by the registration agencies puts the whole record on one line
    and ends it with `` }``, so a brace-based pattern silently swallows the
    entries that follow.
    """
    starts = [m.start() for m in re.finditer(r"^@\w+", bib, re.M)]
    if not starts:
        return bib, []
    header = bib[:starts[0]]
    bounds = starts + [len(bib)]
    out = []
    for i in range(len(starts)):
        text = bib[bounds[i]:bounds[i + 1]]
        key = re.match(r"@\w+\s*\{\s*([^,\s]+)", text).group(1)
        out.append((key, text))
    return header, out


def join_entries(header: str, entries: list[tuple[str, str]]) -> str:
    return header + "\n".join(text.rstrip("\n") + "\n" for _, text in entries)


def main() -> int:
    if not KEY:
        print("OPENALEX_API_KEY is not set")
        return 1
    header, entries = split_entries(open("references.bib").read())
    index = {key: i for i, (key, _) in enumerate(entries)}
    added, replaced, failed = [], [], []

    def replace_entry_inplace(key: str, entry: str) -> bool:
        if key in index:
            entries[index[key]] = (key, entry)
            return True
        entries.append((key, entry))
        index[key] = len(entries) - 1
        return False

    for key, title, surname, year, venue_hint in WANTED:
        if key in MANUAL:
            continue        # written by hand below; searching finds unrelated records
        works = []
        try:
            for form in query_forms(title):
                works = search_one(form)
                if works:
                    break
        except Exception as exc:  # noqa: BLE001
            failed.append((key, f"query error: {exc}"))
            continue
        def acceptable(candidates: list[dict]) -> tuple[dict | None, float]:
            chosen, chosen_score = None, 0.0
            for work in candidates:
                if not work.get("title") or not work.get("publication_year"):
                    continue
                if abs(work["publication_year"] - year) > 1:
                    continue
                names = [tokens(a["author"]["display_name"])[-1]
                         for a in work.get("authorships", [])
                         if tokens(a.get("author", {}).get("display_name", ""))]
                if surname and tokens(surname)[-1] not in names:
                    continue
                if venue_hint and venue_hint.lower() not in venue_of(work).lower():
                    continue      # the venue check the first build lacked
                score = title_score(title, work["title"])
                if score > chosen_score:
                    chosen, chosen_score = work, score
            return chosen, chosen_score

        best, best_score = acceptable(works)
        if best is None or best_score < 0.80:
            for form in query_forms(title)[1:]:
                more = search_one(form)
                candidate, candidate_score = acceptable(more)
                if candidate is not None and candidate_score > best_score:
                    best, best_score = candidate, candidate_score
                if best is not None and best_score >= 0.80:
                    break
        if best is None or best_score < 0.80:
            failed.append((key, f"no venue-matching record (best {best_score:.2f})"))
            time.sleep(0.4)
            continue

        doi = (best.get("doi") or "").replace("https://doi.org/", "")
        entry = None
        if doi:
            fresh = bibtex_for(doi)
            if fresh:
                entry = rekey(fresh, key)
        if entry is None:
            entry = from_openalex(key, best)

        if replace_entry_inplace(key, entry):
            replaced.append((key, doi, venue_of(best)))
        else:
            added.append((key, doi, venue_of(best)))
        time.sleep(0.4)

    for key, entry in MANUAL.items():
        if replace_entry_inplace(key, entry):
            replaced.append((key, "no DOI registered", "written by hand"))
        else:
            added.append((key, "no DOI registered", "written by hand"))

    bib = join_entries(header, entries)
    open("references.bib", "w").write(bib)
    keys = sorted(key for key, _ in entries)
    open("scripts/citation_keys.txt", "w").write("\n".join(keys) + "\n")

    print(f"replaced {len(replaced)}, added {len(added)}, failed {len(failed)}; "
          f"{len(keys)} entries now in references.bib")
    for label, rows in (("REPLACED", replaced), ("ADDED", added)):
        for key, doi, venue in rows:
            print(f"  {label:<9} {key:<18} {doi:<34} {venue[:40]}")
    for key, why in failed:
        print(f"  FAILED    {key:<18} {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

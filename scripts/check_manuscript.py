#!/usr/bin/env python3
"""Whole-manuscript consistency checks for
*Practical Approach to Learning Bioinformatics*.

Run from the book root:

    python scripts/check_manuscript.py            # report
    python scripts/check_manuscript.py --strict   # exit non-zero on any error

Checks performed
----------------
structure   every chapter has the required sections in the required order
headings    sentence case, no manual numbering, no depth beyond level 3
labels      every @fig-/@tbl-/@sec- reference resolves; every figure chunk is captioned
chunks      no file mixes executable {r} and {python}; eval:false chunks are flagged
citations   every @key exists in references.bib; unused keys are listed
data        every book_data() call names a file present in data/MANIFEST.tsv
spelling    British forms, and the phrases STYLE.md forbids
placeholders  TODO/TBD/path/to/... and other leftovers
length      body word count against the 4,000-5,500 word target
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHAPTER_GLOB = re.compile(r"part[1-8]/\d\d-.*\.qmd$")
REQUIRED_SECTIONS = ["Summary", "Exercises", "Solutions", "Further reading"]

FORBIDDEN_PHRASES = [
    "In this chapter, we will explore", "Let's dive in", "the fascinating world of",
    "lorem ipsum", "TODO", "TBD", "FIXME", "path/to/", "your_file", "example.com",
    "XXX", "<insert", "[insert",
]

# American -> British forms that must not appear in prose
AMERICANISMS = {
    "analyze": "analyse", "analyzed": "analysed", "analyzing": "analysing",
    "analyzes": "analyses", "normalize": "normalise", "normalized": "normalised",
    "normalizing": "normalising", "normalization": "normalisation",
    "summarize": "summarise", "summarized": "summarised", "summarizing": "summarising",
    "visualize": "visualise", "visualized": "visualised", "visualization": "visualisation",
    "characterize": "characterise", "characterized": "characterised",
    "organize": "organise", "organized": "organised", "organization": "organisation",
    "recognize": "recognise", "recognized": "recognised",
    "minimize": "minimise", "maximize": "maximise", "optimize": "optimise",
    "optimized": "optimised", "optimization": "optimisation",
    "color": "colour", "colors": "colours", "behavior": "behaviour",
    "center": "centre", "centered": "centred", "modeling": "modelling",
    "labeled": "labelled", "labeling": "labelling", "catalog": "catalogue",
    "program": None,  # legitimate in computing; ignored
}

CODE_FENCE = re.compile(r"^```.*?^```", re.M | re.S)
CHUNK = re.compile(r"^```\{(\w+)\}\n(.*?)^```\s*$", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]+`")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")


def strip_code(text: str) -> str:
    """Prose only: code fences and inline code removed."""
    return INLINE_CODE.sub(" ", CODE_FENCE.sub(" ", text))


def qmd_files() -> list[str]:
    out = []
    for folder, _, names in os.walk(ROOT):
        if any(skip in folder for skip in ("_book", "_freeze", ".quarto", "site_libs")):
            continue
        for name in sorted(names):
            if name.endswith(".qmd"):
                rel = os.path.relpath(os.path.join(folder, name), ROOT)
                if rel.startswith("TEMPLATE"):
                    continue
                out.append(rel)
    return sorted(out)


def bib_keys() -> set[str]:
    path = os.path.join(ROOT, "references.bib")
    if not os.path.exists(path):
        return set()
    return set(re.findall(r"^@\w+\s*\{\s*([^,\s]+)\s*,", open(path).read(), re.M))


def manifest_files() -> set[str]:
    path = os.path.join(ROOT, "data", "MANIFEST.tsv")
    if not os.path.exists(path):
        return set()
    with open(path) as fh:
        next(fh, None)
        files = {line.split("\t")[0] for line in fh if line.strip()}
    files.add("MANIFEST.tsv")   # chapters legitimately read the manifest itself
    return files


def check_file(rel: str, text: str, keys: set[str], data: set[str], rep: Report,
               labels: dict, refs: dict) -> dict:
    prose = strip_code(text)
    is_chapter = bool(CHAPTER_GLOB.search(rel))
    stats = {"file": rel, "words": len(prose.split()), "figures": 0, "citations": set()}

    # --- structure -----------------------------------------------------------
    headings = re.findall(r"^(#{1,6})\s+(.*)$", text, re.M)
    if is_chapter:
        titles = [h[1] for h in headings]
        for required in REQUIRED_SECTIONS:
            if not any(t.startswith(required) for t in titles):
                rep.error(rel, f"missing required section '{required}'")
        if ".objectives" not in text:
            rep.error(rel, "missing the .objectives learning-outcomes block")
        order = [i for required in REQUIRED_SECTIONS
                 for i, t in enumerate(titles) if t.startswith(required)]
        if order != sorted(order):
            rep.error(rel, "required sections are out of order "
                           "(Summary, Exercises, Solutions, Further reading)")

    for hashes, title in headings:
        clean = re.sub(r"\{.*?\}", "", title).strip()
        if len(hashes) > 3:
            rep.error(rel, f"heading deeper than level 3: '{clean[:50]}'")
        if re.match(r"^\d+(\.\d+)*\s", clean):
            rep.error(rel, f"manually numbered heading: '{clean[:50]}'")
        if re.match(r"^Chapter\s+\d+", clean, re.I) and "16-chapter-summaries" not in rel:
            # the review chapter summarises each chapter by name, so there the
            # heading is the cross-reference rather than a numbering slip
            rep.error(rel, f"heading contains a chapter number: '{clean[:50]}'")
        words = [w for w in clean.split() if w.isalpha() and len(w) > 3]
        capitalised = [w for w in words[1:] if w[0].isupper() and not w.isupper()]
        if len(capitalised) >= 2:
            rep.warn(rel, f"heading may be in title case: '{clean[:50]}'")
        if clean.endswith("?"):
            rep.warn(rel, f"heading is a question: '{clean[:50]}'")

    # --- chunks --------------------------------------------------------------
    langs_exec = set()
    for match in CHUNK.finditer(text):
        lang, body = match.group(1).lower(), match.group(2)
        options = dict(re.findall(r"^#\|\s*([\w.-]+):\s*(.+)$", body, re.M))
        evaluated = options.get("eval", "true").strip().lower() not in {"false", "f", "no"}
        label = options.get("label", "")
        if lang in {"r", "python"} and evaluated:
            langs_exec.add(lang)
        if label.startswith("fig-"):
            stats["figures"] += 1
            if "fig-cap" not in options:
                rep.error(rel, f"figure chunk '{label}' has no fig-cap")
        if label.startswith("tbl-") and "tbl-cap" not in options:
            rep.error(rel, f"table chunk '{label}' has no tbl-cap")
        if label:
            if label in labels:
                rep.error(rel, f"duplicate chunk label '{label}' (also in {labels[label]})")
            labels[label] = rel
        elif evaluated and lang in {"r", "python"}:
            rep.warn(rel, "an executable chunk has no label")
    if len(langs_exec) > 1:
        rep.error(rel, "file mixes executable {r} and {python} chunks "
                       "(STYLE.md section 4 forbids this)")

    # --- cross-references ----------------------------------------------------
    for anchor in re.findall(r"\{#((?:fig|tbl|sec|eq|lst)-[\w-]+)\}", text):
        if anchor in labels and labels[anchor] != rel:
            rep.error(rel, f"duplicate anchor '{anchor}' (also in {labels[anchor]})")
        labels[anchor] = rel
    for ref in re.findall(r"@((?:fig|tbl|sec|eq|lst)-[\w-]+)", text):
        refs[ref].append(rel)

    # --- citations -----------------------------------------------------------
    # Match against the keys references.bib actually defines, rather than guessing
    # at their shape: a year-pattern heuristic silently misses keys such as
    # `fastqc` and `rcoreteam` that carry no year.
    cited = set()
    for token in re.findall(r"@([A-Za-z][\w:.-]*)", prose):
        token = token.rstrip(".,;:")
        if token.startswith(("fig-", "tbl-", "sec-", "eq-", "lst-")):
            continue
        if keys and token in keys:
            cited.add(token)
        elif not keys:
            cited.add(token)
        else:
            for k in sorted(keys, key=len, reverse=True):
                if token.startswith(k):
                    cited.add(k)
                    break
            else:
                cited.add(token)   # genuinely undefined; reported below
    stats["citations"] = cited
    for key in sorted(cited):
        if keys and key not in keys:
            rep.error(rel, f"citation key '{key}' is not in references.bib")

    # --- data paths ----------------------------------------------------------
    for call in re.findall(r"book_data\(\s*([^)]*)\)", text):
        if "*" in call or "+" in call or "f\"" in call or "f'" in call:
            continue        # computed path: nothing to check statically
        parts = re.findall(r"[\"']([^\"']+)[\"']", call)
        if not parts or len(parts) != len([c for c in call.split(",") if c.strip()]):
            continue
        rel_path = "/".join(parts)
        if data and rel_path not in data:
            rep.error(rel, f"book_data({call.strip()}) names '{rel_path}', "
                           "which is not in data/MANIFEST.tsv")
    # A literal path is only a problem inside code that runs; naming a data file
    # in prose, or typing it at a shell prompt, is exactly right.
    for match in CHUNK.finditer(text):
        lang, body = match.group(1).lower(), match.group(2)
        if lang not in {"python", "r"}:
            continue
        options = dict(re.findall(r"^#\|\s*([\w.-]+):\s*(.+)$", body, re.M))
        if options.get("eval", "true").strip().lower() in {"false", "f", "no"}:
            continue
        for literal in re.findall(r"[\"'](?:\.\./)*data/[\w./-]+[\"']", body):
            rep.warn(rel, f"literal data path {literal} in an executed chunk "
                          "- use book_data() instead")

    # --- prose hygiene -------------------------------------------------------
    for phrase in FORBIDDEN_PHRASES:
        if phrase.isupper() and phrase.isalpha():
            # a bare marker such as TODO or XXX: must stand alone, so that a
            # legitimate accession pattern like phsXXXXXX is not flagged
            hit = re.search(rf"(?<![A-Za-z0-9]){re.escape(phrase)}(?![A-Za-z0-9])", prose)
        else:
            hit = re.search(re.escape(phrase), prose, re.I)
        if hit:
            rep.error(rel, f"forbidden placeholder or phrase: '{phrase}'")
    for american, british in AMERICANISMS.items():
        if british is None:
            continue
        # lower case only: "National Center for Biotechnology Information" and
        # other proper nouns keep their registered spelling
        if re.search(rf"(?<![A-Za-z]){american}(?![A-Za-z])", prose):
            rep.warn(rel, f"American spelling '{american}' (house style: '{british}')")
    if "  " in prose.replace("\n", ""):
        pass
    for emoji in re.findall(r"[\U0001F300-\U0001FAFF\u2700-\u27BF]", prose):
        rep.error(rel, f"emoji in prose: {emoji}")
    if prose.count("!") > 2:
        rep.warn(rel, f"{prose.count('!')} exclamation marks in prose")

    # --- length --------------------------------------------------------------
    if is_chapter and not rel.endswith("16-chapter-summaries-and-review-questions.qmd"):
        if stats["words"] < 3600:
            rep.warn(rel, f"short chapter: {stats['words']:,} words of prose "
                          "(target 4,000-5,500)")
        elif stats["words"] > 7000:
            rep.warn(rel, f"long chapter: {stats['words']:,} words of prose")
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero when any error is found")
    args = ap.parse_args()

    rep = Report()
    keys, data = bib_keys(), manifest_files()
    labels: dict[str, str] = {}
    refs: dict[str, list[str]] = defaultdict(list)
    all_stats, all_cited = [], set()

    files = qmd_files()
    if not files:
        print("no .qmd files found - run this from the book root")
        return 2
    for rel in files:
        text = open(os.path.join(ROOT, rel)).read()
        stats = check_file(rel, text, keys, data, rep, labels, refs)
        all_stats.append(stats)
        all_cited |= stats["citations"]

    for ref, where in sorted(refs.items()):
        if ref not in labels:
            rep.error(where[0], f"cross-reference @{ref} does not resolve to any label")

    unused = sorted(keys - all_cited)
    print("=" * 78)
    print(f"{len(files)} source files | {sum(s['words'] for s in all_stats):,} words of prose | "
          f"{sum(s['figures'] for s in all_stats)} figures | "
          f"{len(all_cited)}/{len(keys)} bibliography entries cited")
    print("=" * 78)
    print(f"{'file':<58}{'words':>8}{'figs':>6}{'cites':>7}")
    for s in all_stats:
        if s["words"] < 120 and not s["figures"]:
            continue
        print(f"{s['file']:<58}{s['words']:>8,}{s['figures']:>6}{len(s['citations']):>7}")

    print(f"\nERRORS ({len(rep.errors)})")
    for line in rep.errors:
        print("  " + line)
    print(f"\nWARNINGS ({len(rep.warnings)})")
    for line in rep.warnings:
        print("  " + line)
    if unused:
        print(f"\nUNCITED bibliography entries ({len(unused)}): {', '.join(unused)}")

    return 1 if (args.strict and rep.errors) else 0


if __name__ == "__main__":
    sys.exit(main())

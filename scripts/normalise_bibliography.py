#!/usr/bin/env python3
"""Replace each DOI-bearing entry in references.bib with the publisher's own
BibTeX record, obtained by DOI content negotiation.

Search APIs return author names as display strings, which split badly into
`family, given` form.  The registration agency serves properly structured
BibTeX for the same DOI, so this pass fixes author names, page ranges and
journal titles while keeping the citation keys the book already uses.
"""
from __future__ import annotations

import re
import sys
import time
import urllib.request

UA = {"User-Agent": "practical-bioinformatics-book/1.0",
      "Accept": "application/x-bibtex; charset=utf-8"}
ENTRY = re.compile(r"@(\w+)\{([^,]+),(.*?)\n\}\n", re.S)


def fetch(doi: str) -> str | None:
    url = "https://doi.org/" + doi
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as fh:
                return fh.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            time.sleep(1.5 * (attempt + 1))
    return None


def rekey(bibtex: str, key: str) -> str:
    body = bibtex.strip()
    body = re.sub(r"^@(\w+)\s*\{[^,]*,", lambda m: f"@{m.group(1).lower()}{{{key},", body, count=1)
    if not body.endswith("}"):
        body += "}"
    return body + "\n"


def strip_empty_name_slots(bibtex: str) -> str:
    """Remove empty entries from `author` and `editor` lists.

    Crossref records for consortium papers frequently carry the group author as an
    empty name, which the registrar renders in BibTeX as a leading or trailing ` and `
    separator with nothing beside it:

        author={ and Aleksander, Suzi A and Balhoff, James and ...}

    A BibTeX processor reads the empty slot as part of the adjacent name, and the
    reference then prints as "Aleksander, Suzi A and, James Balhoff, ... 2023". The
    empty slot carries no information - the consortium's name is not in the record -
    so it is dropped, and the first named author leads the entry. Every one of the
    affected works is referred to by its consortium name in the book's prose, so
    nothing is lost in the text.
    """
    def clean(match: re.Match) -> str:
        field, opening = match.group(1), match.group(2)
        start = match.end()
        depth, i = 1, start
        while depth and i < len(bibtex):
            depth += (bibtex[i] == "{") - (bibtex[i] == "}")
            i += 1
        value = bibtex[start:i - 1]
        names = [n.strip() for n in re.split(r"\s+and\s+", value)]
        names = [n for n in names if n and n != "and"]
        return f"{field}={opening}{' and '.join(names)}" + bibtex[i - 1:i]

    out, pos = [], 0
    for m in re.finditer(r"\b(author|editor)\s*=\s*(\{)", bibtex):
        if m.start() < pos:
            continue
        depth, i = 1, m.end()
        while depth and i < len(bibtex):
            depth += (bibtex[i] == "{") - (bibtex[i] == "}")
            i += 1
        value = bibtex[m.end():i - 1]
        names = [n.strip() for n in re.split(r"\s+and\s+", value)]
        names = [n for n in names if n and n != "and"]
        out.append(bibtex[pos:m.start()])
        out.append(f"{m.group(1)}={{{' and '.join(names)}}}")
        pos = i
    out.append(bibtex[pos:])
    return "".join(out)


def main() -> int:
    text = open("references.bib").read()
    header = text[:text.index("@")]
    replaced, kept, failed = 0, 0, []
    out = []
    for match in ENTRY.finditer(text):
        kind, key, body = match.group(1), match.group(2), match.group(3)
        doi = re.search(r"doi\s*=\s*\{([^}]+)\}", body)
        if not doi:
            out.append(match.group(0))
            kept += 1
            continue
        fresh = fetch(doi.group(1))
        if not fresh or "@" not in fresh:
            out.append(match.group(0))
            failed.append(key)
            continue
        # keep the entry only if the registrar actually returned a title
        if not re.search(r"title\s*=", fresh, re.I):
            out.append(match.group(0))
            failed.append(key)
            continue
        out.append(rekey(fresh, key))
        replaced += 1
        time.sleep(0.4)

    with open("references.bib", "w") as fh:
        fh.write(header + "\n".join(out))
    print(f"normalised {replaced} entries from the registration agency, "
          f"kept {kept} without a DOI, {len(failed)} left as-is")
    if failed:
        print("  not re-fetched: " + ", ".join(failed))
    return 0


if __name__ == "__main__":
    sys.exit(main())

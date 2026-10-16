#!/usr/bin/env python3
"""Check the rendered print PDF for layout faults that a word count cannot see.

`scripts/check_manuscript.py` validates the sources. This script validates the
*result*: it opens the PDF the Typst build produced and looks for the three faults
that survive a clean render and are only visible on the page.

1. **Trim size.** Every page must be exactly 6 x 9 in. A single stray page at A4
   means a page rule leaked past the template partial.
2. **Overlapping text.** Characters whose tight glyph boxes intersect while sitting
   on different lines. This is what an unbreakable block overflowing the bottom of a
   page looks like in the text layer, and it is how the overflowing Solutions
   callouts in the first print build were found. Isolated single-character hits are
   kerning artefacts in ligatures and are reported but not counted as failures.
3. **Text below the bottom margin.** The other signature of an overflowing block: a
   line set past the foot of the type area, heading for the trim edge. Only the
   bottom edge is tested. The running head sits inside the top margin by design and
   section numbers are set into the outside margin, so testing the other three edges
   reports the template's own layout as a fault.

Usage:
    python scripts/check_pdf_layout.py _book/Practical-Approach-to-Learning-Bioinformatics.pdf

Exit status is 1 if any check fails, so it can be used in CI.
"""
from __future__ import annotations

import sys
from collections import defaultdict

import pypdfium2 as pdfium

TRIM_W_IN, TRIM_H_IN = 6.0, 9.0
PT_PER_IN = 72.0
# Bottom margin from _quarto.yml / tex/typst-show.typ, in points, with a little slack
# for descenders and for rules drawn at the foot of a block.
MARGIN_BOTTOM_PT = 0.875 * PT_PER_IN
MARGIN_SLACK_PT = 6.0
# Two characters are on different lines if their vertical centres differ by this much.
LINE_SEPARATION_PT = 3.0
# Ignore intersections smaller than this; sub-point overlaps are rounding.
MIN_OVERLAP_AREA_PT2 = 1.0
# A page with at most this many colliding pairs is a kerning artefact, not a fault.
ARTEFACT_THRESHOLD = 2


def characters(page):
    """Tight glyph boxes for every non-blank character on the page."""
    tp = page.get_textpage()
    out = []
    for i in range(tp.count_chars()):
        ch = tp.get_text_range(i, 1)
        if not ch.strip():
            continue
        left, bottom, right, top = tp.get_charbox(i, loose=False)
        if right <= left or top <= bottom:
            continue
        out.append((left, bottom, right, top, ch))
    return out


def colliding_pairs(chars):
    """Pairs of characters on different lines whose glyph boxes intersect."""
    grid = defaultdict(list)
    for idx, (left, bottom, right, top, _) in enumerate(chars):
        for gx in range(int(left // 20), int(right // 20) + 1):
            for gy in range(int(bottom // 20), int(top // 20) + 1):
                grid[(gx, gy)].append(idx)
    hits = set()
    for bucket in grid.values():
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                a, b = chars[bucket[i]], chars[bucket[j]]
                if abs((a[1] + a[3]) / 2 - (b[1] + b[3]) / 2) < LINE_SEPARATION_PT:
                    continue  # same line
                dx = min(a[2], b[2]) - max(a[0], b[0])
                dy = min(a[3], b[3]) - max(a[1], b[1])
                if dx > 0 and dy > 0 and dx * dy > MIN_OVERLAP_AREA_PT2:
                    hits.add((bucket[i], bucket[j]))
    return hits


def main(path: str) -> int:
    doc = pdfium.PdfDocument(path)
    n = len(doc)
    sizes, wrong_size = set(), []
    overlaps, artefacts, outside = [], [], []

    for index, page in enumerate(doc):
        page_no = index + 1
        width, height = page.get_size()
        size = (round(width / PT_PER_IN, 3), round(height / PT_PER_IN, 3))
        sizes.add(size)
        if size != (TRIM_W_IN, TRIM_H_IN):
            wrong_size.append((page_no, size))

        chars = characters(page)
        hits = colliding_pairs(chars)
        if len(hits) > ARTEFACT_THRESHOLD:
            sample = "".join(sorted({chars[a][4] for a, _ in hits}))[:24]
            overlaps.append((page_no, len(hits), sample))
        elif hits:
            artefacts.append((page_no, len(hits)))

        floor_pt = MARGIN_BOTTOM_PT - MARGIN_SLACK_PT
        escaped = sum(1 for _, bottom, _, _, _ in chars if bottom < floor_pt)
        if escaped:
            outside.append((page_no, escaped))

    print(f"{path}")
    print(f"{n} pages | page sizes found (in): {sorted(sizes)}")
    print()

    failures = 0
    if wrong_size:
        failures += 1
        print(f"FAIL  {len(wrong_size)} page(s) are not {TRIM_W_IN} x {TRIM_H_IN} in")
        for page_no, size in wrong_size[:10]:
            print(f"        p{page_no}: {size}")
    else:
        print(f"PASS  every page is {TRIM_W_IN} x {TRIM_H_IN} in")

    if overlaps:
        failures += 1
        print(f"FAIL  overlapping text on {len(overlaps)} page(s)")
        for page_no, count, sample in overlaps[:15]:
            print(f"        p{page_no}: {count} colliding character pairs  [{sample}]")
    else:
        print("PASS  no overlapping text")

    if outside:
        failures += 1
        print(f"FAIL  text below the bottom margin on {len(outside)} page(s)")
        for page_no, count in outside[:15]:
            print(f"        p{page_no}: {count} characters")
    else:
        print("PASS  no text below the bottom margin")

    if artefacts:
        print()
        print(f"note  {len(artefacts)} page(s) have one or two touching glyph boxes "
              "(ligature kerning, not a layout fault):")
        print("        " + ", ".join(f"p{p}" for p, _ in artefacts[:20]))

    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))

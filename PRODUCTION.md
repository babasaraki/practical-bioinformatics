# Production notes — items requiring the author's confirmation

This file is for the author and the production editor. It is not part of the book and
is excluded from the render. Everything listed here is a point where the manuscript
asserts something that the author, and only the author, can confirm.

## Author biography (`front-matter/about-the-author.qmd`)

The biography was rewritten from two sources: the original `about-the-author.qmd`
draft supplied with the manuscript, and the research-profile description supplied by
the author when this project was set up. The following statements come from the
profile description rather than from the original chapter file, and should be
confirmed before publication:

- that his work includes oncolytic virotherapy, specifically the mechanisms by which
  Newcastle disease virus establishes persistent infection in cancer cells;
- the framing of his bladder cancer work as covering molecular drivers, therapeutic
  resistance and protein interaction networks;
- that his pathogen-genomics work at Africa CDC involved AMR surveillance and
  population genomics pipelines.

Everything else in the biography — the position at Sa'adu Zungur University, the PhD
in genetics and genomics, the Africa CDC and Africa Bio Genome Project roles, the
founding of Open Science Community Nigeria, the AfricArXiv contributions, and the
teaching and curriculum work — is taken directly from the author's own draft.

A book needs the biography at four different lengths, one per slot: the front-matter
page, the back cover, the Amazon field, and the publisher's catalogue line.
`AUTHOR-BIO.md` holds all four, written to the house conventions each slot follows,
together with the sign-off checklist above. The front-matter page in the book is
version 1 of that file; if the author revises the biography, revise it there and
regenerate the other three, so the four do not drift apart.

A photograph is still needed, for the back cover and for Amazon Author Central: 300
dpi or better, at least 1,200 px on the short edge, plain background, with the rights
owned or released.

## Metadata the author must supply before submission

- **ORCID** — deliberately omitted from `_quarto.yml` rather than guessed.
- **Contact e-mail** — omitted for the same reason.
- **Repository and site URLs** — `_quarto.yml` carries
  `github.com/babasaraki/practical-bioinformatics` and the matching GitHub Pages URL,
  taken from the original draft configuration. Confirm or replace them.
- **ISBN, imprint and copyright notice** — placeholders in `tex/before-body.tex`.
- **Dedication**, if wanted — no dedication page currently exists.

## Cover

The print PDF now opens with the cover as page one, fitted to the page width and
centred on white. The artwork is 1951 × 2560 px, a ratio of 1:1.312, against the
1:1.5 of a 6 × 9 page; cropping it to fill would take about 7% off each side and clip
both the title and the author's name, so it is fitted rather than cropped. **A
print-on-demand interior must not contain the cover**: for KDP or for CRC, supply the
PDF with page one removed, and the cover as its own file. Removing it is one command:

```
qpdf Practical-Approach-to-Learning-Bioinformatics.pdf --pages . 2-z -- interior.pdf
```

`images/cover.jpg` is a downscaled copy (1951 × 2560 px, 0.5 MB) of the 22,866 ×
30,000 px file supplied with the manuscript. Its aspect ratio is 1:1.312. Amazon KDP
recommends 1:1.6 for the e-book cover (1600 × 2560), and a print cover must be built
as a full wrap at the trim size with spine width calculated from the final page
count. Neither can be produced from the front-cover image alone, so the original
designer will need to supply them. The original full-resolution file is unmodified.

## Subtitle

The book is titled exactly as the cover has it: *Practical Approach to Learning
Bioinformatics*, with no subtitle. A subtitle is suggested in `KDP-METADATA.md` for
the Amazon listing field only, where it aids discovery without appearing on the
cover.

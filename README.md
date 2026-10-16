# Practical Approach to Learning Bioinformatics

Source for the book *Practical Approach to Learning Bioinformatics* by Umar Ahmad,
written in [Quarto](https://quarto.org) and rendered to HTML, PDF (6 × 9 in) and EPUB.

## Building the book

```bash
conda env create -f environment.yml      # one-off: build toolchain + analysis stack
conda activate pablb
python scripts/fetch_data.py             # download the bundled example data (~12 MB)
python scripts/fetch_data.py --check     # verify checksums against data/MANIFEST.tsv
quarto render                            # HTML, PDF and EPUB into _book/
```

Render a single format with `quarto render --to html`, and a single chapter with
`quarto render part1/01-introduction-to-bioinformatics.qmd`.

## Repository layout

| Path | Contents |
|---|---|
| `index.qmd` | Landing page of the web edition |
| `front-matter/` | Preface, rationale, structure, how to use the book, author, acknowledgements |
| `part1/` … `part8/` | The sixteen chapters, grouped into the book's eight parts |
| `appendices/` | Glossary, software environment, dataset provenance, command reference |
| `data/` | Example data, all downloaded by `scripts/fetch_data.py`; `MANIFEST.tsv` records provenance and checksums |
| `pybfx/` | Small Python helper package used by the Python chapters (`book_data`, `style`) |
| `R/_common.R` | Shared knitr options, ggplot2 theme and `book_data()` for the R chapters |
| `scripts/` | Data provisioning, bibliography resolution, manuscript checks |
| `scss/`, `tex/` | HTML themes and the LaTeX preamble for the print edition |
| `STYLE.md` | House style; binding for every chapter |
| `references.bib` | Bibliography; every entry carries a DOI verified against Crossref or OpenAlex |

## Checks

```bash
python scripts/verify_chapter.py part2/03-bioinformatics-databases.qmd   # run a chapter's code
python scripts/check_manuscript.py                                        # whole-book consistency
python scripts/build_bibliography.py && python scripts/resolve_openalex.py  # rebuild references.bib
```

## Licence

Text and figures: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
Code in this repository: MIT. Bundled data remains under the licence of its
originating archive; see `data/MANIFEST.tsv` for the source of each file.

# Amazon KDP listing metadata

Draft copy for the Kindle Direct Publishing listing fields. Everything here is a
proposal for the author to edit; nothing in it appears in the book itself.

## Title fields

**Title:** Practical Approach to Learning Bioinformatics

**Subtitle (listing field only):** A Hands-On Guide to Sequence Analysis, Genomics and Data Science with Unix, Python and R

The cover carries no subtitle, and the book's own title block matches the cover. KDP
keeps title and subtitle in separate fields and shows both in search results, so a
subtitle here adds discoverability without contradicting the artwork.

**Author:** Umar Ahmad
**Series:** none
**Edition:** 1

## Description (listing copy, ~190 words)

> Bioinformatics is learned by doing it. This book takes you from your first command
> in a terminal to a complete, reproducible analysis written up to the standard a
> journal expects — and every result in it was actually computed, on data you can
> download, with code you can run.
>
> Across sixteen chapters you will work with the archives where biological data
> lives, implement sequence alignment from first principles, master the Unix, Python
> and R skills that make large files tractable, annotate a genome, analyse sequencing
> reads from FASTQ through to differential expression, compute real quantities from
> protein structures, interrogate biological networks, and apply statistics and
> machine learning to omics data without falling into the traps that high-dimensional
> biology sets. Later chapters cover cancer genomics, rare disease diagnostics,
> pharmacogenomics and pathogen surveillance, and the ethical obligations that come
> with human genomic data.
>
> Written for life scientists, clinicians and students with no programming background,
> it assumes only that you have a computer and the patience to type into it. Every
> chapter ends with graded exercises and full worked solutions.

## Categories

Choose three:

1. Science & Math > Biological Sciences > Biology > Molecular Biology
2. Computers & Technology > Computer Science > Bioinformatics
3. Science & Math > Biological Sciences > Genetics

## Keywords (seven slots)

1. bioinformatics textbook
2. genomics data analysis
3. python for biologists
4. R bioconductor rnaseq
5. sequence alignment tutorial
6. next generation sequencing analysis
7. computational biology course

## Print specification

| Field | Value |
|---|---|
| Format | Paperback |
| Trim size | 6 × 9 in (15.24 × 22.86 cm) |
| Interior | Black & white on cream, or premium colour if the figures are to stay in colour |
| Bleed | No bleed (figures do not run to the page edge) |
| Paper | White for a colour interior, cream for black & white |
| Page count | Set after the final render; the typeset interior is produced by `quarto render --to typst` |
| Gutter margin | Built into the layout: inside margin 0.875 in, outside 0.625 in |

::: Note on colour
Several figures use colour to distinguish categories. The book's palette is
colour-blind safe and every figure is also distinguishable by position or shape, but a
black-and-white interior will still lose information in the heatmaps. Either choose a
colour interior, or regenerate those figures with a greyscale-safe scale before
submitting the print edition.
:::

## Cover files still needed

The supplied artwork is a front cover at a 1:1.312 aspect ratio. KDP needs:

- **E-book cover:** 1600 × 2560 px (1:1.6). The current image must be re-laid-out, not
  simply stretched.
- **Print cover:** a single full-wrap PDF — back cover, spine and front — at the 6 × 9
  trim with 0.125 in bleed on all outer edges. Spine width depends on the final page
  count and paper stock; KDP's cover calculator gives the exact dimensions once the
  interior is final.

## Pricing and rights

Decide before upload: territories (worldwide unless rights are reserved), KDP Select
enrolment (which requires digital exclusivity and is incompatible with keeping the
book freely readable online), and list price. Note that the online edition is
CC BY-NC-SA 4.0; that licence permits the author to sell print copies, but KDP Select
exclusivity would not sit comfortably alongside a freely available web edition.

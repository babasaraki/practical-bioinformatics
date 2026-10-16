# House style — *Practical Approach to Learning Bioinformatics*

This document is binding for every chapter. It exists so that sixteen chapters
read as one book. Where this document and personal preference disagree, this
document wins.

---

## 1. The promise the title makes

The book is called *Practical Approach to Learning Bioinformatics*. Every
chapter must therefore satisfy three tests:

1. **The reader does something.** Theory appears because it is needed to make a
   decision in an analysis, not as a preamble to be endured. A section that
   cannot be connected to a command, a script or an interpretation decision does
   not belong.
2. **The results are real.** Every number, alignment, tree, plot and table shown
   in the book is produced by code that ran against the bundled data. No invented
   output, ever. If a tool cannot run at render time, show the command and quote
   output that was actually captured from a real run, and say so.
3. **The reader can repeat it.** All data lives in `data/`, all code is in the
   chapter, all software is pinned in `environment.yml`.

---

## 2. Chapter anatomy

Every chapter has exactly these elements, in this order. Do not add top-level
sections beyond them; do not omit any.

```
---
title: "Sentence-case chapter title"
---

::: {.objectives}
**After working through this chapter you will be able to**

- verb-first learning outcome
- ... (five to seven outcomes)
:::

Opening narrative: two to four paragraphs. Pose the concrete problem the
chapter solves, state why it matters, and say what the reader will have built
or measured by the end. No bulleted "overview" lists here.

## Section one {#sec-shortname}
...

## Summary {#sec-NN-summary}

## Exercises {#sec-NN-exercises}

## Solutions {#sec-NN-solutions}

## Further reading {#sec-NN-further-reading}
```

**Word budget: 4,000–5,500 words of body text** (excluding code listings and
solutions). Five to nine `##` sections before the Summary is the normal range.

### Required element details

| Element | Rule |
|---|---|
| `.objectives` block | 5–7 outcomes, each starting with a verb (*explain, compute, interpret, diagnose, build*). Never "understand" or "learn about" — those cannot be assessed. |
| Opening narrative | Prose only. Must name the dataset(s) the chapter will use. |
| Summary | 150–300 words of prose, or 6–10 bullets that each state a transferable conclusion — not a list of topics covered. |
| Exercises | 6–10, numbered, graded easy → hard. At least two must require writing code against bundled data; at least one must require interpreting a result rather than producing it. |
| Solutions | Complete worked solutions for **all** exercises, inside a collapsed callout (see §6). Code in solutions must run. |
| Further reading | 4–8 annotated entries, one sentence each explaining *why* the reader would go there. Cite with `@key`; see §7. |

---

## 3. Headings

- **Sentence case**: "Working with alignment files", not "Working With Alignment Files".
- **No manual numbers.** Quarto numbers sections. Never write `## 5.2 Basic commands`; write `## Basic commands`.
- **No "Chapter N:" in the title.** The title field is the chapter name alone.
- Every `##` carries an id: `{#sec-descriptive-slug}`, lowercase, hyphenated, unique book-wide. Prefix chapter number when a slug would otherwise collide, e.g. `{#sec-09-qc}`.
- Maximum depth is `###`. If you need `####`, restructure.
- Headings are noun or gerund phrases, never questions, never sentences.

---

## 4. Code

### Engine separation — hard rule

**A chapter file must not contain both executable `{r}` and executable `{python}`
chunks.** Quarto selects one engine per file; mixing them forces `reticulate`
and breaks the build. Chapter language assignments:

| Chapters | Engine |
|---|---|
| 1, 2, 3, 4, 6, 9 (read/variant parts), 10, 15 | `{python}` |
| 7, 9 (expression parts), 11, 12 | `{r}` |
| 5 | `{bash}` (non-executed, see below) |
| 8, 13, 14, 16 | as stated in the chapter brief |

Non-executable illustrative code in any language is always allowed and does not
affect engine choice.

### Chunk options

```` 
```{python}
#| label: fig-gc-content
#| fig-cap: "GC content across the SARS-CoV-2 genome in 500 bp windows."
#| warning: false
```
````

- Every chunk that produces a figure **must** have a `label:` starting `fig-` and a `fig-cap:`. Reference it in the text as `@fig-gc-content`.
- Every chunk producing a displayed table must have `label: tbl-...` and `tbl-cap:`, referenced as `@tbl-...`.
- Chunks are short: aim for under 25 lines. Split long pipelines across chunks with prose between them.
- `#| eval: false` is reserved for code that genuinely cannot run at build time —
  external binaries (BWA, GATK, Prokka), cluster submissions, multi-gigabyte
  downloads, interactive tools. When you use it, you **must** immediately follow
  with the real captured output in a plain fenced block introduced by a sentence
  stating where the output came from.
- Never use `#| echo: false` to hide code that produces a result the reader is
  meant to understand. It is acceptable only for setup chunks that repeat
  boilerplate already shown once.

### Setup chunk

First code chunk of every chapter, shown once:

Python chapters:
```{.python}
#| label: setup
import sys; sys.path.insert(0, "..")
from pybfx import book_data, style
style()
```

R chapters:
```{.r}
#| label: setup
source(file.path("..", "R", "_common.R"))
```

### Data access

Never hard-code paths. Use `book_data("proteins", "globins.fasta")` in Python and
`book_data("proteins", "globins.fasta")` in R. Every data file you use must
already exist in `data/MANIFEST.tsv`; if you need something that is not there,
say so in your report rather than inventing a file or downloading at render time.

**No network access inside executable chunks.** Live API calls belong in
`eval: false` chunks with captured output, because the book must render offline
and must not hammer public services on every build.

### Code quality

Code in a teaching book is read far more often than it is run. Therefore:

- Meaningful names. `sequence_record`, not `sr`; `gc_fraction`, not `x`.
- A comment above any line whose purpose is not obvious from the names; no
  comments restating the syntax (`# loop over the list` above a `for` loop is noise).
- Show idiomatic, current practice: `Bio.Align.PairwiseAligner`, not the
  deprecated `Bio.pairwise2`; `dplyr` pipelines with the native `|>` pipe.
- Handle the error case when a reader will plausibly hit it (missing file,
  empty result, unexpected sequence alphabet).

---

## 5. Figures and tables

- Figures are generated by code in the book. Do not reference image files that
  do not exist. Schematic diagrams that cannot be computed may be drawn with
  Matplotlib/ggplot2 in a labelled chunk, or omitted.
- 2–4 figures per chapter is the target. Every figure must be referred to in the
  text by `@fig-...` before it appears, and must be interpreted in prose after it:
  say what the reader should see and what it means.
- Captions are full sentences with a terminal full stop, and are
  self-contained — a reader who looks only at the figure can understand it.
- Tables: use Markdown tables for small reference material; generate data tables
  from code. Keep to 6 columns or fewer so they survive the 6 × 9 in print page.
- Colour: use the book palette (`book_palette` in R, `PALETTE` in `pybfx`). Never
  rely on colour alone to distinguish categories.

---

## 6. Callouts

Five types only, used for these purposes and no others:

| Callout | Purpose |
|---|---|
| `::: {.callout-note}` | A definition, a format detail, or a pointer to another chapter. |
| `::: {.callout-tip}` | A practical shortcut, a diagnostic command, a habit worth forming. |
| `::: {.callout-warning}` | A step where readers commonly lose data, waste days, or silently get wrong answers. |
| `::: {.callout-important}` | Ethical, legal, clinical or biosafety obligations. Rare — reserve its force. |
| `::: {.callout-caution collapse="true"}` | The Solutions section only. |

Every callout carries a title: `::: {.callout-warning title="Coordinates are not interchangeable"}`.
Two to five callouts per chapter. A page with three callouts in a row has no
prose rhythm — space them out.

---

## 7. Citations

- Cite **only** keys that exist in `references.bib`. The authoritative list is
  `scripts/bibliography_report.tsv`. **Never invent a citation key, a DOI, an
  author or a year.** If you need to cite something that is not in the file,
  write the claim without a citation and list the gap in your report.
- Inline: "the Smith–Waterman algorithm [@smith1981]"; narrative: "@love2014
  showed that …".
- Cite the primary methods paper when naming a tool the first time in a chapter.
- 10–25 citations per chapter. Do not pad; do not cite a tool twice in one chapter.

---

## 8. Voice and mechanics

- **British English** (`en-GB`): *analyse, normalise, colour, behaviour,
  centre, licence* (noun) / *license* (verb). Keep US spelling inside code,
  option names and quoted output (`--color`, `normalize_counts`).
- Address the reader as **you**. Use **we** only for shared reasoning
  ("we now have two candidate explanations"). Avoid "the user", "one".
- Present tense for what code and biology do; past tense only for history.
- Define every term at first use, in prose, and add it to the glossary.
- Spell out an acronym at first use in each chapter: "multiple sequence
  alignment (MSA)".
- No marketing language ("powerful", "cutting-edge", "revolutionary", "game-changing"),
  no exclamation marks, no emoji, no rhetorical questions as headings, no
  "As we all know".
- Numbers: spell out one to nine in prose; use digits with units
  (`150 bp`, `2.5 GB`, `30,427 reads`). Use a thin space or comma in thousands
  consistently (`29,903 bp`).
- Units and formats: `bp`, `kb`, `Mb`, `Gb` for sequence length; FASTA, FASTQ,
  SAM, BAM, CRAM, VCF, GFF3, GTF always capitalised.
- Gene symbols italic and upper case for human (*TP53*), lower case initial for
  mouse (*Trp53*); protein symbols roman (p53).
- Em dashes — like this — without surrounding spaces in print is CRC style, but
  this book uses spaced en dashes for readability in HTML. Use ` — `.

---

## 9. Cross-referencing other chapters

Refer to chapters by their label, never by number in prose that could drift:
write `[Chapter -@sec-chap-unix]` style only if the chapter has a top-level id.
In practice, add an id to each chapter's title block:

```
---
title: "Unix and the command line"
---
```
and refer to it as "the Unix chapter" in prose, or use `@sec-...` to point at a
specific section. Never write "see Chapter 7, Section 3.2".

---

## 10. What must never appear

- Placeholder text: *TODO*, *TBD*, *lorem ipsum*, `example.com`, `your_file.txt`,
  `path/to/data`.
- Code that was never run, presented as though it produced the output shown.
- A citation key not present in `references.bib`.
- A file path not present in `data/MANIFEST.tsv`.
- Invented accession numbers, DOIs, statistics, or quoted tool output.
- Sections titled "Projects" or "FAQs" — these were in the first draft and are
  replaced by Exercises and by prose that answers the questions in place.
- The phrases "In this chapter, we will explore", "Let's dive in",
  "the fascinating world of".

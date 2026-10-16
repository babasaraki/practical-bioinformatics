# Publishing the online edition

The book already renders as a Quarto website — sidebar navigation, full-text search,
light and dark themes, every figure and code listing inline. What follows puts it at
`https://babasaraki.github.io/practical-bioinformatics/`, which is the address
`site-url` in `_quarto.yml` already declares.

## 1. Put the repository on GitHub

From the repository root:

```bash
git init
git add .
git commit -m "Practical Approach to Learning Bioinformatics: first public version"
git branch -M main
git remote add origin https://github.com/babasaraki/practical-bioinformatics.git
git push -u origin main
```

`_freeze/` is committed on purpose — see below. It is about 34 MB, which is unremarkable
for GitHub; no single file in it approaches the 100 MB limit.

## 2. Turn on Pages

In the repository: **Settings → Pages → Build and deployment → Source: Deploy from a
branch**, branch `gh-pages`, folder `/ (root)`. The branch does not exist yet; the first
successful workflow run creates it. Come back and set this after that run.

Then **Settings → Actions → General → Workflow permissions: Read and write**, which the
publish step needs in order to push to `gh-pages`. The workflow also asks for it through
`permissions: contents: write`, but the repository setting overrides it.

## 3. What the workflow does

`.github/workflows/render.yml` has two jobs, deliberately separated.

**`site`** runs on every push to `main`. It installs Quarto and nothing else, renders
the HTML, and publishes to `gh-pages`. It takes about a minute.

It can do that because **`_freeze/` is committed**. Quarto's freeze cache holds the
computed output of every chunk, so rendering the site executes no code. Three
consequences, all of them wanted:

- CI needs no conda, no R, no Bioconductor, no BLAST, MAFFT, samtools or bwa;
- CI makes no calls to NCBI, UniProt or Ensembl on every push, so the build cannot be
  broken by a service being slow or a rate limit;
- the published site shows **exactly** the results you verified, not whatever a public
  archive happens to return today.

The cost is that the cache must be kept in step with the prose. When you change a chunk,
re-render that chapter locally and commit `_freeze/` along with the `.qmd`. The workflow
fails loudly if `_freeze` is missing rather than quietly publishing a site with no
output in it.

**`reproduce`** runs only when you trigger it by hand, from the Actions tab. It builds
the whole conda environment, re-fetches every dataset and verifies its checksum,
executes every chunk from scratch with `--cache-refresh`, renders all three formats, and
checks the print PDF's geometry. This is the job that proves the book is reproducible.
Run it before each release, and when you have changed the environment.

## 4. Updating the book

```bash
quarto render --to html          # rebuild locally and look at it
git add -A && git commit -m "..." && git push
```

Pages updates within a minute or two of the workflow finishing.

## Alternatives, and why this one

| Route | Why not here |
|---|---|
| `quarto publish gh-pages` from your laptop | Works, and is the quickest way to see the site live. But it publishes whatever is on your machine, with no record of what produced it. Use it for a first look, then let CI own the deployment. |
| `quarto publish quarto-pub` | Free and instant, but the address is `<user>.quarto.pub/<slug>`, and you do not control it. Fine for a preview you send to a reviewer. |
| Netlify or Cloudflare Pages | Better caching and preview deployments per pull request. Worth it if the book gets heavy traffic; unnecessary at the start. |
| Executing chunks in CI instead of committing `_freeze` | A forty-minute job that depends on six command-line tools and four public web services behaving. It will break, and it will break on a push that changed a comma in the preface. |

## 5. A note on the first push

`scripts/fetch_data.py` downloads the ~12 MB of example data; the data files themselves
are not in the repository, only `data/MANIFEST.tsv` with each file's source archive,
accession and SHA-256. A reader clones the repository and runs the script. Keep it that
way: committing the data would add nothing a checksum does not already guarantee, and
some of those archives have terms about redistribution.

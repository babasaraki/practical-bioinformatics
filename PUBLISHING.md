# Publishing the online edition

## The order these steps are taken in

The route chosen for this book is **publisher first, storefronts in reserve**:

1. the free HTML edition goes online now — it needs no ISBN and no foreword;
2. the request for a foreword goes to the prospective writer of it;
3. the proposal goes to CRC, disclosing the free online edition, which is an asset
   rather than an obstacle: Chapman & Hall/CRC publishes several books that are
   freely readable online;
4. **nothing is offered for sale until CRC answers.** A paid edition on Amazon or
   Leanpub is commercial publication, and a book already in the market with an ISBN
   naming another publisher is normally declined on acquisition grounds whatever its
   quality. A free website is not;
5. if CRC accepts, it assigns the ISBNs and handles production and distribution. If
   it declines, the ISBNs are registered with the National Library of Nigeria
   (RIGHTS-AND-ISBN.md) and the Leanpub and KDP packages in `dist/` are used as they
   stand.

Two consequences for the site as it is configured: the sidebar carries no storefront
link, and the reserved foreword page is absent from the default build. "Where to sell
it" below covers the storefront when the time comes; `scripts/make_foreword_pdf.sh`
restores the foreword page for the copy sent to its prospective author.

## Where to host it

Quarto builds the site in every case; the only question is who serves the files.
`quarto publish` is a Quarto command with several destinations, so "publishing with
Quarto" and "hosting on GitHub Pages" are not alternatives - `quarto publish gh-pages`
is both at once.

| Destination | Command | Notes |
|---|---|---|
| GitHub Pages | `quarto publish gh-pages` (or the committed workflow) | Free. Readable URL. Custom domain free. Source and site in one place. |
| Posit Connect Cloud | deploy from the GitHub repository, or `quarto publish` | Free plan allows unlimited documents. Default URLs are opaque share links rather than a readable address. |
| Netlify | `quarto publish netlify` | Free tier, custom domain, good for a site larger than 100 MB. |
| Quarto Pub | `quarto publish quarto-pub` | **Closed to new accounts.** Posit has folded quartopub.com into Connect Cloud; existing sites keep working and are being migrated. Not a route this book can take. |

The rendered site is 54 MB, of which 21 MB is the PDF and EPUB offered as downloads,
so it fits any of these comfortably.

GitHub Pages is the recommendation for this book, for one reason beyond cost: the
address goes into the CRC proposal and may end up on the back cover, so it should be
readable and should stay under the author's control. `babasaraki.github.io/practical-bioinformatics/`
satisfies both and can be pointed at a custom domain later without changing hosts.
Connect Cloud is a reasonable second choice, but it deploys from a GitHub repository
anyway - so the repository goes up either way, and only the final hop differs.

Whichever is chosen, `site-url` in `_quarto.yml` must match the address actually
served; Quarto uses it for the sitemap, the social-card metadata and the canonical
links.

### What the site offers, and what it does not

The site publishes the HTML edition and nothing else: no PDF, no EPUB. That is the
arrangement every Chapman & Hall/CRC book with a free online edition uses, and it is
what the site this book is modelled on does. The reasoning is contractual rather than
aesthetic. A publisher acquires publication rights; a free online HTML edition is a
negotiated exception to that grant, and it survives negotiation because nobody reads a
600-page textbook cover to cover in a browser. A print-ready PDF does not survive it,
because it substitutes directly for the printed book - and the EPUB is the ebook
edition itself, the file that goes to Kindle and VitalSource.

Nothing is withheld from a reader: the HTML carries every chapter, every figure, every
exercise and every solution. What is withheld is the two formats a publisher sells.

This is enforced by absence rather than by hiding links. `_quarto.yml` has no
`downloads:` key, so no download control appears; and the `site` job renders only
`--to html`, so neither file is ever copied into the published directory. Hiding the
link alone would not be enough - the URL is guessable.

Both formats are still built locally by a plain `quarto render`, and both ship in the
distribution packages under `dist/`. Only the public website is affected.

## The site itself

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

---

# Selling the PDF while the site stays free

This is the arrangement most self-published technical authors use, and the one
*Computational Genomics with R* uses: the HTML edition is free and complete, and a
typeset PDF and EPUB are for sale. It works because the two serve different needs. The
site is what a search engine finds and what somebody reads at a terminal with the code
beside them; the PDF is what they buy to read away from a screen, to print, to cite by
page number, or simply to support the work.

Nothing is withheld from the free edition. Crippling the online version — missing
chapters, no exercises — reads as a sales funnel and costs more goodwill than it earns.

## Where to sell it

| | Royalty | Why you might choose it |
|---|---|---|
| **Leanpub** | **80%** on sales of $7.99 and up; 80% minus 50 cents below that | Built for this. Variable pricing lets the reader choose what to pay above your minimum, and the purchase page shows them what you earn, which converts well for a book with a mission. Free updates push to everyone who has bought. This is the one to start with. |
| **Gumroad** | ~90% minus payment processing | More control over the page and the customer list; no bookstore traffic of its own. Good as a second outlet. |
| **Payhip** | 95% on the free tier | Cheapest per sale, handles EU VAT. Least discovery. |
| **Amazon KDP** | 70% at $2.99–$9.99, 35% outside it, minus delivery | For the Kindle and paperback editions, not for a PDF — KDP does not sell PDFs. |

Leanpub and KDP are complements, not alternatives: Leanpub for the PDF and EPUB with
variable pricing, KDP for the paperback and the Kindle edition. The `dist/leanpub` and
`dist/amazon-kdp` packages are built for exactly that split.

## Pricing

Leanpub's variable pricing takes a **minimum** price and a **suggested** price. For a
591-page technical book, a $19 minimum with a $29 suggestion is a defensible pair;
readers who want to pay more routinely do. Set a free or near-free coupon tier for
students in low-income countries — Leanpub supports coupons, and for a book written to
widen access that is worth more than the lost revenue.

## Wiring it up

`_quarto.yml` carries a sidebar cart link and `index.qmd` an HTML-only panel with two
buttons. Both point at placeholders:

```
https://leanpub.com/practical-bioinformatics
https://www.amazon.com/dp/XXXXXXXXXX
```

Replace them once the listings exist.

The panel is wrapped in `.content-visible when-format="html" unless-format="epub"`.
**Both attributes are needed.** Quarto's `html` format selector matches the EPUB build
as well, so `when-format="html"` on its own puts a "Buy the PDF" button inside the EPUB
you are selling — which is exactly what the first version of this did. After any change
to that panel, confirm both saleable formats are clean:

    python3 - <<'EOF'
    import zipfile, pypdfium2 as pdfium
    d = pdfium.PdfDocument("_book/Practical-Approach-to-Learning-Bioinformatics.pdf")
    print("pdf:", [i + 1 for i in range(len(d))
                   if "Buy the PDF" in d[i].get_textpage().get_text_range()] or "clean")
    z = zipfile.ZipFile("_book/Practical-Approach-to-Learning-Bioinformatics.epub")
    print("epub:", [n for n in z.namelist()
                    if n.endswith(".xhtml") and b"Buy the PDF" in z.read(n)] or "clean")
    EOF

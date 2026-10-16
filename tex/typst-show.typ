// Template partial for the Typst print edition.
//
// Quarto's Typst book output is built on the `orange-book` package, whose default
// page is A4. Its `book()` function accepts explicit `width`, `height` and `margin`
// arguments, and this partial is what passes them, setting the 6 x 9 in trim that
// Chapman & Hall/CRC and Amazon KDP expect. Margins are asymmetric for binding:
// wider on the inside edge for the gutter.
//
// It is adapted from Quarto's own orange-book partial rather than copied from it.
// Three things differ, deliberately: `main-color` is fixed to the book's palette
// instead of being looked up from Quarto's brand metadata, which this project does
// not set; `logo` is none, since the cover is supplied separately for print and for
// KDP; and the `marginalia` setup block is dropped, because this book does not use
// margin notes and that block would override the page margins set here.
//
// Referenced from _quarto.yml as `template-partials: [tex/typst-show.typ]`.
#import "@preview/orange-book:0.7.1": book, part, chapter, appendices

// Cover plate. Emitted before the template takes over, so it becomes page one of
// the PDF edition; the template's own title page follows it. The artwork is 1951 x
// 2560 px (ratio 1:1.312), narrower than the 1:1.5 of a 6 x 9 page, so it is fitted
// to the page width and centred rather than cropped to fill - cropping to 1:1.5
// would take about 7% off each side and clip the title and the author's name.
// Print-on-demand suppliers want the cover as a separate file, so a KDP or CRC
// interior is this PDF with page one removed; PRODUCTION.md records that.
#page(width: 6in, height: 9in, margin: 0pt, fill: white, numbering: none)[
  #align(center + horizon, image("images/cover.jpg", width: 100%, fit: "contain"))
]

// The book template puts the folio in the running head, while Quarto's own page rule
// adds a second one in the footer. Drop the footer so each page carries one folio.
// This has to precede the template: the template generates its own front matter - the
// title page and the contents - inside `book()`, before the body, so a rule placed
// after the `show` line never reaches those pages. It did not, and they kept Quarto's
// footer; on the title verso that folio was set 6.6 pt below the trim edge.
#set page(footer: none)

#show: book.with(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(by-author)$
  author: "$for(by-author)$$it.name.literal$$sep$, $endfor$",
$endif$
$if(date)$
  date: "$date$",
$endif$
$if(lang)$
  lang: "$lang$",
$endif$
  width: 6in,
  height: 9in,
  margin: (inside: 0.875in, outside: 0.625in, top: 0.75in, bottom: 0.875in),
  font-size: 10pt,
  main-color: rgb("#1A5276"),
  logo: none,
  first-line-indent: false,
  // The part page places the roman numeral at the top left and the part title in a
  // box occupying the right 60% of the text block. The template's default numeral
  // size is 16em, which at 10pt is 160pt tall and, for a three-glyph numeral such as
  // VII, wider than the 40% left to it on a 6 x 9 page - the numeral then runs under
  // the title. 5em fits the widest numeral this book uses.
  part-font-size: 5em,
  // The part page also carries a contents list for the part, anchored to the bottom.
  // At the default depth of 2 it lists every section of every chapter in the part,
  // which for a 14-section chapter overflows upward into the title. Depth 1 lists
  // chapters only, which is what a part page in a Chapman & Hall book shows.
  outline-small-depth: 1,
  outline-small-width: 10cm,
$if(toc-depth)$
  outline-depth: $toc-depth$,
$endif$
$if(lof)$
  list-of-figure-title: "$if(crossref.lof-title)$$crossref.lof-title$$else$$crossref-lof-title$$endif$",
$endif$
$if(lot)$
  list-of-table-title: "$if(crossref.lot-title)$$crossref.lot-title$$else$$crossref-lot-title$$endif$",
$endif$
)

// Callouts must break across pages. Quarto defines its `callout` function with
// `breakable: false`, which is fine for the short notes the setting was designed for
// but not for this book: the Solutions callout at the end of a chapter regularly runs
// longer than one page. An unbreakable block that does not fit is not reflowed - it
// overflows the bottom of the page, and the following text is then set on top of it.
// That is the overlap visible in Chapter 5's solutions and on twenty other pages.
// This definition is Quarto's, with the three blocks made breakable; it is emitted
// after Quarto's and so is the one the body calls.
#let callout(body: [], title: "Callout", background_color: rgb("#dddddd"), icon: none, icon_color: black, body_background_color: white) = {
  block(
    breakable: true,
    fill: background_color,
    stroke: (paint: icon_color, thickness: 0.5pt, cap: "round"),
    width: 100%,
    radius: 2pt,
    block(
      breakable: true,
      inset: 1pt,
      width: 100%,
      below: 0pt,
      block(
        fill: background_color,
        width: 100%,
        inset: 8pt)[#if icon != none [#text(icon_color, weight: 900)[#icon] ]#title]) +
      if(body != []){
        block(
          breakable: true,
          inset: 1pt,
          width: 100%,
          block(breakable: true, fill: body_background_color, width: 100%, inset: 8pt, body))
      }
    )
}

// Paragraph separation. The book template sets `par(spacing: 0.5em)`, which is the
// same as its leading, so with first-line indentation turned off consecutive
// paragraphs run together into an unbroken block of text. Raising the spacing
// restores the break between paragraphs that the HTML and EPUB editions have. Set
// here rather than in tex/typst-header.typ because the template's own rule is
// applied to the body and would otherwise win.
#set par(spacing: 1em)

// Glossary and other definition lists. Quarto emits a `terms.item` rule that pulls
// the definition up by a negative top inset (`inset: (top: -0.4em)`), which assumes
// the paragraph spacing of its own default template. Against this template's tighter
// spacing the negative inset lifts the definition's first line onto the term's line
// and the two overlap. This rule is identical except that the definition is not
// pulled up, and it adds space around each entry so a long A-Z list stays readable.
// Quarto emits its rule before the template partial, so this later rule wins.
#show terms.item: it => block(breakable: false, above: 0.9em, below: 0.9em)[
  #text(weight: "bold")[#it.term]
  #block(inset: (left: 1.5em))[#it.description]
]

// Inline code sits slightly smaller than the surrounding text; block listings are
// styled in tex/typst-header.typ.
#show raw.where(block: false): set text(size: 9pt)

// Code listings must not be justified. The book template justifies paragraphs, and
// that stretches the spaces inside a wrapped listing until its indentation no longer
// lines up. This rule has to live here rather than in tex/typst-header.typ, because
// Quarto emits its own raw-block rule after the header, and in Typst the later show
// rule wins. Re-emitting `it` with `set par` in scope leaves Quarto's own code
// styling intact and changes only the justification.
#show raw.where(block: true): it => {
  set par(justify: false, leading: 0.55em)
  it
}

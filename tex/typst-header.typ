// Page geometry for the print edition: 6 x 9 in trim with asymmetric margins
// for a bound book (wider on the inside edge to allow for the gutter).
// Page size and margins come from _quarto.yml (papersize: us-trade), because
// Typst's own page rule is emitted after this header and would override one set here.
// `hyphenate: auto` - Typst's default - hyphenates justified text only. Body
// paragraphs are justified and still hyphenate; display text that is set ragged,
// such as a part title or a contents entry, does not. Forcing `true` here instead
// broke part titles across lines ("Systems biol-ogy and data science").
#set text(size: 10pt, lang: "en", region: "gb", hyphenate: auto)
// Paragraph justification and leading are set by the book template itself;
// setting them here as well leaks into the title block and spaces it badly.
#show heading.where(level: 1): it => block(above: 2em, below: 1.2em)[
  #set text(size: 18pt, weight: "bold", fill: rgb("#1A5276"))
  #it
]
#show heading.where(level: 2): set text(size: 13pt, weight: "bold", fill: rgb("#1A5276"))
// Code listings are styled in tex/typst-show.typ, which Quarto emits after its
// own raw-block rule; a rule placed here would be overridden by it.
#show raw: set text(size: 8.5pt)
#show figure.caption: set text(size: 8.5pt)
#show link: set text(fill: rgb("#1A5276"))

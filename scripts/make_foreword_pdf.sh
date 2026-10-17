#!/usr/bin/env bash
# Build the copy sent to the prospective author of the foreword.
#
#   scripts/make_foreword_pdf.sh            # from the book directory
#
# The default build omits front-matter/foreword.qmd, because an empty page reserved
# for somebody else's text should not appear on the public website. This script adds
# that one page back for a single print render and then restores the configuration.
#
# A Quarto profile cannot do this: profiles CONCATENATE list values rather than
# replacing them, so a profile that redeclares book.chapters appends a second copy of
# the whole front matter to the end of the book. Editing the chapter list in place and
# putting it back is the reliable way.
#
# Output: _book-foreword/Practical-Approach-to-Learning-Bioinformatics.pdf
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'mv -f _quarto.yml.bak _quarto.yml' EXIT
cp _quarto.yml _quarto.yml.bak
python - <<'PY'
p='_quarto.yml'; s=open(p).read()
anchor='        - front-matter/preface.qmd'
assert s.count(anchor)==1 and 'front-matter/foreword.qmd' not in s.split('chapters:')[1]
open(p,'w').write(s.replace(anchor,'        - front-matter/foreword.qmd\n'+anchor,1))
PY
quarto render --to typst --output-dir _book-foreword

# ISBNs, rights, and the order to do things in

Three separate questions get tangled together here. Untangling them changes what you
should do next, and in what order.

## 1. Does the online edition need an ISBN?

**No.** An ISBN identifies a discrete monographic product — a specific format of a
specific edition, fixed at a point in time. A continuously updated website is not one,
and no agency assigns ISBNs to them. *Computational Genomics with R* has no ISBN on its
website and ISBNs on its printed editions, which is the normal arrangement.

So the free HTML edition can go online today, with no number and no registration.

**Each saleable format does need its own**, and they are not interchangeable:

| Format | ISBN |
|---|---|
| Paperback | one |
| Hardcover, if ever | a different one |
| EPUB | a different one |
| PDF sold as a product | a different one |
| Free HTML site | none |

## 2. Who provides them — CRC, or the National Library of Nigeria?

**It depends entirely on who publishes, which is not yet decided.** That is why this
question cannot be answered before the CRC question is.

**If Chapman & Hall/CRC publish it**, CRC assigns every ISBN from their own publisher
prefix and you register nothing, buy nothing and apply for nothing. The National Library
of Nigeria's own guidance states the rule for shared cases: in a joint publication the
ISBN is assigned by the publisher in charge of distribution. For a CRC edition that is
CRC.

**If you self-publish**, you need your own, and as an author based in Nigeria they come
from the **National Library of Nigeria**, which is the country's sole ISBN agency —
Nigeria's national identifier is 978-978 and the NLN notes that any other ISBN issuance
centre in the country is fake. Two things to know before you start:

- **A Publisher's Registration Number comes first.** The NLN requires a PRN of any
  publisher or self-publisher before it will issue ISBNs at all.
- **Legal deposit follows publication.** The NLN requires three copies of the book,
  delivered at the publisher's expense within one month of publication. An ISBN also
  makes the book eligible for the NLN's Cataloguing-in-Publication programme, which is
  worth having: it is the CIP block printed on a copyright page.

Indicative cost and time, from a 2026 account and worth confirming with your nearest NLN
office before relying on it: about ₦5,000 for a single ISBN, two to four weeks to
process, applied for in person. The NLN has offices in Abuja, Lagos, Ibadan, Enugu,
Kaduna, Kano, Jos and Port Harcourt.

One rule that catches diaspora authors: ISBN agency is determined by where the
*publisher* is based, not by nationality. Publishing from Nigeria means the NLN; if you
were publishing from the UK it would be Nielsen.

**Do not take Amazon's free ISBN.** KDP will give you one for the paperback, but it
names Amazon as the publisher of record and ties the edition to Amazon. For a book you
may take to CRC, or want in bookshops and libraries, that is the wrong trade.

Leanpub does not require an ISBN at all.

## 3. The order to do things in

Your instinct is right, and the reason is stronger than convenience: **publishing for
sale before an academic publisher has answered can cost you the contract.** Publishers
acquire first publication rights. A free website is negotiable — CRC has published books
whose full text is free online — but a self-published paperback already for sale on
Amazon is a different matter, and an acquisitions editor may ask you to withdraw it or
simply decline. If you buy ISBNs, publish, and CRC then takes the book, the CRC edition
gets new ISBNs, yours are retired, and the catalogue record is a mess.

So:

| | Step | Why here |
|---|---|---|
| 1 | **Ask Professor Mulder for the foreword.** Allow six to eight weeks. | The one step with a long lead time that nothing else depends on. Starting it now costs nothing and blocks nothing. |
| 2 | **Put the free HTML edition online.** No ISBN, no registration, no rights impediment. | It is an asset to the proposal, not a liability: an editor can read the book, and traffic is evidence of demand. Declare it in the first email regardless. |
| 3 | **Send the proposal to CRC** once the foreword is in hand, or sooner if she declines. Allow three to six months. | `CRC-PROPOSAL.md`. A foreword by a series editor is a strong signal, which is why it is worth waiting for. |
| 4 | **Then, and only then, decide on ISBNs.** If CRC accepts, they supply them. If CRC declines, apply to the NLN for a PRN and the ISBNs you need, and publish on KDP and Leanpub. | Spending money and burning numbers before the answer arrives is the one genuinely irreversible mistake available here. |

The four distribution packages are built and will not go stale: they can sit until the
decision is made. Nothing in them needs rebuilding except the paperback wrap, and only
if the page count changes.

## What is still blank, and should stay blank for now

`[ IMPRINT ]` and `ISBN 978-X-XXXXX-XXX-X` on the back cover, and the copyright page's
publisher line. Fill them when you know who the publisher is. The cover regenerates in
one command:

```
python scripts/make_back_cover.py --pages <N> --photo images/author-photo.jpg
```

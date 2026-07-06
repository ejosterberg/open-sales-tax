# Help your state without writing Python

**You do not have to be a software developer to make OpenSalesTax
better.** In fact, the scarcest and most valuable thing this project
needs isn't more Python — it's people who *know their state's sales
tax* and are willing to keep an eye on it as rates change.

If you're a tax preparer, an accountant, a bookkeeper, a business
owner who collects and remits sales tax, someone who works at a state
Department of Revenue, or just a detail-oriented resident who noticed a
rate looks wrong — this page is for you. Every path below can be walked
without opening a code editor.

> Why this matters: sales-tax rates change every quarter, across
> ~13,000 US jurisdictions, and the mistakes are subtle (a county
> surtax that expired, a city that just adopted a 1% local tax, a ZIP
> that straddles two counties). A maintainer can write the code for any
> of these in minutes — but only once someone who knows the ground
> truth tells us *what* changed and *where it's published*. That
> knowledge is the contribution.

## The one rule: cite a primary source

We can only act on a rate that's backed by a **primary source**:

- Your **state Department of Revenue** (DOR) — a rate lookup tool, a
  published rate chart, or a bulletin.
- The **statute or ordinance** that set the rate.
- The **Streamlined Sales Tax (SST) Governing Board's** published rate
  file, for the [24 SST member states](../specs/research/state-coverage.md).

We **cannot** use a number copied from a commercial tax vendor
(Avalara, TaxJar, Vertex, Sovos, TaxCloud). This isn't snobbery — it's
a deliberate legal boundary described in
[constitution §2](../specs/constitution.md). Using a vendor's data or
methods would put the whole project at risk. A DOR link is always
better anyway: it's the source the vendors themselves are copying.

You can absolutely *cross-check* against a vendor to convince yourself
something is wrong — just make sure the source you cite in the issue is
the primary one.

## Three ways to help (easiest first)

### 1. Report a wrong or missing rate — 5 minutes

This is the highest-value thing most people can do. If a ZIP returns
the wrong combined rate (or no local rate at all), open a
[rate-correction issue](https://github.com/ejosterberg/open-sales-tax/issues/new?template=rate-correction.yml).
The form walks you through it: the state, the ZIP, what the API returns
now, what it *should* be, and your source link. That's it — a
maintainer turns it into a code change and a regression test so it
never drifts back.

Good rate reports have prevented real over- and under-collection. Two
recent examples from the project's own audits: a Florida county's 1%
infrastructure surtax that had quietly hit its statutory spending cap
and ended, and a Wisconsin city's 2% tax that existed in the data but
wasn't being applied. Both were one-line truths that mattered.

### 2. Verify your state and tell us it's right — 15 minutes

"It's correct" is useful information too. Pick your state, spot-check
several ZIPs (a big city, a small town, an unincorporated area, a
special taxing district if you know one) against your DOR, and open an
issue confirming what you checked and when. That lets us mark the state
as community-verified and raise its confidence tier. If you find
problems along the way, great — that's path 1.

### 3. Adopt your state — ongoing

If you're willing to *keep* watching a state — re-checking it each
quarter when new rates publish — you can become its listed maintainer.
Open an [adopt-a-state issue](https://github.com/ejosterberg/open-sales-tax/issues/new?template=adopt-a-state.yml).
On the form you tell us how comfortable you are with Python; **"none"
is a completely valid answer.** A no-code maintainer owns the *tax
truth* for their state (verifying rates, supplying citations when
things change) and a developer-maintainer or one of the project's
automated audit runs handles the mechanical code edits. That division
of labor is the whole point: pair domain knowledge with code so neither
person has to be an expert in both.

## How to check what the API currently returns

You don't need to install anything. Two options:

**Point-and-click:** open the
[live demo](https://demo.opensalestax.org), type in a ZIP, and read the
rate breakdown.

**In a browser or terminal:** the live API has a read-only rate lookup.
Just replace the ZIP:

```
https://api.opensalestax.org/v1/rates?zip5=55401
```

Open that URL in your browser and you'll get the full jurisdiction
stack (state + county + city + any special districts) with each rate.
The `combined` figure is what a shopper at that ZIP would pay on a
general item. Compare it to your DOR's rate lookup for the same ZIP —
if they disagree, you've found something worth reporting.

> None of this is tax or legal advice, and OpenSalesTax is a
> calculation engine, not a compliance service —
> see [the disclaimer](disclaimer.md). But an extra set of
> knowledgeable eyes on a rate is exactly how a free, community-run
> engine stays trustworthy.

## Already comfortable with code?

Then the technical on-ramps are for you instead:

- [docs/state-modules.md](state-modules.md) — add a tier-2 SST state
  (about 10 lines) or promote a state to a fully maintained tier-1
  module.
- [CONTRIBUTING.md](../CONTRIBUTING.md) — dev setup, DCO sign-off, and
  the pull-request process.
- [The SST file-format field guide](legislation/sst-file-format.md) —
  a plain-English tour of the underlying quarterly data files.

Thank you for helping keep US sales-tax data free and correct for
everyone. 🙏

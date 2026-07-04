# Legislation & data-format explainers

Public, contributor-facing explainers for the non-obvious parts of US
sales-tax law and the data formats OpenSalesTax builds on. Where our
code comments and `specs/` notes capture *what* we did, these pages
explain the *why* in a way that's readable by someone coming in cold —
including people who don't work on the codebase.

> None of these pages are legal or tax advice. They describe how tax
> systems and data files actually work, compiled from primary sources
> (statutes, state Department of Revenue publications, and the
> Streamlined Sales Tax Governing Board's published files).

## Index

| Topic | What it covers |
|---|---|
| [The SST quarterly file format](sst-file-format.md) | What the Streamlined Sales Tax rate and boundary files actually look like — filename convention, the 9-column rate file, the 89/90-column boundary file, the repeating district triplets, and the format gotchas (BOM, phantom type-45 codes, ZIP+4 padding) that cost real debugging time. |

## Contributing an explainer

If, while building or maintaining a state module, you work out
something non-obvious about how a state's tax system or data source
behaves — write it down here. A single clear explanation can save the
next contributor a day of rediscovery. Keep it primary-source-cited,
free of commercial-vendor reverse-engineering (see
[constitution §2](../../specs/constitution.md)), and readable without
knowledge of the codebase.

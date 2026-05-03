# Research — Prior Art

> What sales-tax-calculation solutions exist? What do they do well?
> Where does an open-source alternative have meaningful opportunity?
> Compiled 2026-05-02.

## TL;DR — the competitive landscape

| Service | Coverage | API quality | Price (small biz) | OSS? | Self-hostable? |
|---|---|---|---|---|---|
| **Avalara AvaTax** | Excellent (US+intl) | Excellent | $$$$ ($50-500+/mo) | ❌ | ❌ |
| **Vertex** | Excellent (enterprise) | Excellent | $$$$$ (enterprise) | ❌ | Hybrid |
| **Sovos** | Excellent (enterprise) | Good | $$$$$ (enterprise) | ❌ | ❌ |
| **TaxJar (Stripe)** | Very good | Very good | $$$ ($19-99/mo + per-call) | ❌ | ❌ |
| **TaxCloud** | Good (24 SST states free) | Good | Free for SST; $$ otherwise | ❌ | ❌ |
| **Sales Tax DataLINK** | Good | Limited | $$ | ❌ | Mixed |
| **Zamp** | Good (newer) | Good | $$ | ❌ | ❌ |
| **Numeral** | Good (newer) | Good | $$ | ❌ | ❌ |
| **OpenSalesTax (this project)** | 24 SST states v1; community for rest | TBD | Free OSS / TBD SaaS | ✅ | ✅ |

**The OSS gap is real.** Every solution above is closed-source and priced
to extract maximum revenue from small businesses. The data underlying
many of them is the same free SST data we plan to use.

## Avalara AvaTax

**Market position:** the 800-pound gorilla. Used by 30,000+ businesses
including major retailers and SaaS companies. Acquired by Vista Equity
Partners 2022 for $8.4B.

**What it does well:**
- Coverage: every US state + 100+ countries
- Address-level precision via their proprietary geocoder + boundary database
- Real-time rate updates (their team monitors every rate change globally)
- Returns filing service (they file for you in addition to calculating)
- Exemption certificate management
- Robust API with mature SDKs in every major language

**Pricing (small business):**
- Starts ~$50/mo for basic
- Per-API-call charges (~$0.10-0.50 per calculation depending on tier)
- Returns filing: $50-200/mo per state
- A 5-state filer doing modest volume easily hits $300-500/mo

**Patent risk:** Avalara holds dozens of US patents on tax calculation
methods. **Apache 2.0 license for OpenSalesTax was chosen specifically
to provide patent-grant protection** to contributors and downstream
users (constitution §2).

**Where they win that we won't try to:**
- International VAT
- 50-state returns filing as a service
- Enterprise integrations with NetSuite / SAP / Salesforce

**Where their offering is weak:**
- Cost. Aggressive sales tactics. "Avalara overage" horror stories on
  Reddit are common.
- Closed data. You can't audit why a calculation was the way it was
  except by re-querying their API.
- Lock-in. Migrating off Avalara is non-trivial.

## Vertex

**Market position:** enterprise; been around since 1978. Owns
significant share of large-enterprise market.

**What it does well:** like Avalara but more enterprise-y. Better
on-premise / hybrid deployment options. Stronger industry verticals
(retail, manufacturing).

**Pricing:** enterprise. Six-figure annual contracts not unusual.

**Why not relevant to OpenSalesTax's market:** small-business doesn't
buy Vertex. They buy Avalara/TaxJar or self-administer.

## Sovos

**Market position:** enterprise. Strong international + e-invoicing.

**Same takeaway as Vertex.** Out of OpenSalesTax's positioning.

## TaxJar (Stripe)

**Market position:** SMB-focused; acquired by Stripe 2021.

**What it does well:**
- Easy to integrate
- Stripe Connect plays well with their flow
- Decent docs

**Pricing:** $19-99/mo + per-call charges above a threshold.

**Why an OSS alternative could displace them for some users:**
- Their users are price-sensitive (often Etsy / Shopify shops)
- $19-99/mo per shop adds up; many would self-host for $0/mo on
  the free tier of any cloud provider

## TaxCloud

**Market position:** unique — they leveraged SST certification to offer
**free filing** for the 24 SST member states. Partner-funded model
(member states pay TaxCloud to provide compliance services).

**What it does well:**
- Free for SST states (this is huge for compliance-burdened small biz)
- Decent API (docs at docs.taxcloud.com)
- SST-certified, so calculations are conformant

**Why an OSS alternative is still interesting:**
- TaxCloud is a closed service with a SaaS-only deployment
- Their "free" model depends on state-government partnership funding
  which could change
- Their data is licensed for use through their API only — you can't
  pull rates and use them yourself
- Self-hosting + auditability matter to some users (regulated
  industries, financial-services accounting departments)
- TaxCloud doesn't cover non-SST states well; for a CA seller you
  still need Avalara/TaxJar

**What we should learn from TaxCloud:**
- The SST certification path is real and worthwhile
- Their UI / documentation patterns are good references
- The "free for SST states" model is exactly our v1 value proposition

## Zamp / Numeral / Stripe Tax

These are newer entrants (2022-2024) trying to pick off Avalara/TaxJar
share with cleaner UX and better pricing. All closed-source. All
SaaS-only.

**Implication for OpenSalesTax:** the market is clearly receptive to
new entrants. The OSS angle differentiates us from every other
challenger.

## Existing open-source attempts

Searches as of 2026-05-02 turn up these — most are unmaintained or
narrow scope:

| Project | Language | Status | Notes |
|---|---|---|---|
| **kemitchell/us-sales-tax** | JS | Stale (~2018) | Hardcoded state-level rates only. No boundaries. |
| **TaxCloud Plug-in for WooCommerce** | PHP | Active | Plug-in only — wraps TaxCloud's closed API |
| **Various Shopify apps** | various | n/a | All wrappers around closed APIs |
| **State DOR sample code** | various | n/a | Some states publish minimal sample code (CSV → rate lookup); not usable as a library |
| **OpenSalesTax (this project)** | TBD | pre-build | The opportunity |

**The OSS gap is unfilled.** Multiple developer threads on Reddit /
HackerNews periodically lament "why is there no open-source sales tax
library?" The answer is that it's hard, the data sources are
unfriendly, and no one has built and sustained it yet.

## What separates OpenSalesTax from existing OSS attempts

Past OSS attempts failed because:
1. **One-person passion projects** that died when the maintainer
   moved on.
2. **State-level rates only** — useless when 80% of US sales tax is
   the local-jurisdiction stack (county + city + special districts).
3. **No update cadence** — rates are stale within a quarter.
4. **No tests** — no way for a user to trust the output.

OpenSalesTax addresses each:
1. **Per-state contributor model** distributes maintenance burden.
2. **SST data is jurisdiction-aware** by construction.
3. **Quarterly data updates** are part of the architecture; CLI
   command + scheduled job.
4. **SST conformance test fixtures** + per-state test suites are
   constitutional requirements.

## Pricing strategy implications (for the eventual SaaS)

If OpenSalesTax later launches a hosted SaaS layer:

- **OSS core stays free forever.** Self-hosters never pay.
- **Hosted SaaS pricing** could undercut Avalara dramatically:
  - Free tier: 100 calls/day, no SLA
  - Small-biz tier: $9-19/mo, 10k calls/mo, basic SLA
  - Pro tier: $49-99/mo, unlimited calls, SLA, priority support
  - Enterprise: custom
- **Returns-filing add-on** could be a separate paid service —
  TaxCloud demonstrated the market wants this bundled.
- **State-maintainer revenue share** could fund per-state experts:
  if the SaaS makes $X from CA users, % goes to the CA module
  maintainer. Aligns incentives for ongoing maintenance.

But: SaaS is **out of scope for v1 OSS launch** (constitution §13).
Mention only.

## Why now

- **SST data has been free and stable since 2005.** The infrastructure
  exists; no one has wrapped it.
- **Compliance burden is increasing** post-Wayfair (2018) — more
  small businesses owe in more states.
- **OSS infrastructure adoption** is accelerating; businesses are
  increasingly comfortable self-hosting (Plausible, PostHog, Cal.com,
  Mattermost, etc., all proved this market exists).
- **AI accelerates contributor onboarding.** State-by-state rule
  documentation can be drafted by Claude/GPT and reviewed by human
  state experts — much faster than human-only.
- **Eric has a captive integration target** (SC Books) to dogfood
  v1 against. Real-world pressure-testing without needing to
  recruit external users for v1.

## Differentiation summary (the elevator pitch)

> OpenSalesTax is the only **open-source, self-hostable, contributor-
> driven** US sales tax calculation API. Built on free public data,
> licensed Apache 2.0, supporting **24 SST states from day one** and
> growing through community state-maintainer modules. Free for
> self-hosters forever. Eventual hosted SaaS dramatically cheaper
> than Avalara/TaxJar.

That sentence should fit on the README and on a single conference slide.

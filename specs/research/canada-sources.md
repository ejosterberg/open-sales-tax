# Research — Canadian sales tax (out of scope for v1)

> Captured 2026-05-03 from Eric's pointer. **Out of scope for
> Phase 1 / v0.1 / v1.0** per [constitution §13](../constitution.md):
> "NOT for international tax. US sales tax / use tax only. VAT is
> a different beast."

This file exists so that if the project later expands scope to
cover Canadian sales taxes (GST + PST + HST + QST), the research
isn't lost.

## Why Canada is interesting

- Canadian provincial sales tax has the same "small businesses
  drowning in compliance" problem the US has, but at a smaller
  scale (10 provinces + 3 territories vs. 50 US states + DC + PR).
- Stack model is similar but cleaner: GST is federal (5%), then
  most provinces layer their own PST or replace it with HST
  (which combines GST + provincial). Quebec uses QST.
- Cross-border integration with US-focused accounting tools
  (SC Books, etc.) is a real desire from US/Canada-operating
  small businesses.

## Source 1: Retail Council of Canada quick-facts page

**URL:** https://www.retailcouncil.org/resources/quick-facts/sales-tax-rates-by-province/

**What it is:** a static HTML table maintained by the Retail
Council of Canada showing GST/PST/HST/QST rates per province.
Maintained by an industry association rather than a government
body, but the data tracks the official rates.

**Strengths:**
- Static HTML, easily scrapable
- Updated when rates change (announced provincially)
- Free public access; no auth wall

**Weaknesses:**
- Industry-association data, not authoritative -- always
  cross-reference against the Canada Revenue Agency (CRA) or
  the relevant provincial revenue agency before relying on a rate
- Doesn't include taxability matrices (which products are
  exempt, etc.)

## Source 2: SatelliteWP / swp-woocommerce-sales-taxes-canada

**URL:** https://github.com/SatelliteWP/swp-woocommerce-sales-taxes-canada

**What it is:** a WordPress / WooCommerce plugin (PHP) that
applies Canadian sales tax to e-commerce orders. Not a data
source per se but useful as **prior-art** for how someone has
modeled the GST/PST/HST/QST stack programmatically.

**Strengths:**
- Real working code, GPL-licensed (need to read its code with
  care -- per constitution §2 we don't reverse-engineer
  commercial APIs but reading OSS code is fine, modulo license
  contamination)
- Demonstrates the practical edge cases of Canadian sales-tax
  software in a small-business context
- Active enough to be visible on GitHub

**Weaknesses:**
- GPL licensed (we'd need to re-implement, not copy, to keep
  OpenSalesTax under Apache 2.0)
- WooCommerce-specific abstractions probably don't translate
  directly to a stateless API
- Single-maintainer project; bus factor of 1

## Authoritative sources for the eventual Canadian module

If/when we expand scope:

| Jurisdiction | Authority | URL |
|---|---|---|
| Federal (GST/HST) | Canada Revenue Agency | canada.ca/en/revenue-agency.html |
| Quebec (QST) | Revenu Québec | revenuquebec.ca |
| British Columbia (PST) | BC Ministry of Finance | gov.bc.ca/gov/content/taxes/sales-taxes |
| Saskatchewan (PST) | SK Ministry of Finance | sets.saskatchewan.ca |
| Manitoba (RST) | MB Finance | gov.mb.ca/finance/taxation |

The other provinces use HST (federal-administered) so CRA covers
them.

## What an OSS Canadian module would need

Mirror the per-state contributor pattern from the US side:

- One module per province / territory under
  `opensalestax/provinces/` (separate from `states/` to keep
  jurisdictional vocabulary distinct)
- Authority-stack model that handles GST + PST/HST/QST
  separately so the response can show breakdown
- Distinct "country" axis on jurisdictions (US vs CA) so the
  API can route correctly
- Localization (en/fr) for jurisdiction names since Quebec is
  bilingual by law

## Decision-needed before any of this happens

1. **Constitution §13 amendment** -- explicitly allow Canada (or
   broader "North America") in scope. Otherwise tier-2 US states
   should land first.
2. **Project rename consideration** -- `OpenSalesTax` reads as
   US-centric. `OpenSalesAndUseTax` is a mouthful. Maybe just
   add a tagline rather than rename.
3. **Maintainer recruitment** -- Eric isn't a Canadian sales-tax
   expert; this only works if a Canadian contributor signs on as
   provincial maintainer.

## Recommendation

**Defer to v1.x at the earliest.** US states 0 → tier 2 → tier 1
should consume the available oxygen first. When Canada lands, this
research file becomes the starting point for the constitution
amendment and the provincial-module pattern design.

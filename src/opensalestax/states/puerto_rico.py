# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Puerto Rico jurisdiction module (tier 1, non-SST, US territory).

## TERRITORIAL STATUS -- not a US state

Puerto Rico is a **US territory (commonwealth)**, not a US state. Its
sales tax is administered by the **Departamento de Hacienda de Puerto
Rico** (the Puerto Rico Treasury Department) -- NOT by the US federal
government and NOT through any state DOR. Federal US sales-tax
frameworks (such as the Streamlined Sales Tax Project) do not extend
to PR; PR is **not** an SST member because SST membership is limited
to US states.

OpenSalesTax treats PR as a peer of the 50 states + DC for module-
shape purposes (it is the 52nd entry in the catalog) but everything
in this docstring should be read with the territorial context in
mind: PR runs its own tax authority, its primary statutory sources
are codified in Spanish, and English translations are secondary
references rather than authoritative text.

## TAX MODEL: IVU (Impuesto sobre Ventas y Uso)

PR's general consumption tax is the **Impuesto sobre Ventas y Uso
(IVU)** -- in English, the "Sales and Use Tax". Despite the name
difference from "sales tax" elsewhere, the IVU is **structurally a
sales tax**: it is imposed on the buyer at the point of sale on the
retail sale of taxable items, collected by the seller, and remitted
to the Departamento de Hacienda. This is fundamentally different
from:

- Hawaii's General Excise Tax (GET) -- imposed on the seller's gross
  receipts as a privilege of doing business
- New Mexico's Gross Receipts Tax (GRT) -- imposed on the seller's
  receipts from business activities

The IVU encoding in OpenSalesTax therefore follows the standard
sales-tax shape (taxability matrix per item category, single
combined rate at the point of sale) without needing the
abstractions that AL/HI/NM require.

The IVU was enacted by **Act No. 117 of July 4, 2006** ("Ley de la
Justicia Contributiva de 2006") with an initial state-portion rate
of 5.5% + 1.5% municipal = 7.0% combined. The current 10.5% state +
1.0% municipal = 11.5% combined structure was established by **Act
No. 72 of May 29, 2015** ("Ley para Enmendar el Codigo de Rentas
Internas de Puerto Rico"), effective **July 1, 2015**. The IVU is
codified in the **Internal Revenue Code of Puerto Rico** (Codigo de
Rentas Internas de Puerto Rico) at **13 L.P.R.A. sections 32001 et
seq.** (Subtitle D, Chapters 1-3 of the Code).

## RATE STRUCTURE: 10.5% state + 1.0% municipal = 11.5% combined

PR's IVU has TWO statutory components that ALWAYS apply together at
every point of sale on the island:

1. **State portion: 10.5%** per **13 L.P.R.A. section 32021** --
   imposed by the Government of Puerto Rico, collected and
   administered by the Departamento de Hacienda. Effective
   2015-07-01 under Act No. 72 of 2015 (raised from the prior 6%
   state portion that had been in effect since 2006 with a brief
   intermediate increase to 7%).

2. **Municipal portion: 1.0%** per **13 L.P.R.A. section 32024** --
   imposed by **every one of PR's 78 municipios** (municipalities)
   under uniform statutory authority. **Unlike state-level US
   sales-tax local options, the PR municipal IVU is uniform across
   all 78 municipalities** -- there is no per-municipality variation
   in rate. The 1.0% municipal portion is collected by the
   Departamento de Hacienda alongside the state portion (a
   centralized collection regime authorized by 13 L.P.R.A. section
   32024 and implementing regulations) and is then distributed to
   the municipalities.

The **combined consumer-facing rate is therefore 11.5% at every
address in Puerto Rico**, identically.

### Encoding decision: single combined 11.5% state-level row

After consulting the per-state-research brief and the rate-stacking
patterns used by states with no per-municipality variation
(IN/KY/MI/RI), this module emits a **single combined 11.5%
authority** rather than splitting into two RateRow instances. The
rationale:

- **The consumer experience is a single 11.5% combined rate** at
  every PR address. There is no jurisdiction-shopping, no boundary
  to cross to find a different rate, no per-municipality lookup
  that an integrator would benefit from.
- **The 1.0% municipal portion is uniform and centrally collected.**
  An integrator computing tax for a PR sale receives the same
  number whether the rate is presented as 11.5% in one row or
  10.5% + 1.0% in two rows; there is no transaction-relevant
  distinction.
- **No-local-tax peer states are encoded as single rows.** ME/IN/KY/
  MI/RI all collapse to a single state-level RateRow despite having
  similar statutory structures (state-level imposition only); the
  PR encoding follows the same pattern with one extra justification
  in the docstring.
- **The legal split is documented in this docstring + the
  TaxabilityRule notes** so a future maintainer or auditor can
  trace the 11.5% back to the 10.5% + 1.0% statutory components
  without confusion.

If a later phase needs the legal split (e.g., for compliance
reporting that requires separate state and municipal lines), this
module can be revisited to emit two RateRow instances under
``parent_authority_name="Puerto Rico"`` for the 1.0% municipal
authority. The combined-rate engine output would be unchanged.

### Special IVU on B2B services (NOT applied to retail sales)

A separate **4% Special IVU on business-to-business services** (and
on certain designated services) was added by Act No. 72 of 2015,
codified at **13 L.P.R.A. section 32022**. This is a SEPARATE,
NARROWER tax on B2B service transactions and is **NOT applied to
ordinary retail sales** -- the 4% Special IVU is therefore NOT
emitted by this module's parse_rates and does NOT affect the 11.5%
combined retail rate. (B2B service taxation is out of scope for the
v1 retail-focused engine; an integrator computing tax on B2B
services in PR must apply the 4% rate separately.)

## TAXABILITY MATRIX (per Codigo de Rentas Internas; Subtitle D)

- **General tangible personal property** -- TAXABLE at the 11.5%
  combined rate per 13 L.P.R.A. section 32020 (imposition) and
  section 32011 (definition of "taxable item" -- "partida
  tributable").
- **Clothing** -- TAXABLE. PR has no general clothing exemption;
  clothing and footwear are taxable items at the full 11.5%
  combined rate. PR has historically held an annual back-to-school
  "Dias sin IVU" (Days without IVU) holiday that has covered
  uniforms and school supplies, but the holiday is enacted ad hoc
  by the legislature each year and has variable scope -- see the
  ``holidays_for(year)`` notes below.
- **Groceries (qualifying unprepared food)** -- EXEMPT per 13
  L.P.R.A. section 32023 (exemption for "alimentos e ingredientes
  de alimentos" -- food and food ingredients). The exemption was
  established by Act No. 72 of 2015 effective 2015-10-01 (the
  initial October-2015 grocery exemption was framed as a relief
  measure offsetting the state-portion rate increase from 6% to
  10.5% earlier that year). The exemption covers UNPROPERED food
  and food ingredients; **prepared food, restaurant meals,
  carbonated beverages, candy, and dietary supplements remain
  taxable** at the full 11.5% combined rate. The Departamento de
  Hacienda has clarified the prepared/unprepared distinction in
  multiple Cartas Circulares (Circular Letters); an integrator
  encoding line items must distinguish between the ``groceries``
  category (exempt) and the ``prepared_food`` category (taxable).
- **Prescription drugs** -- EXEMPT per 13 L.P.R.A. section 32023
  (exemption for "medicamentos recetados"). Over-the-counter (OTC)
  medications are TAXABLE; the exemption is limited to drugs
  dispensed pursuant to a prescription from an authorized health
  professional. Insulin, hypodermic needles, and similar
  prescription-adjacent medical supplies are also exempt under the
  same statutory framework; this module's prescription_drugs rule
  encodes the dominant case (prescribed pharmaceuticals).
- **Prepared food** -- TAXABLE at the full 11.5% combined rate.
  The grocery exemption in section 32023 expressly excludes
  prepared food, restaurant meals, and food ready for immediate
  consumption; these remain in the ordinary IVU base.
- **Digital goods** -- TAXABLE at the full 11.5% combined rate.
  PR's IVU base extends to specified digital products and to
  digital services delivered to a consumer in PR; the controlling
  provisions are in 13 L.P.R.A. sections 32011 and 32020 as
  amended by various post-2015 acts. The Departamento de Hacienda
  has issued Cartas Circulares clarifying the application of IVU
  to streaming services, downloaded software, and digital
  audio/video content. The dominant case (downloaded digital
  media, electronic delivery of software with permanent right to
  use, and SaaS subscriptions consumed in PR) is taxable; an
  integrator with edge-case digital products in PR should consult
  Hacienda's most recent Carta Circular guidance.

## SALES-TAX HOLIDAYS: "Dias sin IVU" -- ad hoc annual holiday

PR has historically held an annual back-to-school sales-tax holiday
known as **"Dias sin IVU"** (Days without IVU) covering school
uniforms and school supplies for one weekend in mid-July (typically
the first or second weekend). The holiday is **enacted ad hoc by
the legislature each year**; it is NOT a permanent recurring
exemption written into the Codigo de Rentas Internas, and the
legislature has skipped the holiday in some prior fiscal years
(notably during fiscal-stress years).

**For 2026: status NOT YET CONFIRMED via Hacienda announcement at
the time this module shipped (2026-05-03).** The Hacienda press-
release / carta-circular cycle for the 2026 "Dias sin IVU" had not
yet published an official date window or scope as of the module
ship date. Per the orchestrator's instruction in the per-state
brief: when the 2026 holiday is announced, this module's
``holidays_for(year)`` should be updated to return a HolidayWindow
with the announced dates, scope (uniforms + school supplies +/-
backpacks), and any per-item amount cap; UNTIL THEN, the method
returns an empty iterator for every year. A regression test pins
the no-holiday-yet position across 2024-2030 so a future
maintainer who adds 2026 (or 2027) holiday data must explicitly
relax the test for that year.

When the 2026 holiday is confirmed, the eventual HolidayWindow
should cite the controlling Departamento de Hacienda Carta
Circular by reference number and date. If the legislature codifies
the holiday as permanent in a future fiscal year, the docstring
above should be updated to remove the "ad hoc" framing.

## PRIMARY-SOURCE LANGUAGE NOTE

PR's primary statutory sources are codified in **Spanish** (the
governmental working language of Puerto Rico). The Codigo de
Rentas Internas de Puerto Rico is published in Spanish; English
translations exist for many provisions through commercial
publishers and through the LexisNexis L.P.R.A. ("Laws of Puerto
Rico Annotated") series, but the **Spanish text is authoritative**
in the event of any translation ambiguity.

This module's TaxabilityRule notes cite both the Spanish primary
source (statute by 13 L.P.R.A. section number, terminology in
Spanish where load-bearing) and -- where available -- English
translations from L.P.R.A. or from official Departamento de
Hacienda publications. Where a citation appears in Spanish only,
the substance has been verified against the L.P.R.A. translation
and any Hacienda Carta Circular interpreting the provision; flags
of any translation-derived ambiguity are called out in
``specs/research/references.md``.

## DEPARTAMENTO DE HACIENDA -- the tax authority

The Puerto Rico tax authority is the **Departamento de Hacienda de
Puerto Rico** ("PR Treasury Department"), not a US state DOR. Its
website is **https://hacienda.pr.gov/** (Spanish-default, with
English translations available for many publications). Hacienda
publishes:

- The current text of the Codigo de Rentas Internas (the statute)
- **Cartas Circulares** (Circular Letters) -- administrative
  guidance interpreting specific provisions
- **Boletines Informativos** (Informative Bulletins) -- shorter
  pronouncements
- **Determinaciones Administrativas** (Administrative
  Determinations) -- ruling-level guidance

For OpenSalesTax purposes, the statute (codified at 13 L.P.R.A.
sections 32001 et seq.) is the primary source; the Cartas
Circulares are cited where they clarify a statutory ambiguity
(particularly around the prepared/unprepared food distinction and
the digital-goods scope).

State maintainer: vacant -- see MAINTAINERS.md. PR is the only
US-territory module in OpenSalesTax (no other US territories --
USVI, Guam, American Samoa, Northern Mariana Islands -- are in the
catalog at this time). A maintainer with bilingual fluency and
familiarity with the Departamento de Hacienda's publication
cycle would be valuable for keeping the holiday data and Carta
Circular cross-references current.

Disclaimer: this module computes tax; it does not provide legal
or tax advice. Verify against the Departamento de Hacienda for any
compliance decision, particularly on edge cases involving the
prepared/unprepared food distinction, the digital-goods scope, or
B2B service transactions subject to the separate 4% Special IVU.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.states.protocol import (
    BoundaryRow,
    HolidayWindow,
    RateRow,
    SpecialCase,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register

# Puerto Rico IVU taxability matrix per Codigo de Rentas Internas
# (Internal Revenue Code of Puerto Rico, Subtitle D), codified at
# 13 L.P.R.A. sections 32001 et seq.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Puerto Rico at the full 11.5% "
            "combined IVU rate (10.5% state per 13 L.P.R.A. section "
            "32021 + 1.0% municipal per 13 L.P.R.A. section 32024). PR "
            "has no general clothing exemption in the Codigo de Rentas "
            "Internas; clothing and footwear are 'partidas tributables' "
            "(taxable items) under section 32011 and tax at the full "
            "rate. PR has historically held an annual ad-hoc 'Dias sin "
            "IVU' (Days without IVU) holiday covering school uniforms "
            "and school supplies, but the holiday is enacted by the "
            "legislature each year and is NOT a permanent recurring "
            "exemption -- see the holidays_for(year) docstring for the "
            "2026 status (not yet confirmed via Hacienda announcement "
            "at the time this module shipped). Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Groceries (qualifying unprepared food and food "
            "ingredients -- 'alimentos e ingredientes de alimentos') "
            "are EXEMPT in Puerto Rico per 13 L.P.R.A. section 32023. "
            "The exemption was established by Act No. 72 of May 29, "
            "2015 effective 2015-10-01 as a relief measure offsetting "
            "the state-portion rate increase to 10.5%. The exemption "
            "covers unprepared food only; PREPARED FOOD, RESTAURANT "
            "MEALS, CARBONATED BEVERAGES, CANDY, and DIETARY "
            "SUPPLEMENTS remain TAXABLE at the full 11.5% combined "
            "rate. Integrators encoding line items must distinguish "
            "between the 'groceries' category (exempt under section "
            "32023) and the 'prepared_food' category (taxable under "
            "the general imposition of section 32020). The Departamento "
            "de Hacienda has clarified the prepared/unprepared "
            "distinction in multiple Cartas Circulares; consult the "
            "most recent Hacienda guidance for edge cases. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs ('medicamentos recetados') are EXEMPT "
            "in Puerto Rico per 13 L.P.R.A. section 32023. The "
            "exemption is limited to drugs dispensed pursuant to a "
            "prescription from an authorized health professional; "
            "OVER-THE-COUNTER (OTC) MEDICATIONS ARE TAXABLE at the "
            "full 11.5% combined rate. Insulin, hypodermic syringes, "
            "and similar prescription-adjacent medical supplies are "
            "also exempt under the same statutory framework. This "
            "rule encodes the dominant case (physician-prescribed "
            "pharmaceuticals); an integrator handling OTC medication "
            "line items in PR should categorize them under 'general' "
            "rather than 'prescription_drugs'. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food, restaurant meals, and food ready for "
            "immediate consumption are TAXABLE in Puerto Rico at the "
            "full 11.5% combined IVU rate per the general imposition "
            "of 13 L.P.R.A. section 32020. The grocery exemption in "
            "section 32023 EXPRESSLY EXCLUDES prepared food, "
            "restaurant meals, and food ready for immediate "
            "consumption from its scope; those items therefore remain "
            "in the ordinary IVU base. The Departamento de Hacienda's "
            "Cartas Circulares interpreting the prepared/unprepared "
            "boundary should be consulted for edge cases (deli items, "
            "rotisserie chicken, hot bar items, etc.). Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods are TAXABLE in Puerto Rico at the full "
            "11.5% combined IVU rate. PR's IVU base extends to "
            "specified digital products and to digital services "
            "delivered to a consumer in PR; the controlling provisions "
            "are 13 L.P.R.A. sections 32011 (taxable-item definition) "
            "and 32020 (general imposition) as amended by post-2015 "
            "acts. The Departamento de Hacienda has issued Cartas "
            "Circulares clarifying the application of IVU to "
            "streaming services, downloaded software, and digital "
            "audio/video content; the dominant case (downloaded "
            "digital media, electronic delivery of software with "
            "permanent right to use, and SaaS subscriptions consumed "
            "in PR) is taxable. Edge cases in B2B digital services "
            "may instead fall under the SEPARATE 4% Special IVU on "
            "B2B services (13 L.P.R.A. section 32022) rather than "
            "the 11.5% retail rate -- consult Hacienda guidance for "
            "B2B service transactions. Calculation only -- not legal "
            "or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in Puerto "
            "Rico at the 11.5% combined IVU rate (10.5% state per 13 "
            "L.P.R.A. section 32021 + 1.0% municipal per 13 L.P.R.A. "
            "section 32024). The rate is uniform across all 78 PR "
            "municipalities -- there is NO per-municipality variation "
            "(unlike state-level US sales-tax local options). The "
            "1.0% municipal portion is centrally collected by the "
            "Departamento de Hacienda and distributed to the "
            "municipalities. PR is a US TERRITORY (commonwealth), not "
            "a US state; the IVU is administered by the Departamento "
            "de Hacienda de Puerto Rico, not by any US federal or "
            "state authority, and PR is NOT an SST member. A separate "
            "4% Special IVU on B2B services (13 L.P.R.A. section "
            "32022) applies to designated business-to-business "
            "service transactions and is OUT OF SCOPE for the v1 "
            "retail engine -- this module emits the 11.5% retail rate "
            "only. Calculation only -- not legal or tax advice."
        ),
    ),
}

# IVU effective date: July 1, 2015 -- the date the current 10.5%
# state portion + 1.0% municipal = 11.5% combined structure took
# effect under Act No. 72 of May 29, 2015 ("Ley para Enmendar el
# Codigo de Rentas Internas de Puerto Rico"). The IVU itself was
# originally enacted by Act No. 117 of July 4, 2006 with a different
# rate structure; pin effective_from to 2015-07-01 because that is
# when the current 11.5% combined rate first applied to taxable
# transactions.
_RATE_EFFECTIVE_FROM = dt.date(2015, 7, 1)


class PuertoRico:
    """Puerto Rico IVU module (tier 1; 11.5% combined; US territory)."""

    state_abbrev: str = "PR"
    state_name: str = "Puerto Rico"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # PR is not an SST member and has no SST upstream file. The IVU
    # rate is set by statute and is uniform across the territory, so
    # parse_rates returns the same combined row regardless of
    # source_file -- the loader must skip the cache-file requirement
    # for PR.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield Puerto Rico's combined 11.5% IVU rate.

        ``source_file`` is intentionally ignored -- PR is not an SST
        member and has no upstream rate file. Pass ``None`` from the
        loader.

        Encoding decision: this method emits a SINGLE 11.5%
        territory-level RateRow rather than splitting into a 10.5%
        state component + 1.0% municipal component. The legal split
        is documented in this module's docstring; the consumer-facing
        rate at every PR address is uniformly 11.5%, so the single-
        row encoding matches the IN/KY/MI/RI/ME no-local-tax
        precedent. (See the module docstring's "Encoding decision"
        section for the full rationale.)

        The separate 4% Special IVU on B2B services (13 L.P.R.A.
        section 32022) is OUT OF SCOPE for the v1 retail engine and
        is NOT emitted here.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Puerto Rico",
            authority_type="state",
            rate_pct=Decimal("11.500"),
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """No boundary rows: PR's IVU is uniform across the territory.

        Although PR has 78 municipalities, the 1.0% municipal IVU is
        STATUTORILY UNIFORM across all of them (per 13 L.P.R.A.
        section 32024). There is no per-municipality variation and
        no boundary lookup that would resolve to a different rate.
        The single 11.5% territory-level authority covers every PR
        address.
        """
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return Puerto Rico's IVU taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases consumed by the engine in v1.

        The separate 4% Special IVU on B2B services (13 L.P.R.A.
        section 32022) is documented in this module's docstring and
        in ``specs/research/references.md`` for follow-up work once
        the engine supports a B2B-service-tax sub-base. The
        prepared/unprepared food distinction is encoded directly via
        the groceries vs. prepared_food taxability rules.
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Puerto Rico's "Dias sin IVU" holiday status: NOT YET CONFIRMED for 2026.

        PR has historically held an annual back-to-school sales-tax
        holiday ("Dias sin IVU" -- Days without IVU) covering school
        uniforms and school supplies, but the holiday is enacted
        AD HOC by the legislature each year and is NOT a permanent
        recurring exemption written into the Codigo de Rentas
        Internas. The legislature has skipped the holiday in some
        prior fiscal years.

        As of this module's ship date (2026-05-03), the
        Departamento de Hacienda had NOT YET issued an official
        Carta Circular announcing the 2026 holiday dates or scope.
        Per the per-state brief's instruction, this method returns
        an empty iterator for every year UNTIL the 2026 (or
        subsequent) holiday is officially announced; when an
        announcement appears, this module should be updated to
        return a HolidayWindow with the announced dates, scope
        (uniforms + school supplies +/- backpacks), any per-item
        amount cap, and a citation to the controlling Carta
        Circular by reference number and date.

        A regression test pins this no-holiday-yet position across
        2024-2030 so a future maintainer who adds holiday data must
        explicitly relax the test for the affected year.

        Returns an empty iterator for every year.
        """
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = PuertoRico()
del _PROTOCOL_CHECK

PUERTO_RICO = register(PuertoRico())

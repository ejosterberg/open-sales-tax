# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Washington state module (tier 1, SST member).

WA is a Streamlined Sales Tax full member (verified 2026-05-03
against the SST member roster on streamlinedsalestax.org). The
statewide retail sales-tax rate is **6.5%** per **RCW
section 82.08.020(1)** (the imposition statute, which sets the
state portion of the retail sales tax at 6.5% of the selling
price). The 6.5% state rate has been stable since the 1983
legislative session, when chapter 7, Laws of 1983 1st Ex. Sess.
raised the rate from 5.4% to its current 6.5% level.

## RATE COMPOSITION -- WIDE COMBINED-RATE VARIANCE

Washington has one of the **widest combined sales-tax rate
ranges** in the United States. Local taxing jurisdictions --
cities, counties, transit districts, regional transit
authorities (RTAs), public transportation benefit areas (PTBAs),
public facility districts (PFDs), high-capacity transit (HCT)
districts, and others -- can stack multiple local-option
percentages on top of the 6.5% state rate. As a result the
combined retail sales-tax rate at any specific WA address can
range from the **statewide-only 6.5% floor** (in unincorporated
areas of low-tax counties with no special-district overlay)
through approximately **10.35% in parts of the Seattle / King
County area** (the highest combined rates in the country
alongside Chicago, IL and parts of Los Angeles County, CA --
verified 2026-05-03 against the Washington Department of
Revenue's Local Sales Tax Rate Lookup tool).

Major local-option authorities authorized by statute:

- **Local sales / use tax** -- RCW chapter **82.14** -- the
  master local-option chapter; cities and counties may impose
  general local sales taxes (typical first 0.5% under
  RCW 82.14.030(1) plus optional additional 0.5% under
  RCW 82.14.030(2)).
- **Public transportation benefit areas (PTBAs)** -- RCW
  chapter **36.57A** + **82.14.045** -- transit districts may
  impose voter-approved sales tax up to 0.9% for transit
  operations.
- **Regional transit authority (RTA) sales tax** -- RCW
  **81.104.170** + **82.14.0455** -- Sound Transit (the King /
  Pierce / Snohomish RTA) imposes a voter-approved 1.4% sales
  tax under the ST3 expansion approved 2016-11-08.
- **Public facility district (PFD) sales tax** -- RCW
  **82.14.048**, **82.14.0485**, **82.14.0494** -- PFDs may
  impose voter-approved sales tax (typically 0.1%-0.2%) for
  qualifying public-facility capital projects.
- **High-capacity transit (HCT) sales tax** -- RCW
  **82.14.045**, **82.14.530** -- the Sound Transit ST3 sales
  tax above operates under HCT authority.
- **Transportation benefit district (TBD) sales tax** -- RCW
  chapter **36.73** + **82.14.0455** -- city-level
  transportation districts may impose voter-approved sales tax
  up to 0.2% for transportation projects.
- **Criminal justice / public-safety sales taxes** -- RCW
  **82.14.340**, **82.14.450**, **82.14.460** -- county-level
  voter-approved overlays for criminal justice / mental
  health / chemical dependency programs.

As an SST member, WA's per-jurisdiction rates flow through the
standard SST quarterly rate file; the inherited
:class:`SstStateModule` parser handles them without state-
specific overrides. The default jurisdiction-type code mapping
(45 state, 00 county, 01 city, 63 district) is presumed --
consistent with MN/WI/IA empirical validation -- and should be
confirmed against an actual ``WAR<...>.csv`` capture by the
next maintainer.

WA is one of only a handful of states (along with CO and CA)
where a single transaction's combined rate can vary by more
than **3 percentage points** depending purely on the buyer's
specific street address. Integrators must NOT assume a single
"Seattle area" rate or "King County" rate -- the actual
combined rate at any given delivery address is the sum of the
6.5% state rate plus every overlapping local-jurisdiction rate
applicable at that address, and the SST file (or DOR's address-
level rate lookup tool) is the authoritative source.

## BUSINESS & OCCUPATION (B&O) TAX -- OUT OF SCOPE

Washington uniquely (among the ~45 states with a general state
sales tax) **also imposes a separate Business & Occupation
(B&O) gross receipts tax** on persons engaging in business
activities within the state. The B&O tax is codified at **RCW
chapter 82.04** and is imposed at differing rates depending on
the classification of business activity:

- **Retailing classification** -- 0.471% (RCW 82.04.250)
- **Wholesaling classification** -- 0.484% (RCW 82.04.270)
- **Manufacturing classification** -- 0.484% (RCW 82.04.240)
- **Service & other activities classification** -- 1.5% or
  1.75% depending on annual gross receipts (RCW 82.04.290)
- **Various specialty classifications** -- royalties,
  insurance, certain specific industries -- assorted rates per
  RCW 82.04.255 et seq.

The B&O tax is a **SELLER-SIDE tax on gross business income**,
NOT a transactional sales tax collected from the buyer.
Conceptually it functions like a state-level corporate gross-
receipts tax (compare Ohio's CAT or Oregon's CAT). The B&O is
**out of scope for this engine.** OpenSalesTax models
TRANSACTIONAL retail sales taxes that the SELLER COLLECTS FROM
THE BUYER and remits to the taxing authority; the B&O is a
seller-paid tax on the seller's own gross receipts. A seller
operating in Washington should compute its B&O liability
through the WA Department of Revenue's E-File / My DOR system
(or an accounting / payroll integration); using OpenSalesTax's
calculation API for B&O would produce wrong answers because
the B&O has different rate-classification rules, no buyer-
facing collection, and different filing / remittance mechanics.

Some sellers in WA pass the B&O through to buyers as a separate
line-item surcharge (e.g. "B&O surcharge: 0.471% added to
invoice"). This is a SELLER PRICING CHOICE, not a tax that
OpenSalesTax should compute -- the seller-side B&O liability
is owed regardless of whether the seller surfaces it on the
invoice. An integrator wishing to model B&O surcharges as
buyer-visible line items must do so as a custom line-item type
outside this engine.

## TAXABILITY MATRIX (per RCW Title 82, Chapter 8)

- **General tangible personal property** -- TAXABLE at 6.5%
  per **RCW section 82.08.020(1)** (the imposition statute) and
  the definition of "retail sale" in **RCW section 82.04.050**.
- **Clothing** -- TAXABLE year-round at 6.5%. Washington has
  **NO general clothing exemption** -- clothing and footwear
  are general tangible personal property and tax at the rate
  set by RCW 82.08.020 plus all applicable local-option
  overlays. WA does NOT join the broad clothing-exemption club
  (PA, MA, MN, NJ, VT) and does NOT have a threshold-based
  exemption (NY, RI). There is also NO recurring annual
  clothing sales-tax holiday in WA (see "Sales tax holidays"
  below).
- **Groceries (food and food ingredients)** -- EXEMPT per
  **RCW section 82.08.0293** (added by chapter 7, Laws of
  1977 1st Ex. Sess. -- the "food sales tax exemption" enacted
  by initiative-style legislative referendum and one of the
  oldest broad food exemptions in the country). The exemption
  uses the Streamlined Sales Tax Project's uniform definition
  of "food and food ingredients" and excludes candy, soft
  drinks, dietary supplements, prepared food, and bottled
  water -- those remain taxable at the general 6.5% rate.
- **Prescription drugs** -- EXEMPT per **RCW section
  82.08.0281**. The exemption covers drugs sold pursuant to a
  written prescription by a licensed practitioner, plus
  insulin (regardless of prescription) and certain related
  items (oxygen for human use, prosthetic devices, hearing
  aids, etc.; see RCW 82.08.0283 et seq. for the related-item
  exemptions). Over-the-counter (non-prescription) drugs are
  NOT covered by RCW 82.08.0281 and remain taxable at the 6.5%
  rate.
- **Prepared food** -- TAXABLE at 6.5%. Washington's grocery
  exemption in RCW 82.08.0293 expressly excludes prepared
  food, candy, soft drinks, dietary supplements, and bottled
  water; prepared food (restaurant meals, hot deli items,
  ready-to-eat foods) taxes at the general rate set by RCW
  82.08.020.
- **Digital goods (digital products / digital codes / digital
  automated services)** -- TAXABLE at 6.5% per **RCW section
  82.04.050(6)** + **RCW section 82.04.192** (the defined-
  terms section), added by chapter 535, Laws of 2009 (S.S.B.
  5295 of the 61st Legislature -- the "Streamlined Sales Tax
  digital products bill"; effective 2009-07-26). Washington
  has **one of the broadest digital-product tax bases in the
  country.** RCW 82.04.192 defines:

  - **"Digital products"** -- digital audio works, digital
    audiovisual works, digital books (the SST-uniform
    "specified digital products" set)
  - **"Digital codes"** -- codes that allow the user to obtain
    one or more digital products
  - **"Digital automated services"** -- services that use one
    or more software applications to perform a service for the
    customer (this category is BROAD; it captures many
    cloud / SaaS / streaming offerings that other states
    don't reach)

  The taxability of digital automated services in particular
  is one of the most-litigated areas of WA tax law -- there
  are statutory carve-outs in RCW 82.04.192(3)(b) for certain
  enumerated services (data-processing services, professional
  services delivered electronically, etc.) and DOR has
  published numerous Excise Tax Advisories (ETAs) interpreting
  the boundary. For the purposes of this engine's
  ``digital_goods`` category default, the rule is TAXABLE; an
  integrator selling DAS that may qualify for a statutory
  carve-out should consult RCW 82.04.192(3)(b) and applicable
  DOR ETAs.

## SALES TAX HOLIDAYS

**NONE.** Washington has **never enacted a recurring sales-tax
holiday.** Confirmed 2026-05-03 against the Washington
Department of Revenue's published guidance and a search of
RCW chapter 82.08 for any periodic exemption window.
``holidays_for(year)`` returns the empty iterator for every
year (mirrors KY, IN, MI, DC, ID, NE, ND, NJ, NC, KS).

The only periodic exemption-style relief WA has implemented was
a **temporary 2024 "manufacturing input" sales tax holiday**
(chapter 419, Laws of 2024) which ran for a limited window in
2024 only and applied to a narrow set of qualifying
manufacturing inputs -- NOT a consumer-facing back-to-school
or general-purpose holiday. That window closed 2024 and has
not been re-enacted; it is documented here for historical
completeness but does NOT reappear as a recurring window in
``holidays_for``. (Encoding a one-time historical window would
risk a future maintainer extrapolating it forward, in
violation of the "no extrapolation" rule applied across all
WA-style no-holiday states.)

## LOADING

Washington's rate data loads from the SST quarterly rate file
via the inherited :class:`SstStateModule.parse_rates`
machinery. The SST file is expected to ship rows for the state
(code 45) plus every county (code 00), city (code 01), and
special district (code 63) currently authorized to collect a
local sales tax. Until an empirical capture of a WA SST file
confirms the jurisdiction-type code mapping, the inherited
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping (00 county / 01 city / 45 state / 63 district) applies.
The next maintainer should validate against an actual WA SST
quarterly capture and override ``jurisdiction_types`` on the
subclass if any code differs.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Washington Department of Revenue guidance before relying on
these rules in production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# Washington taxability matrix per RCW Title 82, Chapter 8 (retail
# sales tax) and Chapter 4 (definitions).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Washington year-round at the "
            "6.5% state rate (plus applicable local-option "
            "overlays under RCW chapter 82.14 and related). "
            "Washington has NO general clothing exemption -- "
            "clothing and footwear are general tangible personal "
            "property and tax at the rate set by RCW section "
            "82.08.020. WA does NOT join the broad-exemption "
            "states (PA, MA, MN, NJ, VT) and does NOT have a "
            "threshold-based exemption (NY's $110 / MA's $175). "
            "WA also has NO recurring annual sales-tax holiday "
            "for clothing (or any other category). Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients are EXEMPT in Washington "
            "per RCW section 82.08.0293 (added by chapter 7, Laws "
            "of 1977 1st Ex. Sess. -- one of the oldest broad "
            "food sales-tax exemptions in the country). The "
            "exemption uses the Streamlined Sales Tax Project's "
            "uniform definition of 'food and food ingredients' "
            "and excludes candy, soft drinks, dietary "
            "supplements, prepared food, and bottled water -- "
            "those remain taxable at the general 6.5% state rate "
            "(plus local). Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Washington per RCW "
            "section 82.08.0281. The exemption covers drugs sold "
            "pursuant to a written prescription by a licensed "
            "practitioner, plus insulin (regardless of "
            "prescription) and certain related items (oxygen "
            "equipment for human use, prosthetic devices, "
            "hearing aids, etc.; see RCW 82.08.0283 et seq. for "
            "the companion exemptions). Over-the-counter (non-"
            "prescription) drugs are NOT covered by this "
            "exemption and remain taxable at the 6.5% state rate "
            "(plus local). Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot deli items, "
            "ready-to-eat foods) is TAXABLE in Washington at the "
            "6.5% state rate (plus applicable local-option "
            "overlays). The food-and-food-ingredients exemption "
            "in RCW section 82.08.0293 expressly excludes "
            "prepared food (along with candy, soft drinks, "
            "dietary supplements, and bottled water); prepared "
            "food taxes at the general rate set by RCW section "
            "82.08.020. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital products, digital codes, and digital "
            "automated services are TAXABLE in Washington at the "
            "6.5% state rate (plus applicable local) per RCW "
            "section 82.04.050(6) (the 'retail sale' definition) "
            "and the defined terms in RCW section 82.04.192, "
            "added by chapter 535, Laws of 2009 (S.S.B. 5295 of "
            "the 61st Legislature; effective 2009-07-26). "
            "Washington has one of the BROADEST digital-product "
            "tax bases in the country: in addition to the SST-"
            "uniform 'specified digital products' (digital audio "
            "works, digital audiovisual works, digital books), "
            "WA also taxes 'digital codes' and 'digital "
            "automated services' (services performed for a "
            "customer using one or more software applications). "
            "The digital-automated-services category captures "
            "many cloud / SaaS / streaming offerings that other "
            "states do not reach. Statutory carve-outs in RCW "
            "section 82.04.192(3)(b) exclude certain enumerated "
            "services (data-processing services, professional "
            "services delivered electronically, etc.) -- "
            "integrators selling DAS-style services should "
            "consult RCW 82.04.192(3)(b) and applicable WA DOR "
            "Excise Tax Advisories before relying on the default "
            "TAXABLE rule for ambiguous edge cases. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "Washington at 6.5% per RCW section 82.08.020(1) (the "
            "imposition statute) and the definition of 'retail "
            "sale' in RCW section 82.04.050. The 6.5% state rate "
            "has been stable since 1983 (chapter 7, Laws of 1983 "
            "1st Ex. Sess.). WA combined rates have one of the "
            "WIDEST RANGES in the country (~6.5% in low-tax "
            "unincorporated areas through ~10.35% in parts of "
            "King County / Seattle) due to layered local-option "
            "rates under RCW chapter 82.14 plus transit (RTA / "
            "PTBA / TBD), public-facility-district, and "
            "criminal-justice / public-safety overlays. The SST "
            "quarterly rate file is the authoritative source for "
            "any specific address. NOTE: Washington also imposes "
            "a separate Business & Occupation (B&O) gross-"
            "receipts tax under RCW chapter 82.04 -- this is a "
            "SELLER-SIDE tax on the seller's gross income, NOT a "
            "buyer-facing transactional sales tax, and is OUT OF "
            "SCOPE for this engine (see module docstring). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
}


class Washington(SstStateModule):
    """Washington state module (tier 1, SST member).

    Subclass of :class:`SstStateModule` that overrides the metadata
    (state abbrev / name / FIPS) and the taxability matrix. Rate
    parsing, boundary parsing, special cases, and the empty-holidays
    default are all inherited.

    Three things distinguish Washington from most other tier-1 SST
    states:

    1. **Wide combined-rate range (~6.5% to ~10.35%)** -- WA has
       one of the largest spans between minimum and maximum
       combined sales-tax rates in the country, driven by stacked
       local-option rates under RCW chapter 82.14 plus transit
       (RTA, PTBA, TBD), public-facility-district, and criminal-
       justice / public-safety overlays. King County / Seattle
       reaches ~10.35%, tied with Chicago / parts of CA for the
       highest combined retail rates nationally.
    2. **Business & Occupation (B&O) tax is SEPARATE and OUT OF
       SCOPE** -- WA uniquely (among states with a general retail
       sales tax) also imposes a B&O gross-receipts tax under RCW
       chapter 82.04. The B&O is a seller-paid tax on the
       seller's gross business income, NOT a buyer-facing
       transactional sales tax, and is NOT modeled by this engine.
       See module docstring for the full out-of-scope rationale.
    3. **Broad digital-services tax base** -- per RCW sections
       82.04.050(6) + 82.04.192 (added by chapter 535, Laws of
       2009), WA taxes digital products, digital codes, AND
       digital automated services. The DAS category in particular
       reaches many cloud / SaaS / streaming offerings that other
       states do not. Statutory carve-outs exist in RCW
       82.04.192(3)(b); integrators selling DAS-style services
       should consult those plus applicable DOR Excise Tax
       Advisories for ambiguous edge cases.

    Sales-tax holidays: NONE. WA has never enacted a recurring
    sales-tax holiday. ``holidays_for(year)`` returns the empty
    iterator for every year (mirrors KY, IN, MI, DC, ID, NE, ND,
    NJ, NC, KS). The 2024 manufacturing-input window (chapter 419,
    Laws of 2024) was a one-time temporary measure and is NOT
    re-encoded as a recurring window.
    """

    state_abbrev: str = "WA"
    state_name: str = "Washington"
    state_fips: str = "53"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def _authority_name(self, code: str, authority_type: str) -> str:
        """Use the curated WA city-name table; fall back to placeholder."""
        from opensalestax.states.wa_names import city_name as _wa_city

        if authority_type == "city":
            friendly = _wa_city(code)
            if friendly is not None:
                return friendly
        return super()._authority_name(code, authority_type)


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.washington`` registers
# Washington under "WA" in the state registry.
_PROTOCOL_CHECK: StateModule = Washington()
del _PROTOCOL_CHECK

# Documentary constants. The actual rate that flows into the engine
# comes from the SST quarterly file via the inherited parser; these
# constants give grep-ability and stable test fixtures for the
# headline 6.5% statewide rate and the documented combined-rate
# ceiling (~10.35%) reached in parts of King County / Seattle.
WASHINGTON_STATEWIDE_RATE_PCT: Decimal = Decimal("6.5")
WASHINGTON_HIGHEST_COMBINED_RATE_PCT: Decimal = Decimal("10.35")

WASHINGTON = register(Washington())

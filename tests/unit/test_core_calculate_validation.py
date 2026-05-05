# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for input validation in the calculate module.

These don't require a database -- they test the Python-level
input contract for LineItem and the lookup helpers.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from opensalestax.core.calculate import (
    TAX_QUANTUM,
    CalculatedLine,
    JurisdictionResult,
    LineItem,
    _apply_threshold,
)
from opensalestax.core.lookup import (
    _pick_closest_per_type,
    _pick_one_city_county_per_zip5,
    lookup_jurisdictions_by_zip,
)


def test_line_item_rejects_negative_amount() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        LineItem(amount=Decimal("-1"))


def test_line_item_zero_amount_allowed() -> None:
    item = LineItem(amount=Decimal("0"))
    assert item.amount == Decimal("0")


def test_line_item_default_category() -> None:
    item = LineItem(amount=Decimal("100"))
    assert item.category == "general"


def test_tax_quantum_is_4dp() -> None:
    assert Decimal("0.0001") == TAX_QUANTUM


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_zip", ["1234", "123456", "abcde", ""])
async def test_lookup_rejects_bad_zip5(bad_zip: str) -> None:
    """The lookup function rejects malformed ZIP5 before hitting the DB."""
    with pytest.raises(ValueError, match="zip5"):
        # session arg never used because validation fails first
        await lookup_jurisdictions_by_zip(session=None, zip5=bad_zip)  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_zip4", ["abcd", "12a4", " "])
async def test_lookup_rejects_bad_zip4(bad_zip4: str) -> None:
    with pytest.raises(ValueError, match="zip4"):
        await lookup_jurisdictions_by_zip(
            session=None,  # type: ignore[arg-type]
            zip5="55401",
            zip4=bad_zip4,
        )


def test_jurisdiction_tax_field_defaults_to_zero() -> None:
    """JurisdictionResult.tax defaults to 0 so non-engine callers don't break."""
    j = JurisdictionResult(name="Minnesota", type="state", rate_pct=Decimal("6.875"))
    assert j.tax == Decimal("0")


def test_jurisdiction_breakdown_reconciles_to_line_total() -> None:
    """Per-jurisdiction tax sums to line tax exactly (no rounding drift).

    Given a $99.99 line at MN's full Minneapolis stack
    (state 6.875% + county 0.15% + city 0.5%), each jurisdiction
    is quantized to 4dp, then summed. The sum is the line total.
    """
    amount = Decimal("99.99")
    jurisdictions = [
        JurisdictionResult(
            name="Minnesota",
            type="state",
            rate_pct=Decimal("6.875"),
            tax=(amount * Decimal("6.875") / Decimal("100")).quantize(TAX_QUANTUM),
        ),
        JurisdictionResult(
            name="Hennepin County",
            type="county",
            rate_pct=Decimal("0.15"),
            tax=(amount * Decimal("0.15") / Decimal("100")).quantize(TAX_QUANTUM),
        ),
        JurisdictionResult(
            name="City of Minneapolis",
            type="city",
            rate_pct=Decimal("0.5"),
            tax=(amount * Decimal("0.5") / Decimal("100")).quantize(TAX_QUANTUM),
        ),
    ]
    line_tax = sum((j.tax for j in jurisdictions), Decimal("0"))
    line = CalculatedLine(
        amount=amount,
        category="general",
        tax=line_tax,
        rate_pct=Decimal("7.525"),
        jurisdictions=jurisdictions,
    )
    assert line.tax == sum((j.tax for j in line.jurisdictions), Decimal("0"))
    # state $99.99 * 0.06875 = $6.87431... -> $6.8743 (HALF_UP)
    # county $99.99 * 0.0015 = $0.14998... -> $0.1500 (HALF_UP)
    # city $99.99 * 0.005 = $0.49995 -> $0.5000 (HALF_UP)
    # sum = $7.5243 (vs $99.99 * 7.525% = $7.524247... = $7.5242 round-then-sum)
    # Per-jurisdiction-then-sum drifts by 1 quantum here -- and that's
    # the point: per-jurisdiction is the source of truth so accounting
    # callers can reconcile state/county/city splits against the line.
    assert line.tax == Decimal("7.5243")


def _threshold_rule(
    threshold: Decimal,
    semantic: str | None,
    notes: str | None = None,
) -> SimpleNamespace:
    """Build a minimal stand-in for an ORM TaxabilityRule for the helper."""
    return SimpleNamespace(
        taxable_threshold_amount=threshold,
        threshold_semantic=semantic,
        notes=notes,
    )


class TestApplyThresholdBelowExempt:
    """``below_exempt`` semantic: amount strictly < threshold -> fully exempt."""

    def test_below_threshold_returns_zero_line(self) -> None:
        rule = _threshold_rule(Decimal("110.00"), "below_exempt")
        outcome = _apply_threshold(rule, Decimal("50.00"), "NY", "clothing")
        assert outcome.zero_line is True
        assert outcome.taxable_basis == Decimal("0")
        assert outcome.note is not None

    def test_at_threshold_taxes_full_amount(self) -> None:
        rule = _threshold_rule(Decimal("110.00"), "below_exempt")
        outcome = _apply_threshold(rule, Decimal("110.00"), "NY", "clothing")
        assert outcome.zero_line is False
        assert outcome.taxable_basis == Decimal("110.00")
        assert outcome.note is None

    def test_above_threshold_taxes_full_amount(self) -> None:
        rule = _threshold_rule(Decimal("110.00"), "below_exempt")
        outcome = _apply_threshold(rule, Decimal("250.00"), "NY", "clothing")
        assert outcome.zero_line is False
        assert outcome.taxable_basis == Decimal("250.00")

    def test_uses_rule_notes_when_provided(self) -> None:
        rule = _threshold_rule(
            Decimal("110.00"), "below_exempt", notes="NY: clothing under $110 is exempt."
        )
        outcome = _apply_threshold(rule, Decimal("50.00"), "NY", "clothing")
        assert outcome.note == "NY: clothing under $110 is exempt."


class TestApplyThresholdAboveExcess:
    """``above_excess`` semantic: tax only the excess above the threshold."""

    def test_at_or_below_threshold_returns_zero_line(self) -> None:
        rule = _threshold_rule(Decimal("175.00"), "above_excess")
        # at threshold
        outcome = _apply_threshold(rule, Decimal("175.00"), "MA", "clothing")
        assert outcome.zero_line is True
        # below threshold
        outcome = _apply_threshold(rule, Decimal("100.00"), "MA", "clothing")
        assert outcome.zero_line is True

    def test_above_threshold_taxes_only_excess(self) -> None:
        rule = _threshold_rule(Decimal("175.00"), "above_excess")
        outcome = _apply_threshold(rule, Decimal("300.00"), "MA", "clothing")
        assert outcome.zero_line is False
        assert outcome.taxable_basis == Decimal("125.00")
        assert outcome.note is not None
        assert "first" in outcome.note.lower() or "excess" in outcome.note.lower()

    def test_above_excess_rhode_island_250(self) -> None:
        """RI's $250 clothing exemption -- $400 jacket has $150 taxable."""
        rule = _threshold_rule(Decimal("250.00"), "above_excess")
        outcome = _apply_threshold(rule, Decimal("400.00"), "RI", "clothing")
        assert outcome.taxable_basis == Decimal("150.00")


def test_apply_threshold_unknown_semantic_falls_back_to_full_basis() -> None:
    """An unrecognized semantic value taxes the full amount (safest default)."""
    rule = _threshold_rule(Decimal("100.00"), "made_up_semantic")
    outcome = _apply_threshold(rule, Decimal("500.00"), "QQ", "clothing")
    assert outcome.zero_line is False
    assert outcome.taxable_basis == Decimal("500.00")
    assert outcome.note is None


# ---------------------------------------------------------------------------
# _pick_closest_per_type — loose-fallback disambiguation
# ---------------------------------------------------------------------------
def _stub_authority(id_: int, name: str, authority_type: str):
    return SimpleNamespace(id=id_, name=name, authority_type=authority_type)


class TestPickClosestPerType:
    """Loose fallback should pick ONE city per type when a ZIP straddles cities.

    Before the fix, OK 73069-6107 returned BOTH Norman (city 52500) and
    Moore (city 49200), summing two city tax rates and yielding 12.625%
    instead of the correct 8.5%. The fallback now picks the city whose
    nearest +4 range is closest to the requested +4.
    """

    def test_returns_closest_city_when_two_overlap(self) -> None:
        norman = _stub_authority(1, "Norman", "city")
        moore = _stub_authority(2, "Moore", "city")
        rows = [
            (norman, "1000", "1018"),
            (norman, "6000", "6099"),
            (moore, "8061", "8062"),
        ]
        picked = _pick_closest_per_type(rows, "6107")
        assert [a.name for a in picked] == ["Norman"]

    def test_picks_each_type_independently(self) -> None:
        city = _stub_authority(1, "Norman", "city")
        county = _stub_authority(2, "Cleveland County", "county")
        rows = [
            (city, "6000", "6099"),
            (county, "0", "9999"),
        ]
        picked = _pick_closest_per_type(rows, "6107")
        types = sorted(a.authority_type for a in picked)
        assert types == ["city", "county"]

    def test_zero_distance_when_inside_range(self) -> None:
        a = _stub_authority(1, "A", "city")
        b = _stub_authority(2, "B", "city")
        rows = [
            (a, "6000", "6200"),
            (b, "5500", "5999"),
        ]
        picked = _pick_closest_per_type(rows, "6107")
        assert [x.name for x in picked] == ["A"]

    def test_skips_rows_with_null_bounds(self) -> None:
        a = _stub_authority(1, "A", "city")
        rows = [
            (a, None, None),
        ]
        picked = _pick_closest_per_type(rows, "6107")
        assert picked == []


# ---------------------------------------------------------------------------
# _pick_one_city_county_per_zip5 — no-+4 dominance dedup
# ---------------------------------------------------------------------------
class TestPickOneCityCountyPerZip5:
    """For zip5-only queries, dedup multi-city ZIPs to ONE city per type.

    Real-world hit: NE 68046 had La Vista (type-z + 1 type-4) AND
    Papillion (2013 type-4) AND Omaha (1 type-4) all bound to the same
    ZIP. Returning all three stacked their city taxes and reported
    11.0% combined when the actual rate at any address is ~7.5%.
    """

    def test_most_rows_beats_typez_with_few_rows(self) -> None:
        """Row count for THIS ZIP wins over a stray type-z claim with few rows.

        Originally (v0.34) this test asserted that a type-z record won
        over type-4-only. That semantic was wrong for the GA Roswell
        30075 case: Cobb County had 1 typez + 18 type4 (= 19 rows),
        Fulton County had 0 typez + 107 type4. ZIP 30075 is physically
        in Fulton (per USPS); the Cobb typez was a stray binding. The
        v0.46 reorder makes "most rows for this ZIP" the primary
        tiebreaker, with typez as a secondary signal.

        For the original NE Papillion 68046 case (the v0.34 motivation),
        the rate is unaffected: La Vista, Papillion, and Omaha all
        impose 2.0% city tax, so picking by row count gives the same
        7.5% combined -- but Papillion (the dominant city) is now the
        displayed name instead of La Vista.
        """
        la_vista = _stub_authority(1, "La Vista", "city")
        papillion = _stub_authority(2, "Papillion", "city")
        rows = [
            (la_vista, None),  # type-z (1 record)
            (la_vista, "4252"),
            (papillion, "0600"),
            (papillion, "0619"),
            (papillion, "0709"),  # 3 type-4, no type-z
        ]
        picked = _pick_one_city_county_per_zip5(rows)
        names = [a.name for a in picked if a.authority_type == "city"]
        # Papillion: 3 rows; La Vista: 2 rows. Most rows wins.
        assert names == ["Papillion"]

    def test_ga_roswell_county_tiebreaker(self) -> None:
        """Regression for GA Roswell 30075: Fulton (107 rows) beats Cobb (19 rows).

        Empirically observed during iter-28 spot-check. ZIP 30075 is
        physically in Fulton County, GA (Roswell city limits) per USPS
        attribution. The SST boundary file has:
          - Cobb County:   1 typez + 18 type4 = 19 rows
          - Fulton County: 0 typez + 107 type4 = 107 rows
        Pre-v0.46 the typez-first tiebreaker picked Cobb (state 4 +
        Cobb 2 = 6%) instead of Fulton (state 4 + Fulton 3.75 = 7.75%).
        """
        cobb = _stub_authority(1, "Cobb County", "county")
        fulton = _stub_authority(2, "Fulton County", "county")
        rows: list[tuple[object, str | None]] = []
        rows.append((cobb, None))  # 1 typez
        for i in range(18):
            rows.append((cobb, str(i).zfill(4)))  # 18 type4
        for i in range(107):
            rows.append((fulton, str(1000 + i).zfill(4)))  # 107 type4, no typez
        picked = _pick_one_city_county_per_zip5(rows)
        names = [a.name for a in picked if a.authority_type == "county"]
        assert names == ["Fulton County"]

    def test_most_rows_wins_when_no_typez(self) -> None:
        """Tie-break: city with most boundary rows wins."""
        minneapolis = _stub_authority(1, "Minneapolis", "city")
        st_louis_park = _stub_authority(2, "St. Louis Park", "city")
        rows = [
            (minneapolis, "1000"),
            (minneapolis, "1001"),
            (minneapolis, "1002"),
            (st_louis_park, "9000"),
        ]
        picked = _pick_one_city_county_per_zip5(rows)
        names = [a.name for a in picked if a.authority_type == "city"]
        assert names == ["Minneapolis"]

    def test_single_city_no_typez_passes_through(self) -> None:
        """Minneapolis 55417 case: city only in type-4 records, but the
        only city -- should still be returned."""
        minneapolis = _stub_authority(1, "Minneapolis", "city")
        state = _stub_authority(2, "Minnesota", "state")
        rows = [
            (state, None),
            (minneapolis, "1024"),
        ]
        picked = _pick_one_city_county_per_zip5(rows)
        types = sorted(a.authority_type for a in picked)
        assert types == ["city", "state"]

    def test_districts_pass_through(self) -> None:
        """Districts (transit, etc.) always apply zip-wide -- include all."""
        state = _stub_authority(1, "Minnesota", "state")
        d1 = _stub_authority(2, "Hennepin Transit", "district")
        d2 = _stub_authority(3, "Metro Transportation", "district")
        rows = [
            (state, None),
            (d1, None),
            (d2, None),
        ]
        picked = _pick_one_city_county_per_zip5(rows)
        district_names = sorted(a.name for a in picked if a.authority_type == "district")
        assert district_names == ["Hennepin Transit", "Metro Transportation"]

    def test_typez_districts_all_apply(self) -> None:
        """MN-style metro transit: all districts with type-z records stack.

        Bloomington 55425 has 3 metro districts each with a type-z
        record: Hennepin Transit + Metro Transportation + Metro Housing.
        All three correctly apply to the entire ZIP.
        """
        state = _stub_authority(1, "Minnesota", "state")
        d1 = _stub_authority(2, "Hennepin Transit", "district")
        d2 = _stub_authority(3, "Metro Transportation", "district")
        d3 = _stub_authority(4, "Metro Housing", "district")
        rows = [(state, None), (d1, None), (d2, None), (d3, None)]
        picked = _pick_one_city_county_per_zip5(rows)
        district_names = sorted(a.name for a in picked if a.authority_type == "district")
        assert district_names == ["Hennepin Transit", "Metro Housing", "Metro Transportation"]

    def test_lone_type4_only_district_included(self) -> None:
        """A single type-4-only district treated as county-wide; included.

        Regression for GA Roswell 30075: Fulton County TSPLOST
        (the only district binding to ZIP 30075) has 107 type-4
        records and 0 type-z. Pre-v0.47 it was dropped because of
        the "type-4-only districts are CIDs" heuristic, which made
        the engine return 7.0% (state 4 + Fulton 3) instead of the
        correct 7.75% (with TSPLOST 0.75% added).

        The heuristic was too aggressive: CID stacking only applies
        when MULTIPLE type-4-only districts compete for the same
        ZIP. A single one is almost certainly a county-wide overlay
        whose SST encoding happens to use per-+4 records.
        """
        state = _stub_authority(1, "Georgia", "state")
        county = _stub_authority(2, "Fulton County", "county")
        tsplost = _stub_authority(3, "Fulton County TSPLOST", "district")
        rows: list[tuple[object, str | None]] = [(state, None), (county, None)]
        # 107 type-4 records all pointing at the same TSPLOST authority.
        for i in range(107):
            rows.append((tsplost, str(i).zfill(4)))
        picked = _pick_one_city_county_per_zip5(rows)
        district_names = sorted(a.name for a in picked if a.authority_type == "district")
        assert district_names == ["Fulton County TSPLOST"]

    def test_type4_only_districts_dropped(self) -> None:
        """KS Olathe: 4 CIDs with only type-4 records -- drop all of them.

        Pre-fix, KS 66061 returned 13.475% because 4 KS-district-209xx
        CIDs (Community Improvement Districts) summed at ~1% each on top
        of the legitimate state + county + city. CIDs are address-
        specific; without ZIP+4, no single district can be authoritatively
        chosen, so dropping all is safer than picking arbitrarily.
        """
        state = _stub_authority(1, "Kansas", "state")
        county = _stub_authority(2, "Johnson County", "county")
        city = _stub_authority(3, "Olathe", "city")
        cid1 = _stub_authority(10, "KS-district-20910", "district")
        cid2 = _stub_authority(11, "KS-district-21059", "district")
        cid3 = _stub_authority(12, "KS-district-20917", "district")
        rows = [
            (state, None),
            (county, None),
            (city, "2917"),
            (cid1, "1000"),
            (cid1, "1001"),
            (cid2, "5000"),
            (cid3, "9000"),
        ]
        picked = _pick_one_city_county_per_zip5(rows)
        types = sorted(a.authority_type for a in picked)
        # Should be: state + county + city -- NO districts (all were type-4 only)
        assert types == ["city", "county", "state"]

    def test_mix_typez_and_type4_districts(self) -> None:
        """TN-style: 1 type-z district stays; 3 type-4-only ones drop.

        TN 37027 (Brentwood) had 1 Williamson IMPROVE Act with type-z
        plus 3 other-county IMPROVE Acts with only type-4 records.
        Only the legitimate Williamson one should remain.
        """
        state = _stub_authority(1, "Tennessee", "state")
        d_typez = _stub_authority(2, "TN-district-91950", "district")
        d_t4_a = _stub_authority(3, "Other IMPROVE Act A", "district")
        d_t4_b = _stub_authority(4, "Other IMPROVE Act B", "district")
        rows = [
            (state, None),
            (d_typez, None),
            (d_typez, "1234"),
            (d_t4_a, "1000"),
            (d_t4_b, "2000"),
        ]
        picked = _pick_one_city_county_per_zip5(rows)
        district_names = sorted(a.name for a in picked if a.authority_type == "district")
        assert district_names == ["TN-district-91950"]

    def test_fewer_total_zips_wins_when_both_curated(self) -> None:
        """Tie on every other signal -> the city covering fewer ZIPs wins.

        Regression for Winooski 05404: the SST 'A'-record loader binds
        ZIP 05404 to BOTH city 85150 ("Winooski", covers only 05404) and
        city 14875 ("Colchester", covers a wider Chittenden County
        cluster). Both are curated friendly names, both have row_count=1
        for 05404, both are zip-wide ('A'-collapse). Without this
        tiebreaker the lower-id authority (Colchester) wins arbitrarily;
        the more-specific city (Winooski, 1 total ZIP) is the right
        answer for a ZIP that physically lives in Winooski.
        """
        vt_state = SimpleNamespace(abbrev="VT")
        # Lower id; covers many ZIPs.
        colchester = _stub_authority(1, "Colchester", "city")
        colchester.state = vt_state
        # Higher id but covers ONLY 05404.
        winooski = _stub_authority(2, "Winooski", "city")
        winooski.state = vt_state
        rows = [(colchester, None), (winooski, None)]
        # Colchester covers 12 ZIPs total; Winooski covers 1.
        total_zip_counts = {colchester.id: 12, winooski.id: 1}
        picked = _pick_one_city_county_per_zip5(rows, total_zip_counts=total_zip_counts)
        names = [a.name for a in picked if a.authority_type == "city"]
        assert names == ["Winooski"], (
            f"expected ['Winooski']; got {names} (more-specific city should "
            "have won the tiebreaker)"
        )

    def test_curated_name_wins_over_placeholder(self) -> None:
        """When two cities tie on every other signal, prefer the vetted name.

        Regression for VT 05401 (Burlington): the SST 'A'-record loader
        binds the ZIP to BOTH city ``10675`` (= "Burlington") and the
        regional code ``66175`` (placeholder ``VT-city-66175``). Both are
        type-z (zip-wide via the 'A'-collapse) and have the same row count
        after dedup. Without this tiebreaker the lower authority id wins
        arbitrarily, causing the API response to display the placeholder
        instead of "Burlington" -- the rate is correct but the city name
        is unhelpful. Curated names indicate a maintainer-vetted code.
        """
        vt_state = SimpleNamespace(abbrev="VT")
        # Lower id but placeholder name -- would win without the new
        # tiebreaker.
        regional = _stub_authority(1, "VT-city-66175", "city")
        regional.state = vt_state
        burlington = _stub_authority(2, "Burlington", "city")
        burlington.state = vt_state
        rows = [
            (regional, None),  # 'A'-collapse: zip4_low None (type-z proxy)
            (burlington, None),
        ]
        picked = _pick_one_city_county_per_zip5(rows)
        names = [a.name for a in picked if a.authority_type == "city"]
        assert names == ["Burlington"], (
            f"expected ['Burlington']; got {names} (placeholder beat the "
            "curated name -- tiebreaker regression)"
        )

    def test_tn_city_drops_county(self) -> None:
        """TN's city codes already include the county rate; drop county."""
        tn_state_attr = SimpleNamespace(abbrev="TN")
        county = _stub_authority(1, "Williamson County", "county")
        county.state = tn_state_attr
        city = _stub_authority(2, "Brentwood", "city")
        city.state = tn_state_attr
        rows = [(county, "1234"), (city, "1234")]
        picked = _pick_one_city_county_per_zip5(rows)
        types = sorted(a.authority_type for a in picked)
        assert types == ["city"]
        assert picked[0].name == "Brentwood"

    def test_wa_city_drops_county(self) -> None:
        """WA's city codes are combined-local (include county+transit)."""
        wa_state_attr = SimpleNamespace(abbrev="WA")
        county = _stub_authority(1, "King County", "county")
        county.state = wa_state_attr
        city = _stub_authority(2, "Bellevue (combined local)", "city")
        city.state = wa_state_attr
        rows = [(county, "3504"), (city, "3504")]
        picked = _pick_one_city_county_per_zip5(rows)
        types = sorted(a.authority_type for a in picked)
        assert types == ["city"]

    def test_ok_city_keeps_county(self) -> None:
        """OK genuinely separates city + county taxes -- both must apply.

        Norman 73069: state 4.5 + Cleveland County 0.125 + Norman city
        4.125 = 8.75%. Dropping the county would under-collect.
        """
        ok_state_attr = SimpleNamespace(abbrev="OK")
        county = _stub_authority(1, "Cleveland County", "county")
        county.state = ok_state_attr
        city = _stub_authority(2, "Norman", "city")
        city.state = ok_state_attr
        rows = [(county, "6107"), (city, "6107")]
        picked = _pick_one_city_county_per_zip5(rows)
        types = sorted(a.authority_type for a in picked)
        assert types == ["city", "county"]

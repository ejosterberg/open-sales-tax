# Alaska: Ward Cove over-collects 3.00pp; six ARSSTC ZIPs return 0.000%

**Found:** 2026-08-01 (daily state audit, day 1 — AK + AL)
**Status:** ✅ **FIXED IN REPO 2026-08-01** — prod reload still pending
(see "Resolution" at the bottom)
**Source:** ARSSTC "Sales Tax Rate Sheet with Zip Codes 7-1-2026"
(`arsstc.org/wp-content/uploads/2026/07/ARRSTC-Sales-Tax-Rate-Sheet-with-Zip-Codes-7-1-2026.xlsx`)
— the current published sheet, downloaded and diffed row-by-row against
the live engine.

## Method

Alaska has no state sales tax; every rate is borough and/or city, and
ARSSTC publishes the authoritative per-ZIP table monthly. The sheet
carries an `inoutcity` flag: `I` rows are the rate **inside** the named
city's limits, `O` rows the rate **outside** them (borough-only). For a
bare ZIP5 the engine must return one number, so a result is counted
correct if it matches **either** bracket.

**Result across all 84 ARSSTC ZIPs: 73 exact match, 4 defensibly between
the I/O bracket, 1 over-collect, 6 under-collect.**

All 18 AK rows pinned in `tests/integration/test_sst_dor_validation.py`
match the live engine exactly — the tier-1 cities are fine. Everything
below is outside the pinned set.

> Note for future audits: the sheet's `inoutcity` column contains
> `'I '` **with a trailing space** on some rows. Strip before comparing
> or inside-city rows silently bucket as outside-city.

## Finding 1 — ZIP 99928 (Ward Cove) over-collects by 3.00pp

| | |
|---|---|
| ARSSTC row | `99928, AK, KETCHIKAN GATEWAY, 9038, WARD COVE, (no city code), rate 2.5` |
| Correct rate | **2.500%** — Ketchikan Gateway Borough only |
| Live engine | **5.500%**, jurisdictions `Alaska 0.0; Ketchikan 5.5` |
| **Error** | **over-collects 3.00pp** |

Two things are wrong, not one:

1. The engine applies the **City of Ketchikan's 5.5% city tax** to a ZIP
   that is not in Ketchikan city. Ward Cove is an unincorporated
   community in Ketchikan Gateway Borough, several miles north of the
   city. ARSSTC gives it no city filing code at all — the tell that it
   levies no city tax.
2. The engine simultaneously **drops the 2.5% borough tax** that Ward
   Cove genuinely owes. So it is not "the right components at the wrong
   total" — both components are wrong.

Compare the correctly-modelled neighbour: `99901` returns
`Ketchikan Gateway Borough 2.5 + Ketchikan 5.5 = 8.000%`, matching
ARSSTC's inside-city row. 99928 gets the city without the borough.

Over-collection is the failure mode a consumer notices as a real
overcharge, which makes this the highest-priority item in this finding.

## Finding 2 — six ARSSTC ZIPs return 0.000% with no jurisdictions

Each of these has a published ARSSTC rate but the engine returns a bare
`Alaska 0.000%` and nothing else:

| ZIP | ARSSTC city | Inside | Outside | Engine | Under-collects by |
|---|---|---:|---:|---:|---:|
| 99903 | Ketchikan | 8.0 | 2.5 | 0.000 | ≥ 2.50pp |
| 99918 | Ketchikan | 8.0 | 2.5 | 0.000 | ≥ 2.50pp |
| 99950 | Ketchikan | 8.0 | 2.5 | 0.000 | ≥ 2.50pp |
| 99824 | Juneau | — | 5.0 | 0.000 | 5.00pp |
| 99836 | (Sitka area) | 6.0 | — | 0.000 | 6.00pp |
| 99850 | Excursion Inlet | 4.5 | — | 0.000 | 4.50pp |

99903 / 99918 / 99950 are Ketchikan Gateway Borough ZIPs — the borough
levies 2.5% everywhere in it, so **2.5% is the floor regardless of city
limits**; returning 0% cannot be right under either bracket. 99824 is
Douglas, inside the consolidated City and Borough of Juneau (5.0%).

This looks like missing boundary rows rather than a wrong rate: the
borough authorities exist and are correctly rated for other ZIPs
(`99901` → Ketchikan Gateway Borough 2.5), they are just not bound to
these ZIPs.

## Not findings (recorded so a later audit doesn't re-derive them)

Four ZIPs land **between** the ARSSTC inside/outside bracket. Each
straddles two taxing bodies, so a single ZIP5 answer is inherently a
choice, and the engine's pick is defensible:

| ZIP | Engine | Bracket | Note |
|---|---|---|---|
| 99637 | Toksook Bay 2.0 | 0.0 – 6.0 | distinct city sharing the Bethel ZIP |
| 99645 | Palmer 3.0 | 0.0 – 4.0 | Palmer city vs. MatSu (no borough tax) |
| 99827 | Haines 5.5 | 4.5 – 7.0 | Haines Borough seasonal schedule |
| 99919 | Thorne Bay 6.0 | 2.5 – 8.0 | Thorne Bay and Ketchikan Gateway share it |

Also confirmed clean:

- **No August-2026 Alaska change.** The newest ARSSTC sheet is 7-1-2026;
  there is no 8-1-2026 publication, so nothing took effect today.
- All 18 pinned AK rows match live (Homer 7.85, Juneau 5.0, Ketchikan
  8.0, Sitka 6.0, Wasilla 2.5, Kodiak 7.0, Seward 7.0, Bethel 6.0, Nome
  6.0, Seldovia 9.5 peak, North Pole 5.5, Petersburg 6.0, Wrangell 7.0,
  Soldotna 6.0, Kenai 6.0, and the three KPB-unincorporated fallbacks).

## Recommended action

1. **99928 first** — remove the Ketchikan city binding for that ZIP and
   bind Ketchikan Gateway Borough. Before doing so, find out *why* a
   city binding exists for a ZIP with no ARSSTC city code; if the AK
   boundary builder infers city membership from a shared borough or a
   name match, the same inference may be mis-binding other ZIPs and the
   builder is the thing to fix, not this row.
2. Add borough-floor boundary rows for the six 0.000% ZIPs.
3. Add the seven affected ZIPs to the AK live-API grid so the next audit
   catches regressions automatically.

Per root-cause discipline: item 1 is deliberately phrased as
"investigate the builder, then fix" — hand-pinning 99928 alone would
make the symptom vanish without establishing whether the mis-binding
rule is general.

## Reproduction

```bash
curl -s -H 'User-Agent: Mozilla/5.0' \
  'https://api.opensalestax.org/v1/rates?zip5=99928'
# -> 5.500%  Alaska 0.0; Ketchikan 5.5     (ARSSTC: 2.5, borough only)
```

---

## Resolution (2026-08-01, same day)

### Root cause — not what this finding first hypothesized

The finding speculated the AK boundary builder was *inferring* city
membership. It was not. **99928 was hand-listed as a Ketchikan city ZIP**
in `AK_CITIES["Ketchikan"]`:

```python
frozenset({"99901", "99928"})   # <- 99928 does not belong here
```

Two independent faults compounded:

1. **The wrong city binding.** Ward Cove is unincorporated Ketchikan
   Gateway Borough territory; ARSSTC assigns it no city filing code, so
   it owes no city tax.
2. **No borough binding was reachable.** The borough pass is driven by
   Census `ZIP_COUNTY`, and **99928 is absent from `ZIP_COUNTY`
   entirely** — so the 2.5% borough tax could never be applied.

Together those produced 5.500% (city only) where 2.500% (borough only)
was correct. The same `ZIP_COUNTY` gap explains 99950; 99903 and 99918
are present but Census assigns them to Wrangell and Prince of
Wales-Hyder, neither of which levies a borough tax, while ARSSTC bills
all four as Ketchikan Gateway.

### The general fix

Census is authoritative for **where a ZIP is**; ARSSTC is authoritative
for **who taxes it**. For Alaska, where they disagree, ARSSTC wins. New
`AK_BOROUGH_ZIPS` in `ak_data.py` carries the ARSSTC-attested borough
bindings and is overlaid on the Census-derived map in
`alaska.py::parse_boundaries`, so the borough pass no longer depends on
Census geography being complete or in agreement.

### Changes

| ZIP | Before | After | Change |
|---|---|---|---|
| 99928 Ward Cove | 5.500% (Ketchikan city) | **2.500%** (KGB only) | removed from `AK_CITIES["Ketchikan"]`, added to `AK_BOROUGH_ZIPS` |
| 99903 | 0.000% | **8.000%** | added to Ketchikan city ZIPs + `AK_BOROUGH_ZIPS` |
| 99918 | 0.000% | **8.000%** | ditto |
| 99950 | 0.000% | **8.000%** | ditto |
| 99824 Douglas | 0.000% | **5.000%** | added to `AK_CITIES["Juneau"]` |
| 99836 | 0.000% | **6.000%** | added to `AK_CITIES["Sitka"]` |
| 99850 Excursion Inlet | 0.000% | **4.500%** | new `AK_CITIES` entry |

Verified against the module's own `parse_rates`/`parse_boundaries`
output: all seven now match ARSSTC, and the previously-correct
neighbours (99901 8.0, 99801 5.0, 99835 6.0) are unchanged — no
regression.

The four "between the bracket" ZIPs (99637, 99645, 99827, 99919) were
deliberately left alone, as the finding recommended.

### Tests

Seven new rows added to the AK DOR grid in
`tests/integration/test_sst_dor_validation.py`. They fail under
`-m liveapi` until prod reloads AK, matching the HI-Maui / IA-WDM
precedent. AK unit tests pass (`len(city_rows) == len(AK_CITIES)` still
holds with the new Excursion Inlet entry).

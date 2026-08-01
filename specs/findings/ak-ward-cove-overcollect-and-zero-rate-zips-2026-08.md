# Alaska: Ward Cove over-collects 3.00pp; six ARSSTC ZIPs return 0.000%

**Found:** 2026-08-01 (daily state audit, day 1 — AK + AL)
**Status:** OPEN — chipped for review
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

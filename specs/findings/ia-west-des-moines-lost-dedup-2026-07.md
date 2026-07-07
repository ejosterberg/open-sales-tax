# Finding — IA West Des Moines LOST dedup over-collect (2026-07)

**Status:** OPEN — confirmed on the live engine 2026-07-07 during the daily
IA+ID audit. Pre-existing (first logged iter-128); this is the first
dedicated finding file + chip.

**Severity:** Real customer-facing **over-collection of 2–3%** on West Des
Moines, Iowa transactions. Iowa's Local Option Sales Tax is statutorily
capped at **1%** (Iowa Code ch. 423B), so the correct combined rate for any
Iowa address is at most **7.0%** (state 6% + one 1% LOST). The engine
returns 9–10% for the West Des Moines cross-county ZIPs.

## Symptom (live engine, 2026-07-07)

| ZIP | Engine jurisdictions | Combined | Correct |
|-----|----------------------|----------|---------|
| 50265 | Iowa 6% + **Polk Co LOST 1%** + **Union Co LOST 1%** + **IA-district-98199 1%** | **9.0%** | 7.0% |
| 50266 | Iowa 6% + **IA-district-98049 1%** + **Polk Co LOST 1%** + **Union Co LOST 1%** + **IA-district-98199 1%** | **10.0%** | 7.0% |

West Des Moines straddles Polk and Dallas counties (with a sliver in Warren).
Both counties impose the 1% LOST, so a single 1% LOST correctly applies →
7.0%. The engine instead emits and **sums** several 1% LOST authorities for
the same ZIP.

## Why the extra districts are wrong

- **Union County LOST** is unambiguously wrong. Union County is rural
  south-central Iowa (county seat Creston); it has no geographic relationship
  to West Des Moines. Its authority is leaking onto these ZIPs.
- **IA-district-98199** and **IA-district-98049** are synthetic IA SST
  district codes that are stacking on top of the county-named LOST authority
  for the same locality. Only one 1% LOST should survive per ZIP.

This is the same class of bug as the TN IMPROVE Act same-ZIP district
stacking (handoff iter-148) and is explicitly the "IA West Des Moines LOST
dedup bug" noted in `specs/handoff.md` (iter-128 open follow-up).

## Root cause (hypothesis)

The SST boundary file binds West Des Moines ZIPs to multiple 1% LOST
authorities (the Polk-side county authority, the Dallas-side authority via
district code, plus a stray Union County binding). The lookup engine's
LOST handling lacks a per-state cap/dedup rule that recognizes Iowa's
"at most one 1% LOST applies" invariant and collapses the competing 1%
LOST districts to a single authority.

## Fix direction (needs engine work — NOT a data/pin edit)

1. Add Iowa-specific LOST dedup in the lookup engine (mirror the v0.44 TN
   IMPROVE Act cross-county dedup pattern): when multiple 1% LOST-class
   districts bind the same ZIP, keep exactly one (the one whose parent
   county actually contains the ZIP centroid) and drop the rest.
2. The stray **Union County** binding suggests a boundary-file cross-county
   leak similar to the MN/SD area-majority fix (iter-165..168) — verify the
   ZCTA canonical-state/county resolution for 50265/50266 anchors West Des
   Moines to Polk/Dallas, not Union.
3. Do **not** mask this by editing the failing grid pin
   `("IA","West Des Moines","50265","0001","7.000")` in
   `tests/integration/test_sst_dor_validation.py`. That pin encodes the
   correct expected 7.0% and currently (correctly) fails under `-m liveapi`
   at 9.0%. Fix the engine so the pin xpasses.

## Verification once fixed

```bash
# both should return 7.000%:
curl -s -A "<browser-UA>" https://api.opensalestax.org/v1/calculate \
  -H 'Content-Type: application/json' \
  -d '{"address":{"zip5":"50265"},"line_items":[{"amount":"100.00"}]}'
curl -s -A "<browser-UA>" https://api.opensalestax.org/v1/calculate \
  -H 'Content-Type: application/json' \
  -d '{"address":{"zip5":"50266"},"line_items":[{"amount":"100.00"}]}'
# regression pin:
pytest -m liveapi tests/integration/test_sst_dor_validation.py -k "West_Des_Moines or 50265"
```

## References
- `specs/audits/2026/07/state-audit-2026-07-07.md`
- `specs/handoff.md` — iter-128 "IA West Des Moines LOST dedup bug" open item
- Iowa Code ch. 423B (LOST, 1% cap)

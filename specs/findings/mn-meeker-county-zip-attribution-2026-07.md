# MN — Meeker County rural-ZIP cross-county attribution (2026-07)

**Status:** OPEN — investigation. **Likely resolved by two already-actioned
items** (MN Q3 2026 SST reload + the pending iter-220/221 MN district-name
reload). **Do NOT ship an engine/loader change until re-verified AFTER those
reloads** — the misattribution may disappear entirely once Meeker County's new
transit authority binds and the corrected friendly names apply.

Surfaced by the daily state-tax audit 2026-07-12 (MI + MN pair).

## Symptom

Several **Meeker County** ZIPs resolve on the live engine
([api.opensalestax.org](https://api.opensalestax.org/v1/rates)) to
**neighboring counties** — Meeker County never appears in their jurisdiction
stack:

| ZIP | City (actual county) | Engine returns | Engine combined | Published (2025, pre-July-2026) |
|-----|----------------------|----------------|-----------------|----------------------------------|
| 55355 | Litchfield (Meeker) | state + **McLeod County** 0.5% + city 0.5% | 7.875% | 7.375% (state + city 0.5%) |
| 55325 | Dassel (Meeker) | state + **McLeod County** 0.5% | 7.375% | 6.875% (state only) |
| 55329 | Grove City (Meeker) | state + **Stearns County** 0.25% + **Anoka County Transportation** 0.375% | 7.500% | 6.875% (state only) |

Sources for the "published" column: [SalesTaxHandbook — Litchfield
7.375%](https://www.salestaxhandbook.com/minnesota/rates/litchfield),
[sales-taxes.com](https://www.sales-taxes.com/mn/litchfield). Litchfield is
unambiguously the Meeker County seat; Dassel and Grove City are also Meeker.

## What the DB shows (prod, MN SST Q2 2026 = `MNR2026Q2FEB18`)

Joining `boundaries → tax_authorities → data_versions` for these ZIPs:

- **55325 (Dassel):** bound to `McLeod County` **and** `Wright County` (both
  `source=sst`). No `Meeker County` row exists.
- **55329 (Grove City):** ~40 `Stearns County` county rows + several
  `Anoka County Transportation Sales Tax` district rows (all `source=sst`). No
  `Meeker County` row.

So the currently-loaded SST Q2 boundary file binds these Meeker ZIPs to
**adjacent counties' authorities**, and Meeker County itself is absent from the
boundary set.

## Root-cause hypothesis (two compounding factors)

1. **Meeker County had no general county sales tax before 2026-07-01.** With no
   Meeker authority to bind, the rural ZCTA polygons — which physically spill
   across the McLeod / Wright / Stearns county lines — get attributed to
   whichever neighboring county's authority the SST boundary file lists for that
   ZIP+4 range. This is the same cross-county-straddle family as the CA ZCTA
   fixes and the MN/SD border fix (handoff iter-165..168).

2. **`Anoka County Transportation Sales Tax` on 55329 is a stale friendly
   name.** Grove City is ~65 mi from Anoka County; the label is almost certainly
   a mislabeled district code from the **pre-iter-220** name table. iter-220
   (`d9dfada`) re-derived `MN_DISTRICT_NAMES` from the MN DOR "Tax Type Codes"
   xlsx and corrected exactly this class of mislabeling, but those corrections
   **have not been reloaded to prod** (handoff "What to start on next", open
   item #1).

## Why this is probably self-resolving

Effective **2026-07-01**, Meeker County adopts a **0.5% Transit Sales and Use
Tax** (a *general* local sales/use tax under Minn. Stat. 297A.993; SST district
code **80054**, friendly name already curated in
[`mn_names.py:102`](../../src/opensalestax/states/mn_names.py)). This is in the
**MN Q3 2026** SST files (`MNR2026Q3MAY20` / `MNB2026Q3MAY20`), which prod does
**not** yet have.

Once the MN Q3 files are loaded:
- Meeker County's transit authority should bind to these Meeker ZIPs, giving the
  engine a *correct* Meeker jurisdiction to attribute.
- The corrected iter-220 friendly names (if reloaded in the same pass) replace
  the stale `Anoka County Transportation` label.

Note the coincidence that makes today's totals *look* mostly fine: post-July-1
the correct Litchfield rate is state + Meeker transit 0.5% + city 0.5% =
**7.875%** — the same total the engine already returns for 55355, but via the
wrong jurisdiction (McLeod). Dassel post-July-1 is 7.375% (matches today's total
by coincidence, wrong label). Grove City post-July-1 is 7.375% vs today's 7.500%
(engine over by 0.125%, and wholly wrong jurisdictions).

## Next steps (in order)

1. **Chip filed:** refresh MN SST to `MNR2026Q3MAY20` / `MNB2026Q3MAY20`
   (combine with the pending iter-220/221 MN/IA/NC name reload — do them in one
   pass so both the new Meeker authority and the corrected names land together).
2. **After the reload, re-probe** 55355 / 55325 / 55329 and confirm:
   - Meeker County (transit) now appears in the stack for these ZIPs.
   - The spurious `McLeod County` / `Stearns County` / `Anoka County
     Transportation` attributions are gone.
   - Combined rates: Litchfield 7.875%, Dassel 7.375%, Grove City 7.375%.
3. **Only if the misattribution persists post-reload** does this become a genuine
   ZCTA area-majority / loader bug worth an engine change. In that case, follow
   the pattern in `scripts/audit_district_code_bindings.py` and the
   `_filter_to_canonical_state` / area-majority logic in `core/lookup.py`.

Do **not** mask this by editing test pins to the wrong jurisdiction — fix the
data (reload) first, then re-verify.

# PR back-to-school IVU-free days 2026-27 announced; module says "not yet confirmed"

**Found:** 2026-11-20 daily audit (day 20: PA + PR).
**Status:** Open. Chipped for human review. No code changed.
**Severity:** Medium and time-bound. One window has already passed. The next is
**Friday 2027-01-08 to Saturday 2027-01-09**.

## Summary

`src/opensalestax/states/puerto_rico.py` still says the 2026 back-to-school
IVU holiday is "NOT YET CONFIRMED". `holidays_for(year)` returns nothing, and
`tests/unit/test_state_puerto_rico.py` pins "no holiday" for every year from
2024 to 2030. The 2026-11-01 audit also reported "no 2026 holiday announced".
That was wrong: Hacienda had already announced it in June/July 2026.

## Primary sources

All of these are on hacienda.pr.gov and were read on 2026-11-20.

- **Carta Circular de Rentas Internas CC RI 26-11**, dated 2026-06-02:
  `https://hacienda.pr.gov/publicaciones/carta-circular-de-rentas-internas-num-26-11-cc-ri-26-11`
  - First period: Friday 17 July 2026 to Saturday 18 July 2026 (passed).
  - Second period: Friday 8 January 2027 to Saturday 9 January 2027 (upcoming).
  - Scope: school uniforms and school materials only, under Code Sección
    4030.20(b). Printed books and e-books are exempt all year under 4030.20(a).
- Press release dated 2026-07-09:
  `https://hacienda.pr.gov/sobre-hacienda/sala-de-prensa-virtual/comunicados-de-prensa/departamento-de-hacienda-anuncia-dias-exentos-del-pago-de-ivu-en-la-compra-de-uniformes-y-materiales-para-el-ano-escolar-2026-2027`

**Not yet verified:** the CC RI 26-11 PDF itself. The dates above come from the
publication page. Before encoding them, read the PDF for the exact item
definitions, any per-item price caps, and whether both the state and municipal
parts of the IVU are waived.

## Why this is not a one-line fix

- The holiday covers school uniforms and school supplies, not all clothing.
  The engine's `clothing` category is broader. Encoding the window against
  `clothing` would under-collect on ordinary clothing for those two days.
  Encoding it needs either a narrower category or a documented decision.
- The 2024–2030 "no holiday" regression test has to be relaxed for 2026 and
  2027. The holidays are enacted one year at a time, so 2028 onward should stay
  pinned as "no holiday".
- The windows fall in two calendar years: July 2026 and January 2027.

## Recommended action

1. Read the CC RI 26-11 PDF.
2. Add `HolidayWindow`s for 2026-07-17..18 and 2027-01-08..09, using the
   narrowest correct categories.
3. Update the docstring and the regression test.
4. Ship before **2027-01-08**.

## Related, not drift

The 2026-07-02 press release says that from July/August 2026, 73 municipios
file the municipal IVU through SURI (Ley 72-2025; CC RI 26-13). Bayamón,
Carolina, Guaynabo, Mayagüez and San Juan keep their own processes. The
calendar is unchanged and CC RI 26-13 confirms the 1% municipal IVU.
**The rate is unchanged.** This affects filing only, not calculation.

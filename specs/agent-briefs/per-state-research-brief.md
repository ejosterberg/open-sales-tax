# Per-State Research + Implementation Brief

> **Read this first** if you've been assigned a single US state to
> bring up to **tier 1**. This is the canonical brief; spawning
> agents should be given this document as their primary instruction.

## Your goal

Deliver a single state's tier-1 module:

- A `src/opensalestax/states/<state_name>.py` module that
  implements the :class:`StateModule` Protocol with full
  taxability matrix, statewide rate, and any sales-tax holidays
- A `tests/unit/test_state_<abbrev_lower>.py` covering the
  module
- Updates to `src/opensalestax/states/__init__.py` (import the
  module so it self-registers)
- Updates to `src/opensalestax/states/catalog.py` if your state's
  metadata changes (rare; usually just `notes`)
- Update to the `/v1/states` integration test if your state moves
  from tier 0 → tier 1
- Update `MAINTAINERS.md` (add your name as the state maintainer
  if you want)
- A short PR description summarizing what changed + what you
  verified against external sources

## Read these first (5 minutes; mandatory)

1. `specs/constitution.md` — non-negotiable principles
2. `specs/current-state.md` — what's done across all states
3. `specs/decisions/01-language-framework.md` through `03-database.md`
4. `specs/research/references.md` — consolidated external sources
   already used (the "what we already know" doc)
5. **Two existing tier-1 examples** — pick whichever pattern matches
   your state:
   - `src/opensalestax/states/california.py` if your state is
     **non-SST** (most non-SST states use the `self_seeded`
     pattern)
   - `src/opensalestax/states/minnesota.py` if your state is
     **SST** (uses the SstStateModule pattern)
   - `src/opensalestax/states/florida.py` if your state has
     **annual sales-tax holidays** (TX/FL/MA/MD all do)

## Step 1 — Determine the state's "shape"

| Question | Where to look |
|---|---|
| Is it an SST member? | `specs/research/state-coverage.md` (table) + cross-check the SST member list at https://www.streamlinedsalestax.org |
| What is the statewide base rate, and when did it take effect? | The state's Department of Revenue (DOR) website. Sovos summary at `specs/research/sovos-state-summary.md` is a good starting point but ALWAYS verify against the state DOR. |
| Does the state have local jurisdictions that add their own rates? Counties? Cities? Special districts? Parishes (LA)? | DOR site. Note the topology -- some states are state-only (MD), some have city + county (TX), some have parishes (LA), some have home-rule cities that self-administer (CO). |
| Does the state use a tax model OTHER than sales tax? | HI = General Excise Tax (GET); NM = Gross Receipts Tax (GRT); AZ = Transaction Privilege Tax (TPT). Document the model in the module's docstring. |
| Does the state have annual sales-tax holidays? | DOR site + cross-check Sovos summary. If yes, you'll implement `holidays_for(year)` like FL/TX/MA/MD do. |
| Does the state have item-amount thresholds? (e.g., NY clothing under $110, MA clothing under $175) | DOR site. v0.6 will add a threshold-rule feature; for now, document the threshold in your TaxabilityRule's `notes` field. |
| Does the state tax models require special handling? | E.g., AZ TPT is technically imposed on the seller not the buyer (same math, different legal liability). Document in the docstring. |

## Step 2 — Build the taxability matrix

Use these 6 categories as the baseline (the loader prepopulates them):

- `general` — usually taxable
- `clothing` — varies wildly: PA non-taxable, MN non-taxable, NY threshold, MA threshold, most others taxable
- `groceries` — usually non-taxable; IL is a famous exception (1% reduced rate)
- `prescription_drugs` — almost always non-taxable
- `prepared_food` — almost always taxable
- `digital_goods` — varies; check state-specific legislation (CA's AB 147, MD's HB 932)

For each category, your `TaxabilityRule` should:
- Set `is_taxable` boolean correctly
- Cite the **statute** in the `notes` field (e.g., "Cal. Rev. &
  Tax Code section 6359"). **Statutory citations are
  mandatory** -- they're how a future maintainer verifies the
  rule is still correct after legislation changes.
- For threshold-rule states (NY, MA), set `is_taxable=True` by
  default and document the threshold in notes (the v0.6
  threshold feature will read this later)
- For reduced-rate states (IL groceries), set
  `rate_modifier=Decimal("1.000")` and document the caveat

## Step 3 — Implement the module

For **non-SST states** (CA pattern):

```python
# src/opensalestax/states/<state_name>.py
class <StateName>:
    state_abbrev = "XX"
    state_name = "Full Name"
    sst_member = False
    has_sales_tax = True
    tier = 1
    self_seeded = True  # signals loader to skip the cache file

    def parse_rates(self, source_file, version_label):
        del source_file, version_label
        yield RateRow(
            authority_name="Full Name",
            authority_type="state",
            rate_pct=Decimal("X.XXX"),
            effective_from=dt.date(YYYY, M, D),
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(self, source_file, version_label):
        del source_file, version_label
        return iter(())  # boundaries deferred to a later phase

    def taxability_for(self, item_category, effective_date):
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self):
        return iter(())

    def holidays_for(self, year):
        if year != 2026:
            return iter(())  # add 2027+ when published
        return iter([
            HolidayWindow(...),
            ...
        ])
```

For **SST states being promoted from tier 2 → tier 1**:

```python
class <StateName>(SstStateModule):
    state_abbrev = "XX"
    state_name = "Full Name"
    state_fips = "NN"
    tier = 1  # override tier 2 default
    taxability = _TAXABILITY  # override default matrix

    # Override holidays_for if your state has them
    def holidays_for(self, year):
        if year != 2026:
            return iter(())
        return iter([HolidayWindow(...), ...])
```

Then **remove the entry from `_tier2.py`** to avoid double-registration.

## Step 4 — Tests

Required (mirror what `test_state_california.py` and
`test_state_minnesota.py` do):

- Metadata test (abbrev, name, sst_member, has_sales_tax, tier,
  self_seeded if applicable)
- Protocol satisfaction test (`isinstance(instance, StateModule)`)
- Registration test (`get_state_module("XX") is not None`)
- 6 parametrized taxability tests (one per category)
- `parse_rates` test verifying the statewide rate
- If holidays: per-holiday data tests + chronological-order test
- Any state-specific quirks worth a dedicated test (e.g., AZ's
  TPT note, PA's clothing exemption, IL's rate_modifier marker)

Aim for 8-15 tests. Match the style of `test_state_california.py`.

## Step 5 — Document references

Every external source you used **must** be added to
`specs/research/references.md` with:

- The state's section header
- Each URL accessed and the date you accessed it
- The version of the data captured (e.g., "MN DOR rate page,
  retrieved 2026-05-03, statewide rate verified at 6.875%")

This is non-negotiable; future maintainers need to be able to
re-verify your work.

## Step 6 — Verify before submitting

- `poetry run ruff check && poetry run ruff format --check` clean
- `poetry run mypy src/` clean
- `poetry run pytest -q` -- new tests pass; existing 310+ still pass
- SonarQube scan stays at 0 bugs / 0 vulns / 0 smells (run
  per `~/.claude/sonarqube-playbook.md`)
- DCO sign-off on every commit (`git commit -s`)
- One squash-merge or focused commit per state ("feat(states):
  add <full state name> tier-1 module")
- The `/v1/states` integration test is updated if your state
  moves out of tier 0 (see `tests/integration/test_api.py`
  parametrized lists)

## Constraints that apply EVERY state

These come from the constitution and have already burned us once:

- **No reverse-engineering of commercial APIs** (Avalara, Vertex,
  Sovos, TaxJar, TaxCloud). Implement from primary sources only:
  state statutes, DOR publications, SST docs.
- **No paid datasets**. Free public data only.
- **Disclaim everything.** Every TaxabilityRule.notes field
  should remind future readers this is calculation, not advice.
- **No floats for money**. Always Decimal.
- **No engine branches on dialect.** Anything you add must work
  on both PostgreSQL and MariaDB without conditional code in
  business logic.

## Common pitfalls to avoid

- **Don't trust Sovos defaults blindly.** The Sovos summary has
  documented errors (we caught 7 -- see
  `specs/research/sovos-state-summary.md` defects table). Always
  cross-check with the state DOR.
- **Don't hardcode 2026 holiday dates as if they recur**. They're
  set annually by the legislature; future years need explicit
  data updates.
- **Don't forget `parent_authority_name`**. It's NULL for
  state-level rates and the state's name (e.g., `"California"`)
  for sub-state authorities. Loader uses it to build the
  authority hierarchy.
- **Effective dates matter.** A rule with `effective_from` in the
  future or `effective_to` in the past will be skipped by the
  engine. Use `dt.date(YYYY, M, D)` and pin to when the law
  changed, not "today".
- **The `self_seeded` flag is for non-SST states only**. SST
  states load from upstream files; setting `self_seeded = True`
  on an SST state will silently skip loading their rate file.

## What "done" looks like

- Module file exists and imports cleanly
- All tests pass on both engines (CI confirms)
- SonarQube reports 0 new issues
- `references.md` updated with what you consulted
- `/v1/states?abbrev=<your state>` returns `tier: 1` after a
  fresh `data load`
- `POST /v1/calculate` for an address in your state returns the
  correct combined rate for a `general` category line item

## Time estimate

A pragmatic single-state module (statewide rate + 6 taxability
rules + tests + docs) takes a focused agent **30-60 minutes**
including verification. States with holidays add ~15 minutes per
holiday. Threshold-rule states (NY, MA) take longer because the
v0.6 threshold feature isn't built yet -- those states should
wait or be done in coordination with the threshold feature.

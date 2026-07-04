# Adding or improving a state module

The architectural keystone of OpenSalesTax (per
[constitution §4](../specs/constitution.md)) is the **per-state
contributor pattern**: every US state is a Python module
implementing a small Protocol. Volunteers who know their state's
tax law can add or upgrade a state's coverage independently.

## Coverage tiers

| Tier | What it means | Example |
|---|---|---|
| 0 | No module loaded; calculations return 0 | CA, TX in Phase 1 |
| 1 | Fully maintained: full taxability matrix + 10+ tests | MN, WI |
| 2 | Rate-only via SST data; default taxability matrix | The other 22 SST states |

## How states get from 0 → 2

A non-SST state at tier 0 needs a NEW state module. Follow the
template below.

A SST state can be promoted from "missing" to **tier 2** by
adding it to `src/opensalestax/states/_tier2.py` -- 10 lines per
state. Most rate parsing comes for free from `SstStateModule`.

## How states get from 2 → 1

A tier-2 state has rates but uses the default taxability matrix
(everything taxable except groceries). To promote to **tier 1**,
contribute a state-specific module under
`src/opensalestax/states/<state_name>.py` that:

1. Subclasses `SstStateModule` (or implements `StateModule`
   directly if the state isn't SST)
2. Provides a `_TAXABILITY` dict citing each rule's statute
3. Ships at least 10 known-good test fixtures
4. Updates [MAINTAINERS.md](../MAINTAINERS.md) with your name

## The Protocol

[`opensalestax/states/protocol.py`](../src/opensalestax/states/protocol.py):

```python
class StateModule(Protocol):
    state_abbrev: str          # 'CA'
    state_name: str            # 'California'
    sst_member: bool
    has_sales_tax: bool
    tier: StateTier            # 0, 1, or 2

    def parse_rates(self, source_file: Path, version_label: str) -> Iterable[RateRow]: ...
    def parse_boundaries(self, source_file: Path, version_label: str) -> Iterable[BoundaryRow]: ...
    def taxability_for(self, item_category: str, effective_date: date) -> TaxabilityRule | None: ...
    def special_cases(self) -> Iterable[SpecialCase]: ...
```

## Step-by-step: adding a tier-2 SST state

> New to the SST data files? Read
> [the SST quarterly file format field guide](legislation/sst-file-format.md)
> first — it explains the filename convention, the rate and boundary
> file layouts, and the format gotchas before you meet them in a
> failing test.

**This is the easiest contribution.** If your state is in SST
but not yet listed, add it in three steps:

1. **Look up your state's FIPS code** (e.g. CA = 06, TX = 48).
2. **Add a class** to [`opensalestax/states/_tier2.py`](
   ../src/opensalestax/states/_tier2.py):
   ```python
   class California(SstStateModule):
       """California (CA) -- SST member, state base 7.25%, FIPS 06."""

       state_abbrev = "CA"
       state_name = "California"
       state_fips = "06"
   ```
3. **Add the class to `TIER_2_CLASSES`** in the same file so it
   gets registered.

That's it. The smoke tests in
[`test_state_tier2.py`](../tests/unit/test_state_tier2.py) are
parametrized to cover every registered tier-2 state automatically.

## Step-by-step: promoting to tier 1

A tier-1 module is your chance to make your state's taxability
truly correct. See [`opensalestax/states/minnesota.py`](
../src/opensalestax/states/minnesota.py) and
[`opensalestax/states/wisconsin.py`](
../src/opensalestax/states/wisconsin.py) for examples.

Required:

1. **Module file** `opensalestax/states/<state_name>.py`
2. **`_TAXABILITY` dict** with at least: `clothing`, `groceries`,
   `prescription_drugs`, `prepared_food`, `digital_goods`,
   `general`. Cite the relevant statute in each rule's `notes`.
3. **Register the instance** with
   `MY_STATE = register(MyState())`
4. **Remove the entry from `_tier2.py`** if it was there (no
   double-registration).
5. **Tests file** `tests/unit/test_state_<state_name>.py`. At
   least 10 test cases:
   - 6 parametrized taxability checks (one per category)
   - parse_rates extracts the state base rate from a real SST
     fixture
   - parse_boundaries handles a real boundary fixture
   - registration + Protocol check
6. **MAINTAINERS.md update** -- add your GitHub handle as the
   state's maintainer.

## Don't reverse-engineer commercial APIs

Per [constitution §2](../specs/constitution.md#2-open-source--apache-20),
implementations must come from primary sources only:

- Tax law (state statutes, regulations)
- SST documentation
- State Department of Revenue publications

Reading commercial vendor docs (Avalara, TaxJar, Vertex, Sovos,
TaxCloud) to understand "what tax software does" is fine; copying
their algorithms or schemas is not.

If you currently or formerly worked at one of those vendors,
please flag it in your PR description. Not a blanket exclusion --
just a documented vetting step to verify your contribution is
unencumbered by invention-assignment or non-compete obligations.

## What if my state isn't in SST?

For non-SST states (CA, TX, NY, FL, IL, PA, etc.), there's no
free quarterly rate file. You'll need to:

1. Find your state DOR's published rate data (CSV / PDF / API).
2. Implement `parse_rates` and `parse_boundaries` against that
   format directly (don't extend `SstStateModule`; implement
   `StateModule` directly).
3. Add a refresh procedure documented in your module's docstring.

Phase 1 doesn't ship any non-SST tier-1 states. Phase 2's first
target is California; expect more guidance once that lands.

## Questions?

Open an issue on GitHub or ping the maintainers listed in
[MAINTAINERS.md](../MAINTAINERS.md). State-specific PRs prefer
review by the relevant state's maintainer when one exists.

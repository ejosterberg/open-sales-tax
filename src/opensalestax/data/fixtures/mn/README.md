# Minnesota SST fixtures

Real upstream SST files used as test inputs. Captured from
https://www.streamlinedsalestax.org/ on 2026-05-03.

| File | Source | Rows | Purpose |
|---|---|---:|---|
| `MNR2026Q2FEB18.csv` | full upstream rates file | 147 | rate-parser tests |
| `MNR2026Q2FEB18.zip` | full upstream rates ZIP | 147 (1 CSV inside) | fetcher / unzip tests |
| `MNB2026Q2FEB18-sample.csv` | first 100 lines of upstream boundary | 100 | boundary-parser tests (full file is 40k rows / 5.6 MB; trimmed for repo size) |

Refresh procedure when SST publishes a new quarter:

```bash
# Where SST publishes the current quarter (URL pattern is stable)
curl -O https://www.streamlinedsalestax.org/ratesandboundry/Rates/MNR2026Q3<MONTH><DAY>.zip
curl -O https://www.streamlinedsalestax.org/ratesandboundry/Boundary/MNB2026Q3<MONTH><DAY>.zip

# Replace fixtures
unzip -p MNR<...>.zip > src/opensalestax/data/fixtures/mn/MNR<...>.csv
mv MNR<...>.zip src/opensalestax/data/fixtures/mn/
unzip -p MNB<...>.zip | head -100 > src/opensalestax/data/fixtures/mn/MNB<...>-sample.csv

# Update tests that reference filename strings
# Re-run tests to confirm parser still handles the new vintage
poetry run pytest tests/unit/test_sst_parser.py
```

These are public-domain government data; no copyright concerns
with bundling them in the repo.

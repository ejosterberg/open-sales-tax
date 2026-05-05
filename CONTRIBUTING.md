# Contributing to OpenSalesTax

Thanks for your interest in helping build a free, open-source US sales-tax
calculation API. This document covers everything you need to make your
first contribution.

## TL;DR

1. Fork + clone the repo.
2. Install Python 3.11+ and Poetry.
3. `poetry install` then `pre-commit install`.
4. Make your change. Add tests.
5. Commit with `git commit -s` (the `-s` is required — see DCO below).
6. `pytest` passes against both PostgreSQL and MariaDB locally.
7. Open a PR. CI runs lint + DCO check + tests on both engines.

## Code of conduct

This project follows [Contributor Covenant 2.1][cc]. By participating
you agree to abide by its terms. Be kind; assume good faith; help others
learn.

[cc]: https://www.contributor-covenant.org/version/2/1/code_of_conduct/

## Development environment

### Requirements

- **Python 3.11 or later** — pinned in `.python-version`. Use [`pyenv`][pyenv]
  if you need to manage multiple versions.
- **Poetry 1.8+** — see [installation guide][poetry-install].
- **Docker + Docker Compose** — for running PostgreSQL and MariaDB locally
  via the bundled `docker-compose.yml`.

[pyenv]: https://github.com/pyenv/pyenv
[poetry-install]: https://python-poetry.org/docs/#installation

### Setup

```bash
git clone https://github.com/ejosterberg/open-sales-tax.git
cd open-sales-tax
poetry install
poetry run pre-commit install
```

### Running tests

```bash
# Against PostgreSQL (default)
docker compose --profile postgres up -d
export OPENSALESTAX_DATABASE_URL="postgresql+asyncpg://opensalestax:opensalestax@localhost:5432/opensalestax"
poetry run pytest

# Against MariaDB
docker compose --profile mariadb up -d
export OPENSALESTAX_DATABASE_URL="mysql+asyncmy://opensalestax:opensalestax@localhost:3306/opensalestax"
poetry run pytest
```

**Tests must pass on both engines** before a PR can be merged. CI enforces this.

### Linting and formatting

The CI workflow runs **all four** of these on every push -- run them
locally before committing to avoid red builds:

```bash
poetry run ruff check src tests        # lint
poetry run ruff format --check         # format CHECK (CI gate)
poetry run mypy src/                   # type check
poetry run pytest -q                   # tests
```

If `ruff format --check` reports diffs, run `poetry run ruff format`
to apply them, then commit. Do NOT commit only after `ruff check` --
the format check is a separate gate and a common red-CI cause.

`pre-commit` runs lint + format on every commit; install it once with
`poetry run pre-commit install` and you'll never need to think about it.

## Developer Certificate of Origin (DCO)

**Every commit to this project must be signed off** with the
[Developer Certificate of Origin][dco] v1.1. This is OpenSalesTax's
contributor agreement — no separate CLA to sign.

[dco]: https://developercertificate.org

### What is DCO?

The DCO is a one-line statement (auto-added when you commit with `-s`)
asserting that:

- You wrote the code yourself, **or**
- You have the right to submit it under the project's Apache 2.0 license,
  **and**
- You understand the contribution is public, recorded indefinitely, and
  redistributable under the same terms.

The full text is on the [DCO website][dco]. It's lightweight and used by
the Linux kernel, GitLab, Docker, and most CNCF projects.

### How to sign off

```bash
git commit -s -m "your commit message"
```

The `-s` flag adds a trailer like:

```
Signed-off-by: Your Name <your.email@example.com>
```

The name and email must match your `git config user.name` and
`git config user.email`.

### Forgot to sign off?

Amend the most recent commit:

```bash
git commit --amend -s --no-edit
```

Or for older commits in your branch:

```bash
git rebase HEAD~N --signoff   # last N commits
```

CI will block PRs with un-signed commits.

## Per-state contributor pattern

The architectural keystone: **every state is a Python module that
implements a common Protocol.** If you know your state's tax law, you
can drop in your state's data and quirks.

Read [`specs/phase-1-foundation/plan.md`][plan] for the architecture
and [`specs/research/state-coverage.md`][coverage] for state-by-state
notes.

[plan]: specs/phase-1-foundation/plan.md
[coverage]: specs/research/state-coverage.md

A state module ships with:

- Rate parser (consumes upstream rate data)
- Boundary parser (consumes upstream boundary data)
- Taxability matrix (which categories are taxable in this state)
- At least 10 known-good test cases (real addresses + expected rates)
- One-page state-specific quirks document
- Update procedure (CLI + cron-ready)
- Maintainer listed in `MAINTAINERS.md`

**No tests = not officially supported.** Constitution §12.

## What NOT to do

These rules come from [`specs/constitution.md` §2][const-2] (patent
landscape):

- **Don't reverse-engineer commercial sales-tax APIs** (Avalara,
  Vertex, Sovos, TaxJar, TaxCloud) to derive algorithms or schemas.
  Implement from primary sources only — tax law, SST documentation,
  state DOR publications.
- **Don't name features after commercial products** (no
  "AvaTax-compatible," no "TaxCloud-style").
- **Don't import paid datasets.** Free public data only —
  constitution §3.
- **If you currently or formerly worked at a commercial sales-tax
  vendor**, please flag this in your PR description so maintainers
  can verify your contribution is unencumbered by invention-assignment
  or non-compete obligations. Not a blanket exclusion — just a
  documented vetting step.

[const-2]: specs/constitution.md

## Pull request process

1. **Open an issue first** for non-trivial changes so maintainers can
   confirm the direction. Trivial fixes (typos, doc improvements) can
   skip this.
2. **Branch from `main`** with a descriptive name
   (`feature/state-iowa`, `fix/mn-rate-rounding`).
3. **Add tests.** Every change needs tests. State modules without
   tests are not officially supported per constitution §12.
4. **Run the full pipeline locally** before pushing:
   - `poetry run ruff check && poetry run ruff format --check`
   - `poetry run mypy src/`
   - `poetry run pytest` against both engines
5. **Sign off every commit** (`git commit -s`).
6. **Open the PR.** Describe what changed and why. Link the issue.
7. **CI runs:** lint, DCO check, tests against both engines, Docker
   build. All must pass.
8. **One maintainer review** is required to merge. State-specific PRs
   prefer review by that state's maintainer when one exists.

## License

By submitting a contribution, you agree to license it under the
[Apache License 2.0](LICENSE) — the project's license. Your DCO
sign-off is your assertion of the right to do so.

## Questions?

Open an issue or discussion on GitHub. Maintainer is Eric Osterberg
([@ejosterberg](https://github.com/ejosterberg)) until additional
maintainers are added (per constitution §14).

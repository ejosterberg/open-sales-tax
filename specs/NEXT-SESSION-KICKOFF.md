# NEXT-SESSION KICKOFF

> **Read this file first.** Eric reset the session intentionally
> and wants you to execute the two tasks below in order. The
> previous session's context is gone, but everything you need is
> committed in this repo.

## Where the project is right now

- **Latest release: v0.5.0** (https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.5.0)
- 16 tier-1 states, 22 tier-2 states, 14 unsupported (`tier 0`)
- 310 unit tests + 37 integration tests, CI green on PostgreSQL +
  MariaDB, SonarQube 0/0/0/0 with all-A ratings, 3601 LOC
- `specs/current-state.md` has the full feature ladder and
  release history

## Your two tasks (in this order)

### Task 1 — Provision the production-target Proxmox VM

Eric needs a live deployment of the API so he can test it from a
separate PHP project. Use the recipe in
`~/.claude/proxmox-playbook.md` (auto-loaded into your context
via the global CLAUDE.md).

**Recipe specifics for this VM:**

```bash
ssh proxmox-workshop bash <<'PROVISION'
set -e
VMID=900                     # First free in the 900-999 range
NAME=opensalestax-01         # Follows <project>-NN convention
MEM=8192                     # 8 GB
CORES=4
DISK=80                      # 80 GB
ISO=/var/lib/vz/template/iso/debian-13-genericcloud-amd64.qcow2

# Download cloud image if not already cached
[ -f $ISO ] || wget -qO $ISO https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2

# Create VM shell
qm create $VMID \
  --name $NAME --memory $MEM --cores $CORES --cpu host \
  --net0 virtio,bridge=vmbr0 \
  --scsihw virtio-scsi-single \
  --serial0 socket --vga serial0 \
  --agent enabled=1 --ostype l26

qm importdisk $VMID $ISO vmpool
qm set $VMID --scsi0 vmpool:vm-$VMID-disk-0,discard=on,ssd=1
qm set $VMID --ide2 vmpool:cloudinit
qm set $VMID --boot order=scsi0
qm resize $VMID scsi0 ${DISK}G
qm set $VMID --ciuser ejosterberg          # ALWAYS ejosterberg
qm set $VMID --sshkeys /root/.ssh/authorized_keys
qm set $VMID --ipconfig0 ip=dhcp
qm start $VMID
PROVISION
```

After it boots:

1. **Discover its IP** (per playbook: arp-scan or tcpdump
   the VM's MAC for outgoing traffic; the playbook has the exact
   commands).
2. **Add an SSH alias** to `~/.ssh/config` on Eric's Windows box:
   ```
   Host opensalestax-01
     HostName <discovered-ip>
     User ejosterberg
     IdentityFile ~/.ssh/proxmox_workshop
     IdentitiesOnly yes
     StrictHostKeyChecking accept-new
   ```
3. **Bootstrap the host:**
   ```bash
   ssh opensalestax-01 'sudo apt update && sudo apt install -y docker.io docker-compose-v2 git'
   ssh opensalestax-01 'sudo usermod -aG docker ejosterberg'
   # Then disconnect + reconnect so the docker group takes effect
   ```
4. **Clone the repo + start the stack:**
   ```bash
   ssh opensalestax-01 bash <<'BOOTSTRAP'
   git clone https://github.com/ejosterberg/open-sales-tax.git
   cd open-sales-tax
   docker compose --profile postgres up -d
   sleep 15  # wait for postgres healthcheck
   docker compose run --rm api alembic upgrade head
   # Load every tier-1 state's data
   for state in CA TX NY FL PA IL MD MA AZ MN WI; do
     docker compose run --rm api opensalestax data load --state $state --version v0.6
   done
   curl -sf http://localhost:8080/v1/health || echo 'health check failed'
   BOOTSTRAP
   ```
5. **Verify externally:**
   ```bash
   curl http://<vm-ip>:8080/v1/health
   curl http://<vm-ip>:8080/v1/states | jq '.states[] | select(.tier == 1) | .abbrev'
   curl -X POST http://<vm-ip>:8080/v1/calculate \
     -H 'Content-Type: application/json' \
     -d '{"address":{"zip5":"75201"},"line_items":[{"amount":"100.00","category":"general"}]}'
   ```

**Report back to Eric:** the VM's IP, the SSH alias name, and a
working curl example.

**Then update** `specs/current-state.md` with a "Live deployment"
section recording the VM's IP, hostname, and provisioned date.

### Task 2 — Spawn parallel state-research agents

Once the VM is up, start the multi-agent buildout per
`specs/agent-briefs/multi-agent-coordination.md` and the per-agent
template in `specs/agent-briefs/per-state-research-brief.md`.

**Recommended first batch (Phase 6 / Batch A — 4 simple tier-0
states):**

| Agent | State | Why first |
|---|---|---|
| 1 | **CT** Connecticut | State-only (one local jurisdiction = Mashantucket Pequot at 1%); fast win |
| 2 | **DC** District of Columbia | Single jurisdiction; trivial |
| 3 | **SC** South Carolina | State + simple county model; County of Myrtle Beach surcharge documented |
| 4 | **VA** Virginia | State + regional; tractable |

Spawn each via the `Agent` tool with `subagent_type=general-purpose`
(or whichever your harness offers; Claude Code's default Agent tool
should work). Each agent's prompt:

```
You are a per-state research-and-implementation agent for the
OpenSalesTax project at C:\Users\ejosterberg\Documents\GITprojects\sales_tax_api_service.

Your assignment: bring **{STATE_NAME} ({ABBREV})** up to tier 1.

Before any code:
1. Read specs/agent-briefs/per-state-research-brief.md COMPLETELY
2. Read the example modules cited there (california.py for the
   non-SST self_seeded pattern; minnesota.py for SST states)
3. Read specs/research/references.md to see what we already
   know

Then: research, implement, test, document. Sign off every commit
(`git commit -s`). Work on a dedicated branch:
`feat/state-{abbrev_lower}`. Push the branch + open a PR with a
clear summary of what you verified against external sources.

Stop and ask before:
- Making any schema change
- Touching files outside the tier-1 brief's "files agents WILL
  touch" list
- Resolving a statutory ambiguity from anything other than primary
  sources

Quality bar (non-negotiable, per the brief):
- 0 SonarQube issues
- All tests pass on PostgreSQL AND MariaDB
- DCO sign-off on every commit
- Statutory citations in every TaxabilityRule.notes
- specs/research/references.md updated with every external source
```

Run **all 4 agents in parallel** (one Agent call with all 4 in a
single message). Each works on its own branch. When all 4
return, you (the orchestrator):

1. Fetch the 4 branches: `git fetch origin feat/state-ct feat/state-dc feat/state-sc feat/state-va`
2. Merge each PR (squash-merge style; one commit per state)
3. Resolve any conflicts in `states/__init__.py` (alphabetical
   order)
4. Run the full local test suite + SonarQube scan
5. Bump version to **v0.6.0**, tag, GitHub release
6. Deploy: `ssh opensalestax-01 'cd open-sales-tax && git pull && docker compose run --rm api opensalestax data load --state CT --version v0.6 && [...same for DC/SC/VA...]'`
7. Update `specs/current-state.md` coverage table

Then move on to **Batch B** (5 more states: MO, MS, ID, CO, LA)
following the same pattern. CO and LA are harder because of
home-rule cities + parishes — flag any roadblocks and ask Eric
how to proceed if a state's local-tax model needs new schema
support.

**Suggested batching cadence:** ship one release per batch (v0.6,
v0.7, ...). Don't merge a state's PR if its CI is red or if
SonarQube reports new issues — send it back to the agent.

## Standing rules (from `specs/handoff.md`)

- Standing permission to commit directly to `main`.
- **Push allowed without per-deploy approval** (Eric granted
  2026-05-03).
- No AI co-author trailers in commits.
- DCO sign-off (`-s`) required on every commit; CI enforces.
- Run `poetry run pytest -q` before declaring done.
- Run SonarQube scan after each state batch via
  `~/.claude/sonarqube-playbook.md`.
- Project venv: Python 3.11.15 + Poetry 2.3.4 already installed
  via `uv` (no setup needed).
- gh token has `gist, read:org, repo, workflow` scopes (no
  re-auth needed).

## When to stop

Eric said "build out a complete solution" — i.e. push as far as
you can go autonomously while maintaining the quality bar. Stop
and report back if:

- Any agent's PR can't pass the quality bar after one round of
  feedback (orchestrate a retry; if still stuck, escalate)
- A schema change becomes necessary mid-buildout (don't change
  the schema piecemeal across states)
- You hit a state with a tax model not yet supported (e.g. HI's
  GET, NM's GRT) — these probably need a small Protocol
  extension before being fully modeled
- You've successfully pushed through Batch A and want to
  checkpoint with Eric before continuing

## Acknowledgment

When you complete this kickoff, **delete this file** and add a
note to `specs/current-state.md` saying "v0.6 / Phase 6 buildout
in progress, started YYYY-MM-DD". This keeps the kickoff doc
from misleading future sessions.

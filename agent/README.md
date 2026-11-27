# Agent loop

A scheduled task runs `agent/orchestrator.md` in a cloud container. The orchestrator picks
functions with `tools/agent/pick.py`, hands each one to a worker (`agent/worker.md`), checks
the result with `tools/agent/lint.py` and `agent/review.md`, and commits to the `agent-work`
branch. A person reviews the draft pull request from `agent-work` before anything reaches
`main`.

| File | Purpose |
|------|---------|
| `agent/orchestrator.md` | What one scheduled run does |
| `agent/worker.md` | How a worker matches one function |
| `agent/review.md` | What a match must pass before it's committed |
| `agent/state.json` | Attempts and results per function, kept on `agent-work` |
| `tools/agent/pick.py` | Picks the next function; records results; `stats` for progress |
| `tools/agent/lint.py` | Mechanical checks on the diff |
| `tools/agent/setup-cloud.sh` | Container setup: toolchain, disc from R2, verified build |

## Cloud environment

- Setup script: `bash tools/agent/setup-cloud.sh`
- Secrets: `R2_ENDPOINT`, `R2_BUCKET`, `FF8_DISC_PREFIX`, `AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY`
- Network: the R2 endpoint, plus the package registries, GitHub and the Ubuntu archive.

## Order of work

Core game first (field, battle, world, menus), effect overlays last, since that's the order
a port needs them in. Inside each tier, overlays closest to finished go first, and small
functions before large ones. Change `TIERS` in `pick.py` to reorder.

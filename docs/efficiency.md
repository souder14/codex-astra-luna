# Token/context efficiency

More workers can reduce elapsed time while increasing total tokens. The configured
six-worker limit is a ceiling. Delegate substantial independent work, combine
related small tasks, and avoid paying orchestration overhead for trivial actions.

## Practices built into the skill

* Explicit fresh Luna contexts and short, self-contained task packets.
* Workers inspect their own relevant files; Astra avoids duplicating full reads.
* Narrow searches/read ranges; verbose logs remain on disk with decisive excerpts.
* Concise reports and a small assignment ledger with dependencies and ownership.
* Long, native completion-driven waits; no habitual status messages or duplicate work.
* Fresh reviewers only for meaningful risk; rerun checks for integration risk or new changes.
* A concise CODEX_STATE.md for substantial work and fresh root sessions at clean boundaries.

## Optional local session audit

Bound the sample, for example the newest 40 roots within 30 days plus descendants.
Open SQLite read-only and stream relevant rollouts. Do not copy entire runtime
databases or conversations into the repository. Report only aggregates and
necessary local evidence paths, with credentials and private content excluded.

Measure model/effort distribution, first/last input sizes, cache counts, compaction
markers, explicit fork modes, wait durations, status-call counts and tool-output
sizes. Include both function-call and custom-tool-call event types where present.
Link forks by real parent/child metadata where possible; label heuristics.

Deduplicate repeated usage snapshots. Cumulative counters may include inherited
history, resets or earlier turns. Do not sum them blindly or treat cached input as
free. Separate root/child metrics, expose missing telemetry, and do not convert
counter totals into billing dollars. Output bytes are not tokens. Distinguish
native agent waits from shell/tool waits before labeling polling waste.

A before/after comparison of fresh and inherited contexts needs matched tasks and
comparable instrumentation. Without that, report opportunities—not a causal
percentage saving. Keep any raw findings private. No private session statistics
are needed to install this kit.

Consider pruning genuinely unused integrations only with user authorization.
Authentication warnings and large catalogs may add startup noise/context, but
do not disable unrelated plugins or security controls merely to optimize tokens.

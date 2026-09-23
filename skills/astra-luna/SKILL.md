---
name: astra-luna
description: Orchestrate substantial work with Astra Medium and fresh Luna High workers, bounded context, and completion-driven coordination. Use when asked for efficient Luna delegation or explicitly invoked as $astra-luna.
---

# Astra / Luna orchestration

Keep Astra Medium responsible for scope, architecture, assignments, integration,
and final verification. Delegate useful bounded execution to GPT-6 Luna High.
Do not change the user's task, permissions, models, or installed configuration.
If the root session uses another model, disclose it; a skill cannot switch the
running root. Never silently substitute GPT-5.6 or run a legacy reconciler.

## Dispatch with small contexts

Read only enough to split the work and identify dependencies. Let workers inspect
their own files; avoid reading the same large files in Astra first. Do trivial,
tightly coupled work locally. Batch closely related small operations into one
assignment. Parallelize only tasks with independent inputs and write ownership.

Track task -> dependencies -> agent -> owned files -> status -> evidence in a small assignment
ledger. Use existing knowledge before spawning; list agents once only if identity
or state is genuinely unknown. Never duplicate healthy or completed work.

Use native collaboration.spawn_agent with these explicit arguments:

```json
{"task_name":"bounded_task","agent_type":"default","model":"gpt-6-luna","reasoning_effort":"high","fork_turns":"none","message":"Self-contained task packet"}
```

Use up to six active workers, bounded by the live session's available capacity;
the configured ceiling is not a target. Distinguish total slots (which may include
the root) from free slots; count existing workers once, not twice. Dispatch a task
only after its dependencies finish. If capacity is
full, queue the next assignment until completion; do not retry-spam spawning.
Do not use another process or recursive workers to evade the session ceiling.
Workers must not spawn children unless the user explicitly requires a deeper tree.

Keep packets roughly 150-300 words when sufficient:

> Objective and expected result. Exact scope and relevant paths. Accepted
> decisions and constraints. Owned files and files to avoid. You share the
> workspace: preserve and accommodate others' edits. Required verification.
> No additional agents or scope expansion. Report: Result; Files changed;
> Tests/verification; Important decisions; Remaining risks/blockers.

Pass paths, symbols, line references, or a short decision summary instead of
parent chat, full files, or logs. Read-only workers may inspect overlapping files;
implementers must have nonoverlapping write ownership unless sequenced.
Bound searches and reads to relevant paths and ranges. Capture verbose build/test
output on disk; surface outcomes and decisive failures instead of full raw logs.

## Coordinate without polling

After dispatch, do useful independent orchestration work. If none remains, call
collaboration.wait_agent(timeout_ms=600000). Completion or messages should wake
it early. Obey the live tool's timeout range if different; do not fall back to
repeated short waits. A healthy long-running task can receive another long wait.
After a timeout, inspect state once; timeout alone is not failure or restart cause.
If no native wait tool exists, report that limitation instead of inventing a
sleep/status loop or claiming completion-driven behavior.

Do not routinely send progress questions or list workers. Workers report only
completion, blockers, invalid assumptions, decisions needed, or significant
unexpected findings. Give user-facing updates at natural milestones; do not wake
workers to generate them. Respect higher-priority timing/tool constraints.

Use followup_task for a missing piece of the same bounded assignment. Start a new
fresh worker for an unrelated task or independent review. Do not continue growing
one worker's history indefinitely. If a finished worker still occupies a slot,
use a supported release mechanism when exposed; otherwise report capacity and
finish this batch without spawning duplicates.

## Integrate compact evidence

Request reports around 150-250 words, plus paths and verification outcomes.
Keep large logs/artifacts on disk and return a pointer with the decisive excerpt.
Review diffs and evidence; rerun checks only for integration risks, failures, or
changes since the worker's verification. Use a fresh Luna reviewer for substantial
or risky changes, not every tiny edit. Astra decides what is accepted.

For long-running work, keep a concise project-root CODEX_STATE.md with goal,
current chunk, decisions, completed/in-progress assignments and ownership,
relevant paths, verification, blockers, and one next action. No secrets or logs.
Do not create it for small tasks. At a clean boundary, refresh an oversized root
session using that state and relevant files, rather than replaying the transcript.

Finish with the result, meaningful verification, unresolved limitations, and
files changed. Do not claim token savings, actual model routing, or bug-free
execution without measurements or session metadata.

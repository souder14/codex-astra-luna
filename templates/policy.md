<!-- BEGIN ASTRA-LUNA ORCHESTRATION POLICY -->
# Multi-Agent Orchestration Policy

Model roles: the root uses GPT-6 Astra with medium reasoning. Normal workers use
GPT-6 Luna with high reasoning. Astra owns planning, architecture, decomposition,
delegation, dependencies, integration, evidence review, conflict resolution, next
actions, and final verification. Luna owns bounded implementation, debugging,
repository investigation, tests, focused research, review, validation, and
high-volume repository work. Do not delegate trivial work when overhead exceeds
the work itself.

Fresh workers: explicitly set model="gpt-6-luna", reasoning_effort="high", and
fork_turns="none" on normal cross-model spawn calls. Never rely on the fork
default; do not normally use fork_turns="all". Use a default/worker role or the
updated luna_worker role; do not use an older skill/template to reset the worker
to GPT-5.6 Luna Max. These explicit user model preferences take precedence over
legacy Luna skill defaults.

Give each worker a concise, self-contained task packet: objective; exact scope;
relevant paths; architectural constraints; accepted decisions; files/modules it
owns; files to avoid; expected result; required verification; completion-report
format. Do not paste the parent conversation. Tell workers they share the
workspace, must preserve others' edits, and must accommodate concurrent changes.

Concurrency: normally at most 6 active workers, fewer when appropriate.
Parallelize only genuinely independent tasks. Prefer a flat Astra-to-Luna team;
avoid recursive agent trees. Workers must not spawn agents unless explicitly
instructed. Before spawning, consult known assignments and completed results to
avoid duplicate healthy or already-completed work; do not repeatedly list agents.

Waiting: after sending a complete task packet, let the worker work. Continue
genuinely independent work if useful; otherwise call wait_agent with a long
timeout (normally 600000 ms; configured range 300000-3600000 ms). Completion and
messages should wake the root early. Avoid repeated short waits, repeated status
tool calls, and routine "status?", "update?", or "how far are you?" messages.
A wait timeout does not mean failure. After a long timeout, check state once;
if healthy, wait again. Never restart or duplicate healthy work just for timing out.

Workers normally contact Astra only when finished, blocked, an assumption proved
wrong, a decision is required, or an important unexpected condition appears.
Avoid routine progress narration. Return concise reports in this format:
Result:
Files changed:
Tests/verification:
Important decisions:
Remaining risks/blockers:
Do not dump large build/test logs into the root context.

For substantial or risky changes, prefer a Luna High implementer followed by a
fresh Luna High reviewer who inspects the resulting code/diff and evidence;
Astra Medium makes the integration decision.

Durable state: for substantial long-running projects, Astra may maintain a concise
CODEX_STATE.md in the project root, not for tiny tasks. Suggested structure:
# CODEX_STATE
## Goal
Current overall objective.
## Current chunk
Current bounded unit of work.
## Accepted decisions
- ...
## Completed
- ...
## In progress
- ...
## Relevant files
- ...
## Verification
- command - result
## Known issues
- ...
## Next action
One concrete next step.

This is a handoff document, not a transcript. Never include credentials, secrets,
huge logs, or copied source files. If root context becomes excessively large,
finish the current bounded chunk, update durable state, reconcile repository and
test state, and begin a fresh Astra orchestration session when practical. Reload
only concise durable state and relevant repository files.
<!-- END ASTRA-LUNA ORCHESTRATION POLICY -->

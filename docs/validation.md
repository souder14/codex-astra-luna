# Runtime validation

Use a disposable directory outside real projects and outside this checkout for
private evidence. Create a README.md with a known heading. Use fresh sessions,
not the setup agent's pre-existing model/tool context. Save JSON events and
session metadata privately; do not publish rollouts or auth data.

## One-worker routing test

Ask a fresh root, without overriding the configured root model:

> Spawn exactly one native default-role worker with model="gpt-6-luna",
> reasoning_effort="high", fork_turns="none". Have it inspect only README.md and
> return its first Markdown heading. No changes, other agents, network or apps.
> Receive its completion and report the result and observed routing evidence.

Verify Astra Medium in actual root metadata and Luna High in child metadata.
Confirm the recorded spawn uses the explicit fresh fork. A requested argument or
model's self-description is not proof of actual routing. On supported versions,
read thread metadata through the app-server or the local state SQLite database in
read-only mode; schema/layouts are version-dependent. Inspect recorded tool calls
for fork and timeout values. Do not modify databases.

## Long-wait test

Ask one separate harmless worker to sleep for 40 seconds once, then read the
fixture heading. Have Astra immediately request native wait_agent with a 600000 ms
timeout. It should wake when completion arrives, not after ten minutes. Record
call/output timestamps, timeout outcome and how many waits/status calls occurred.
One long wait per completion is expected; repeated 30-second waits/status queries
are not. Do not mistake waiting for a shell process for polling an agent.

If it fails, distinguish config not loaded, higher-precedence overrides, model
choice, missing tool, and client bug. Do not restart healthy work just for timing
out. Do not claim success from the configured timeout alone.

## Fresh policy test

In another fresh root, without repeating the policy:

> Without tools or new agents, summarize the normal worker model, reasoning,
> context-fork choice, concurrency, waiting and durable-state practices required
> by the global instructions already loaded. State their source.

Inspect the prompt-input/debug surface when available to confirm the actual
global section loaded. Check AGENTS.override.md precedence and project rules.

## Skill behavior test

Create two small independent read-only fixture files. Ask:

> Use $astra-luna to assign exactly two independent read-only reviews of the two
> fixture files. Each worker sleeps once for 35 seconds before inspecting its
> file and returns one useful finding with a short supporting excerpt. Make no
> changes, use no external apps and spawn no further agents. Integrate the results.

Verify skill loading, two fresh Luna High children, bounded assignments, native
long waiting, no routine worker-list/status polling, and evidence-based integration.
This artificial task tests behavior; ordinary tiny reads should not require two workers.

## Final checks

Parse TOML; inspect strict-loader errors; compare unrelated settings before/after;
verify backup hashes and safe restore dry run. Review all auto-created test trust
entries. Reconfirm live files match the after snapshot. Do not undo the successful
live setup to test rollback. Report unsupported observability explicitly.

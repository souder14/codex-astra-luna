# Codex Astra + Luna

Reproduce a backup-first Codex setup with **GPT-6 Astra / Medium** orchestrating
up to **six GPT-6 Luna / High** workers in fresh contexts.

Give an agent this prompt:

> Read https://github.com/souder14/codex-astra-luna/blob/main/SETUP.md and implement
> the setup on this machine. Create and verify the permanent rollback snapshot
> before modifying any Codex configuration or instructions. Preserve unrelated
> settings, verify installed support, run the runtime tests, and report the exact
> rollback command. Use six as the worker ceiling, not a utilization target.

Or clone this repository and ask the agent to follow `SETUP.md`.

## What it installs

* Astra Medium as the root; Luna High worker defaults and custom role.
* Multi-Agent V2 with six workers maximum, where supported.
* Explicit `fork_turns="none"` in the global policy and `$astra-luna` skill.
* Completion-driven waits: 5-minute minimum, 10-minute default, 60-minute maximum.
* Concise assignments/reports, duplicate prevention, independent review when useful,
  and optional durable `CODEX_STATE.md` for long-running work.
* Experimental context management disabled.

Use the installed skill in a **fresh session**:

```text
$astra-luna Implement the feature described in SPEC.md
```

The skill uses fewer workers when parallelism would waste tokens or create
conflicts. Six is a selected practical ceiling, not a universal Codex maximum.

## Safety and scope

The Windows-first tooling creates restricted, timestamped backups with SHA-256
verification and a standalone PowerShell rollback script. It preserves unrelated
TOML keys, original instructions, and role instructions. Previously absent files
are recorded; rollback removes only files introduced by the migration.

`configure.py` defaults to planning, probes the installed client's model catalog
and strict configuration loader, detects concurrent file changes before applying,
and rolls back on application/validation failure. It does **not** replace the
agent's profile/managed-layer inspection or runtime smoke tests.

This repository contains reusable assets only: no personal config, authentication,
session logs, database copies, backup snapshots, or private project data. Keep all
installation evidence outside the checkout. Do not blindly paste the config
template over an existing config.

## Compatibility

The source setup was exercised on native Windows with Codex CLI **0.155.1**.
Fresh-session metadata confirmed Astra Medium, Luna High, and explicit fresh
forks. Delayed workers woke 10-minute waits early without status polling.
These observations are not a guarantee against future client/model bugs.

Check the installed build; version numbers alone do not prove model entitlement
or feature availability. Never silently substitute GPT-5.6 Luna. Automated
snapshot/apply/rollback scripts currently target Windows. Other platforms require
an agent to implement the equivalent safe workflow described in `SETUP.md`;
cross-platform automation is not claimed.

## Contents

* [SETUP.md](SETUP.md): complete agent implementation and verification contract.
* [scripts](scripts): verified backup, guarded merge, and standalone rollback.
* [skills/astra-luna](skills/astra-luna): the invokable orchestration skill.
* [docs/efficiency.md](docs/efficiency.md): session-audit methodology and savings practices.
* [docs/validation.md](docs/validation.md): harmless runtime test prompts and evidence requirements.

## Toolkit development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests operate on temporary fake homes, not your live Codex configuration.

Reference: [official Codex configuration schema](https://developers.openai.com/codex/config-schema.json).

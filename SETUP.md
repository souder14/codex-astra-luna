# Agent setup contract

Implement this workflow; do not stop at giving the user instructions. Default to
six workers unless the user chooses otherwise. Preserve unrelated configuration.
The final outcome is Astra Medium orchestration, fresh Luna High execution,
completion-driven coordination, and a permanent, verified one-command rollback.

## 0. Discover and back up before changing anything

Run `codex --version` and `codex --help`. Resolve CODEX_HOME from the environment,
otherwise the actual user's `~/.codex`; do not assume a username or installation
path. Inspect config.toml, both global AGENTS files, active profiles, custom roles,
project layers, managed/admin requirements, relevant command-line overrides, and
feature flags. Determine the effective instruction source (normally
AGENTS.override.md when present, otherwise AGENTS.md).

Inspect applicable skill instructions, but keep the explicit GPT-6 target.
Old Luna reconciliation scripts may hard-code GPT-5.6 and undo this setup.

Before the first configuration/instruction write, create a persistent timestamped
snapshot outside this checkout. Use one timestamp per migration. Back up every
target, preserve timestamps/permissions, record absent files, and verify SHA-256
against each live source. Stop if any verification fails. Do not copy auth,
caches, sessions, whole repositories, or runtime databases.

On native Windows, run from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\backup.ps1
```

The script prints the backup directory and rollback command and covers all files
the provided merger may modify. Inspect `snapshot.json`, `CHECKSUMS.before.txt`,
`BACKUP_MANIFEST.txt`, and `restore.ps1`. Add any additional targets to the SAME
snapshot before touching them. Record effective profile/precedence and client
installation details in private `environment.json` alongside the manifest.

Use `restore.ps1 -VerifyOnly` and `restore.ps1 -WhatIf` to inspect restoration
without changing the live configuration. Never overwrite or delete this snapshot.

On Unix, implement the equivalent snapshot with mode 0700 directories, metadata-
preserving copies, checksums, absent-file records, and a standalone confirmation-
gated restore.sh. Do not run the Windows merger without its rollback mechanism.

## 1. Verify actual support

Use installed help, schema/client behavior, and current official documentation.
Confirm the refreshed model catalog exposes `gpt-6-astra` with `medium` reasoning
and `gpt-6-luna` with `high`. Confirm V2, explicit model/effort overrides, fresh
forks, native wait, concurrency limits, hint fields, and context-management fields.
Do not infer support from this repository's templates or version alone.

If the client lacks essential support, make NO configuration changes. Report the
version, missing capability and the upgrade procedure for its actual installation
method. Do not auto-upgrade or silently substitute an older Luna model.

If individual optional keys are unsupported, determine a supported equivalent or
omit that field with an explanation. Never insert unknown keys. Do not bypass
managed policy. Preserve security settings and all unrelated features/integrations.

## 2. Stage, inspect, and merge

Create a Python 3.11+ virtual environment and install requirements.txt. Find the
native installed Codex executable (on Windows this may be inside the npm package's
platform-specific vendor directory). Do not assume the wrapper path is an exe.

```powershell
.\.venv\Scripts\python.exe .\scripts\configure.py --backup "ABSOLUTE_BACKUP_PATH" --codex "ABSOLUTE_CODEX_EXE" --cwd "PROJECT_PATH"
```

This stages files privately under the backup and probes supported settings using
nonpersistent CLI overrides. Inspect the plan and effective layers. The helper
targets the default user config; if an active profile changes these defaults,
back up that profile and implement a reviewed equivalent merge manually. Do not
claim a profile-specific installation from a default-profile probe.

Then apply the reviewed plan using the same command with `--apply`. The helper
rechecks backup/live hashes, records which files it will introduce, preserves
unrelated TOML keys/comments, merges the marked policy into the effective global
file, updates only model/effort on an existing worker role, and installs the skill.
Existing differing skill files require a manual reviewed merge, not replacement.
Existing hint text is retained before the new guidance: resolve any conflicting
old model/concurrency instruction explicitly instead of silently deleting it.

Desired values are in templates/config.toml. Normal workers must explicitly pass
model="gpt-6-luna", reasoning_effort="high", fork_turns="none". The installed
skill is invoked with `$astra-luna`. Existing sessions may need restarting.

## 3. Validate configuration and runtime

Parse affected TOML; reject duplicate keys/tables. Start the installed client with
strict configuration checking on a command that supports it (app-server/exec).
Inspect effective config/read and configRequirements/read where exposed. Confirm
root/worker defaults, six-worker ceiling, V2, waits, disabled experimental context
management, loaded global instructions, and preservation of unrelated settings.

Follow [docs/validation.md](docs/validation.md): a fresh root, exactly one harmless
Luna worker, a separate delayed-worker long-wait test, and a fresh-session policy
test without restating the policy. Also test a real `$astra-luna` invocation.
Inspect actual model/reasoning/session metadata when available; record requested
values separately from observed ones. Measure wait duration and whether completion
woke the parent before timeout. Distinguish shell waiting from agent polling.

Do not touch a real project just for tests. Codex may auto-add a trust entry for a
temporary fixture: inspect and remove ONLY the test-created entry, preserving
concurrent unrelated edits. Configured concurrency is not a saturation test;
label it honestly if six simultaneous workers were not exercised.

## 4. Fail safely

For a significant apply/validation failure, stop unrelated changes and invoke the
snapshot's restore script with intentional `-Force`. Verify restored hashes,
removal of migration-created files, and Codex startup. Diagnose a clearly fixable
issue without destructive experimentation; do not leave a half-migrated setup.
The merger rolls back on its own application/strict-validation failures, but the
agent must also roll back if subsequent essential runtime tests fail.

Do not test rollback by undoing a successfully configured live environment. Use
dry runs and disposable fixture tests instead. Rollback must work weeks later
without this repository or conversation (the script is copied into the snapshot).

## 5. Audit efficiency when requested

Use [docs/efficiency.md](docs/efficiency.md). Keep the audit bounded, read-only and
local. Never publish a user's session data or assume cumulative token counters
equal billed usage. Apply workflow improvements in the skill; do not disable
unrelated tools, plugins, or security settings without authorization.

## 6. Capture known-good state and report

After tests pass, create a separate after snapshot with the SAME migration
timestamp. On Windows use backup.ps1 `-Phase after -Timestamp YYYYMMDD-HHMMSS`.
Verify its hashes and retain the before snapshot intact. Reopen final config and
instructions; inspect restore scripts and referenced files; check final effective
values. Keep runtime evidence privately alongside snapshots.

Report these sections with actual results, not assumed successes:

* Environment: Codex version/home, config path, effective global instruction path,
  active profile and precedence.
* Backup and rollback: absolute before/after paths, files saved/absent, checksums,
  restore script and EXACT runnable command.
* Changes: configuration/instruction changes, created and modified files, skill invocation.
* Effective orchestration: root/worker models and reasoning, max workers, fork,
  wait limits and context-management mode.
* Verification: backup, TOML, startup, actual model/reasoning/fork metadata,
  long-wait behavior, global policy, unrelated-settings preservation.
* Rollback verification: script inspection and required backup file verification.
* Issues: unsupported fields, substitutions, overrides, bugs, warnings and anything
  not conclusively tested. Do not promise bug-free behavior or unmeasured savings.

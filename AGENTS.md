# Repository instructions

This repository is a reusable setup kit, not the user's Codex home. Follow
SETUP.md for installation tasks. Reading this repository does not itself authorize
installing it; the user must request setup.

Never commit live config, snapshots, credentials, session databases, raw logs,
or identifying session content. Keep installation evidence under the resolved
CODEX_HOME/backups directory, outside this checkout.

Preserve unrelated configuration. Back up every target before editing. Never
silently downgrade models or bypass managed policy. Run tests against temporary
fake homes; never test destructive rollback on the user's configured home.

For toolkit changes, run `python -m unittest discover -s tests -v`. Do not claim
runtime model routing from a template or requested argument alone. Prefer native
metadata. A six-worker configured limit is not proof of a saturation test.

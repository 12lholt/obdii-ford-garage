# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Offline OBD-II capture/logging for a multi-make garage, built on
[python-OBD](https://python-obd.readthedocs.io/) + an ELM327 dongle, with
optional upload of captures to Azure Blob Storage. Managed with `uv`; Python
3.13+.

## Commands

```bash
uv sync                      # core deps (at-the-car logging)
uv sync --extra azure        # also install Azure upload deps (azure-storage-blob, azure-identity)
uv run garage --help         # CLI entry point (see subcommands below)
uv run ruff check .          # lint
uv run ruff format .         # format (CI runs `ruff format --check .`)
uv run pytest                # full test suite (no hardware needed)
uv run pytest tests/test_config.py::test_env_overrides_connection_url  # single test
```

CLI subcommands: `garage snapshot -v <slug>`, `garage log -v <slug>`,
`garage upload`, `garage vehicles`.

## Architecture

The two original standalone scripts were refactored into one installable package
(`src/obd_garage/`). Key idea: **a vehicle is data, not code.**

- **`config.py`** — `VehicleProfile` is loaded from a TOML file in `vehicles/`
  (selected by slug). `OBD_CONNECTION_URL` env always overrides the profile's
  dongle address so it stays out of this **public** repo. Vehicle dir is
  overridable via `GARAGE_VEHICLES_DIR` (used by tests).
- **`obd_client.py`** — the single source of truth for OBD helpers
  (`serialize`/`unit_of`/`loggable_commands`/`query_with_retry`). These were
  duplicated across the original scripts; don't reintroduce copies.
- **`snapshot.py`** — `take_snapshot(profile)` returns one report dict combining
  data **and** diagnostics. Its value is making failures *legible*: it captures
  python-OBD's handshake log and maps each `OBDStatus` to a plain-language
  explanation (`diagnostics.py`). Preserve this behavior when editing.
- **`logger.py`** — `run_logger(profile, dir)` polls all signals on an interval,
  one JSON file per poll. Runs offline at the car.
- **`storage.py`** — Azure upload. **Secretless by design**: uses
  `DefaultAzureCredential` (no SAS tokens / account keys anywhere). Azure SDK
  imports are lazy so the at-the-car logger doesn't need the `azure` extra.
- **`cli.py`** — argparse dispatch; each subcommand imports its module lazily.

Snapshots are written to `./obd_snapshots/` (gitignored).

## Conventions / gotchas

- Use `datetime.datetime.now(datetime.UTC)` — not the deprecated `utcnow()`.
- `diagnostics.py` keys its table by `str(OBDStatus.*)` (e.g. `"Not Connected"`,
  `"Car Connected"`), not the enum repr. Detect success via
  `snapshot_summary["ok"]`, not by string-matching the status.
- Hardware is never required for tests — tests fake Pint quantities and use a
  temp `vehicles/` dir. Keep new logic unit-testable without a dongle.
- Never commit `.env`, SAS tokens, account keys, or `.claude/settings.local.json`.
  `.claude/settings.json` (shared) **is** committed; team Skills live in
  `.claude/skills/`.

## Azure auth

`az login` once, then grant your identity **Storage Blob Data Contributor** on
the storage account/container. Same `DefaultAzureCredential` code transparently
uses a managed identity when later run on Azure compute. Set
`AZURE_STORAGE_ACCOUNT_URL` and `AZURE_STORAGE_CONTAINER` (see `.env.example`).

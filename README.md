# obdii-ford-garage

Offline OBD-II capture and logging for a **multi-make garage**, with optional
upload of captures to **Azure Blob Storage**. Built around
[python-OBD](https://python-obd.readthedocs.io/) and an ELM327 dongle.

Two ways to capture:

- **`garage snapshot`** — a one-shot, heavily-instrumented diagnostic. It runs a
  full battery of connection/health checks and writes one JSON file with the data
  *and* the diagnostics. When something doesn't work, the file tells you exactly
  where the chain broke and what to try next.
- **`garage log`** — runs offline at the car, polling every supported signal on a
  fixed interval and writing one timestamped JSON snapshot per poll.

Later, from any machine with internet, **`garage upload`** pushes the saved
snapshots to Azure Blob Storage.

## Requirements

- Python 3.13+ and [uv](https://docs.astral.sh/uv/)
- An ELM327 OBD-II dongle (WiFi or Bluetooth/USB)

## Setup

```bash
uv sync                 # core (at-the-car logging)
uv sync --extra azure   # also installs the Azure upload deps
cp .env.example .env     # then edit; .env is gitignored
```

## Vehicles are configuration, not code

Each car is a TOML file in [`vehicles/`](vehicles/). To add one, copy the
template and edit it:

```bash
cp vehicles/example.toml vehicles/ford-f150-2018.toml
uv run garage vehicles            # list available profiles
```

Keep the real dongle address out of git by setting `OBD_CONNECTION_URL` in `.env`
rather than committing it to the profile.

## Usage

```bash
uv run garage snapshot --vehicle bmw-535xi-2012     # one-shot diagnostic
uv run garage log --vehicle bmw-535xi-2012          # interval logger (Ctrl+C to stop)
uv run garage upload                                # push snapshots to Azure
```

Snapshots are written to `./obd_snapshots/` (gitignored).

## Azure upload — secretless by design

Authentication uses **Microsoft Entra ID** via `DefaultAzureCredential` — there
are **no SAS tokens or account keys** anywhere in this (public) repo.

One-time setup:

```bash
az login
# Grant your identity access to the storage (free; you only pay for storage itself):
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee "$(az ad signed-in-user show --query id -o tsv)" \
  --scope "<your storage account or container resource id>"
```

Then set `AZURE_STORAGE_ACCOUNT_URL` and `AZURE_STORAGE_CONTAINER` in `.env` and
run `uv run garage upload`. On Azure compute later, the same code transparently
uses that resource's **managed identity** instead — no changes needed.

> Cost note: the identity layer (Entra ID, RBAC, managed identity) is free. An
> Azure free account includes 5 GB of blob storage free for 12 months, and JSON
> snapshots are tiny — you can stay at zero cost.

## Development

```bash
uv run ruff check .          # lint
uv run ruff format .         # format
uv run pytest                # tests (no hardware needed)
uv run pre-commit install    # enable git hooks
```

CI (GitHub Actions) runs ruff + pytest on every push and PR.

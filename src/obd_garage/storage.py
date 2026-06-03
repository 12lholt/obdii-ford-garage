"""Azure Blob upload -- secretless, via Entra ID.

Run LATER, from any machine with internet access and the saved snapshot folder.
Authentication uses ``DefaultAzureCredential`` (no SAS tokens, no account keys),
so nothing sensitive is committed to this public repo:

  * On your laptop it falls back to the Azure CLI login -- run ``az login`` once.
  * On Azure compute (Function / Container App) it transparently uses that
    resource's managed identity instead, with no code change.

One-time setup: grant your identity the **Storage Blob Data Contributor** role on
the target container (or account). The identity layer (Entra ID, RBAC, managed
identity) is free; you only pay for the storage itself.

The ``azure`` extra is required:  ``uv sync --extra azure``  (or it's already in
the dev group).
"""

from __future__ import annotations

import os
from pathlib import Path


def upload_snapshots(
    snapshot_dir: Path,
    *,
    account_url: str | None = None,
    container: str | None = None,
    pattern: str = "obd-*.json",
) -> tuple[int, int]:
    """Upload every matching snapshot in ``snapshot_dir`` to Blob storage.

    ``account_url``/``container`` default to the ``AZURE_STORAGE_ACCOUNT_URL`` and
    ``AZURE_STORAGE_CONTAINER`` environment variables. Returns ``(uploaded, failed)``.
    """
    # Imported lazily so the at-the-car logger doesn't need the azure extra installed.
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient

    account_url = account_url or os.environ.get("AZURE_STORAGE_ACCOUNT_URL")
    container = container or os.environ.get("AZURE_STORAGE_CONTAINER")
    if not account_url:
        raise ValueError(
            "Set AZURE_STORAGE_ACCOUNT_URL (e.g. https://<account>.blob.core.windows.net) "
            "or pass account_url."
        )
    if not container:
        raise ValueError("Set AZURE_STORAGE_CONTAINER or pass container.")

    credential = DefaultAzureCredential()
    service = BlobServiceClient(account_url=account_url, credential=credential)
    container_client = service.get_container_client(container)

    files = sorted(snapshot_dir.glob(pattern))
    print(f"Found {len(files)} snapshot(s) to upload to {account_url}/{container}.")

    uploaded, failed = 0, 0
    for path in files:
        try:
            with path.open("rb") as f:
                container_client.upload_blob(name=path.name, data=f, overwrite=True)
            uploaded += 1
            print(f"  uploaded {path.name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAILED   {path.name}: {e}")

    print(f"\nDone. {uploaded} uploaded, {failed} failed.")
    return uploaded, failed

"""``garage`` command-line entry point.

Subcommands:
  garage snapshot --vehicle <slug>   One-shot diagnostic capture -> JSON file.
  garage log --vehicle <slug>        Interval logger (runs offline at the car).
  garage upload                      Push saved snapshots to Azure Blob.
  garage vehicles                    List available vehicle profiles.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import VehicleProfile, list_vehicles

DEFAULT_OUTPUT_DIR = Path("./obd_snapshots")


def _cmd_vehicles(_: argparse.Namespace) -> int:
    slugs = list_vehicles()
    if not slugs:
        print("No vehicle profiles found in vehicles/.")
        return 1
    print("Available vehicles:")
    for slug in slugs:
        print(f"  {slug}")
    return 0


def _cmd_snapshot(args: argparse.Namespace) -> int:
    from .snapshot import take_snapshot

    profile = VehicleProfile.load(args.vehicle)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to {profile.name} at {profile.connection_url} ...")
    report = take_snapshot(profile)

    safe_ts = report["captured_at"].replace(":", "-")
    out_path = output_dir / f"obd-snapshot-{safe_ts}.json"
    out_path.write_text(json.dumps(report, indent=2))

    conn = report["connection"]
    print(f"  Status: {conn.get('status')}  ({conn.get('connect_seconds')}s)")
    print(f"  {conn.get('status_explanation', '')}")
    for s in conn.get("suggestions", []):
        print("    -", s)
    print(f"\nWrote snapshot + diagnostics to: {out_path.resolve()}")

    if conn.get("snapshot_summary", {}).get("ok"):
        n = conn["snapshot_summary"]["ok"]
        print(f"SUCCESS: captured {n} live signals from the car.")
        codes = report.get("check_engine", {}).get("trouble_codes")
        print("Trouble codes found:", codes) if codes else print("No trouble codes returned.")
        return 0

    print("DID NOT REACH 'CAR CONNECTED'. See connection.suggestions in the output file.")
    return 2


def _cmd_log(args: argparse.Namespace) -> int:
    from .logger import run_logger

    profile = VehicleProfile.load(args.vehicle)
    run_logger(profile, Path(args.output_dir))
    return 0


def _cmd_upload(args: argparse.Namespace) -> int:
    from .storage import upload_snapshots

    _uploaded, failed = upload_snapshots(
        Path(args.output_dir),
        account_url=args.account_url,
        container=args.container,
    )
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="garage", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_snap = sub.add_parser("snapshot", help="one-shot diagnostic capture")
    p_snap.add_argument("--vehicle", "-v", required=True, help="vehicle profile slug")
    p_snap.add_argument("--output-dir", "-o", default=str(DEFAULT_OUTPUT_DIR))
    p_snap.set_defaults(func=_cmd_snapshot)

    p_log = sub.add_parser("log", help="interval logger (offline at the car)")
    p_log.add_argument("--vehicle", "-v", required=True, help="vehicle profile slug")
    p_log.add_argument("--output-dir", "-o", default=str(DEFAULT_OUTPUT_DIR))
    p_log.set_defaults(func=_cmd_log)

    p_up = sub.add_parser("upload", help="upload saved snapshots to Azure Blob")
    p_up.add_argument("--output-dir", "-o", default=str(DEFAULT_OUTPUT_DIR))
    p_up.add_argument("--account-url", default=None, help="overrides AZURE_STORAGE_ACCOUNT_URL")
    p_up.add_argument("--container", default=None, help="overrides AZURE_STORAGE_CONTAINER")
    p_up.set_defaults(func=_cmd_upload)

    p_veh = sub.add_parser("vehicles", help="list available vehicle profiles")
    p_veh.set_defaults(func=_cmd_vehicles)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

"""Interval logger -- runs OFFLINE at the car.

Polls every supported signal on a fixed interval and writes one timestamped JSON
snapshot per poll to a local folder. No internet needed while logging; upload to
Azure later with ``garage upload``.
"""

from __future__ import annotations

import datetime
import json
import os
import time
from pathlib import Path
from typing import Any

import obd

from .config import VehicleProfile
from .obd_client import loggable_commands, serialize


def _take_snapshot(connection: obd.OBD, commands: list[obd.OBDCommand]) -> dict[str, Any]:
    snap: dict[str, Any] = {"timestamp": datetime.datetime.now(datetime.UTC).isoformat()}
    for cmd in commands:
        key = cmd.name.lower()
        try:
            resp = connection.query(cmd)
            snap[key] = None if resp.is_null() else serialize(resp.value)
        except Exception as e:  # noqa: BLE001
            snap[key] = f"ERROR: {e}"
    return snap


def _write_local(snap: dict[str, Any], output_dir: Path) -> Path:
    # Colons aren't filename-safe on all OSes, so swap them out.
    safe_ts = snap["timestamp"].replace(":", "-")
    path = output_dir / f"obd-{safe_ts}.json"
    path.write_text(json.dumps(snap, indent=2))
    return path


def run_logger(profile: VehicleProfile, output_dir: Path) -> None:
    """Connect and log snapshots on ``profile.poll_interval`` until Ctrl+C."""
    output_dir.mkdir(parents=True, exist_ok=True)

    connection = obd.OBD(profile.connection_url, check_voltage=profile.check_voltage)
    commands = loggable_commands(connection)

    print(f"Logging {len(commands)} supported signals every {profile.poll_interval}s")
    print("Signals:", ", ".join(c.name for c in commands))
    print(f"Writing snapshots to: {output_dir.resolve()}\n")
    print("Starting logger. Ctrl+C to stop.\n")

    try:
        while True:
            start = time.time()
            snap = _take_snapshot(connection, commands)
            path = _write_local(snap, output_dir)
            print(
                f"[{snap['timestamp']}] saved {os.path.basename(path)}  ({len(snap) - 1} signals)"
            )
            # Hold a steady cadence even if polling took a moment.
            elapsed = time.time() - start
            time.sleep(max(0, profile.poll_interval - elapsed))
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        connection.close()
        print("Connection closed.")

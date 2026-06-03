"""One-shot, heavily-instrumented OBD-II capture.

Connects, runs a full battery of connection/health diagnostics, takes a single
snapshot of every supported signal, and returns one report dict (data +
diagnostics). The goal is to make failures *legible*: when something doesn't
work, the report says exactly where in the chain it broke and what to try next.

Failure modes it explicitly detects (from the python-OBD docs and BMW/ELM327
community forums): unresponsive ELM, unresponsive vehicle, partial connection
(OBDStatus below CAR_CONNECTED), slow-car retries, and flaky WiFi clones.
"""

from __future__ import annotations

import datetime
import logging
import sys
import traceback
from typing import Any

import obd
from obd import OBDStatus

from .config import VehicleProfile
from .diagnostics import diagnose_status
from .obd_client import loggable_commands, query_with_retry, serialize, unit_of


class _ListLogHandler(logging.Handler):
    """Capture python-OBD's verbose AT/OBD handshake log into a list so it lands
    in the report alongside the data -- that log shows the exact line a handshake
    fails on."""

    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


def take_snapshot(profile: VehicleProfile, *, capture_debug_log: bool = True) -> dict[str, Any]:
    """Connect to ``profile``'s vehicle and return a full diagnostic report."""
    debug_handler: _ListLogHandler | None = None
    if capture_debug_log:
        debug_handler = _ListLogHandler()
        debug_handler.setFormatter(logging.Formatter("%(message)s"))
        obd.logger.addHandler(debug_handler)
        obd.logger.setLevel(logging.DEBUG)

    try:
        return _run(profile, debug_handler)
    finally:
        if debug_handler is not None:
            obd.logger.removeHandler(debug_handler)


def _run(profile: VehicleProfile, debug_handler: _ListLogHandler | None) -> dict[str, Any]:
    report: dict[str, Any] = {
        "captured_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "vehicle": profile.name,
        "vehicle_slug": profile.slug,
        "connection_url": profile.connection_url,
        "connection": {},
        "environment": {},
        "signals": {},
        "signal_meta": {},
        "errors": [],
        "debug_log": [],
    }

    try:
        report["environment"] = {
            "python_version": sys.version.split()[0],
            "obd_version": getattr(obd, "__version__", "unknown"),
            "platform": sys.platform,
            "timestamp_local": datetime.datetime.now().isoformat(),
        }
    except Exception as e:  # noqa: BLE001
        report["errors"].append(f"environment capture failed: {e}")

    # --- Connect (timed + diagnosed) ---
    connection: obd.OBD | None = None
    connect_start = _now()
    try:
        connection = obd.OBD(
            profile.connection_url,
            timeout=profile.connect_timeout,
            check_voltage=profile.check_voltage,
        )
    except Exception as e:  # noqa: BLE001
        report["errors"].append(f"OBD() constructor raised: {e}")
        report["connection"]["exception"] = traceback.format_exc()
    connect_elapsed = round(_now() - connect_start, 2)

    if connection is not None:
        status = connection.status()
        explanation, suggestions = diagnose_status(status)
        report["connection"].update(
            {
                "status": str(status),
                "status_explanation": explanation,
                "suggestions": suggestions,
                "is_connected": connection.is_connected(),
                "connect_seconds": connect_elapsed,
                "port_name": connection.port_name(),
                "protocol_id": connection.protocol_id(),
                "protocol_name": connection.protocol_name(),
                "supported_command_count": len(connection.supported_commands),
            }
        )
    else:
        report["connection"].update(
            {
                "status": "NOT_CONNECTED",
                "status_explanation": "Connection object was never created -- the constructor "
                "failed.",
                "connect_seconds": connect_elapsed,
            }
        )

    # --- Snapshot (only if the car is actually talking) ---
    if connection is not None and connection.status() == OBDStatus.CAR_CONNECTED:
        _capture_signals(connection, profile, report)
    else:
        report["connection"]["snapshot_summary"] = {
            "ok": 0,
            "note": "Snapshot skipped -- the car was not fully connected (need CAR_CONNECTED). "
            "See connection.suggestions for how to get there.",
        }

    if debug_handler is not None:
        report["debug_log"] = debug_handler.lines

    if connection is not None:
        try:
            connection.close()
        except Exception as e:  # noqa: BLE001
            report["errors"].append(f"close() raised: {e}")

    return report


def _capture_signals(connection: obd.OBD, profile: VehicleProfile, report: dict[str, Any]) -> None:
    commands = loggable_commands(connection)
    captured, empty, errored = 0, 0, 0

    for cmd in commands:
        key = cmd.name.lower()
        resp, attempts = query_with_retry(
            connection, cmd, retries=profile.query_retries, wait=profile.retry_wait
        )

        if isinstance(resp, tuple) and resp[0] == "ERROR":
            report["signals"][key] = f"ERROR: {resp[1]}"
            report["signal_meta"][key] = {"status": "error", "attempts": attempts + 1}
            errored += 1
            continue

        if resp is None or resp.is_null():
            report["signals"][key] = None
            report["signal_meta"][key] = {
                "status": "no_response",
                "attempts": attempts + 1,
                "note": "Command is marked supported but returned no data. Can happen with "
                "intermittent sensors or a slow ECU.",
            }
            empty += 1
            continue

        report["signals"][key] = serialize(resp.value)
        report["signal_meta"][key] = {
            "status": "ok",
            "attempts": attempts + 1,
            "unit": unit_of(resp.value),
            "command_desc": cmd.desc,
        }
        captured += 1

    report["connection"]["snapshot_summary"] = {
        "ok": captured,
        "no_response": empty,
        "errored": errored,
        "total_attempted": len(commands),
    }

    # Headline: the check-engine picture, pulled out explicitly.
    ce: dict[str, Any] = {}
    signals = report["signals"]
    if "status" in signals:
        ce["mil_status_raw"] = signals["status"]
    if "get_dtc" in signals:
        ce["trouble_codes"] = signals["get_dtc"]
    if "distance_w_mil" in signals:
        ce["distance_with_mil_on"] = signals["distance_w_mil"]
    if "run_time_mil" in signals:
        ce["minutes_with_mil_on"] = signals["run_time_mil"]
    if ce:
        report["check_engine"] = ce


def _now() -> float:
    import time

    return time.time()

"""Shared OBD-II helpers used by both the snapshot and interval-logger flows.

``serialize()`` / ``unit_of()`` were previously copy-pasted into both scripts;
they live here once so there is a single definition of "JSON-safe OBD value."
"""

from __future__ import annotations

import time
from typing import Any

import obd


def serialize(value: Any) -> Any:
    """Turn any python-OBD response value into something JSON-safe."""
    if value is None:
        return None
    if hasattr(value, "magnitude"):  # numeric sensor (Pint quantity)
        return value.magnitude
    if isinstance(value, list):  # GET_DTC etc. -> list of (code, desc)
        return [
            {"code": i[0], "description": i[1]} if isinstance(i, (list, tuple)) else str(i)
            for i in value
        ]
    return str(value)  # STATUS, FUEL_STATUS, FREEZE_DTC, etc.


def unit_of(value: Any) -> str | None:
    """Pull the unit string off a Pint quantity, if present."""
    if value is not None and hasattr(value, "units"):
        return str(value.units)
    return None


def is_loggable(cmd: obd.OBDCommand) -> bool:
    """Skip the bookkeeping PIDs (PIDS_A/B/C, MIDS_*) that only report which
    PIDs exist rather than real sensor data."""
    return not cmd.name.startswith(("PIDS_", "MIDS_"))


def loggable_commands(connection: obd.OBD) -> list[obd.OBDCommand]:
    """Every real, supported signal on this vehicle, sorted by name."""
    return sorted(
        (c for c in connection.supported_commands if is_loggable(c)),
        key=lambda c: c.name,
    )


def query_with_retry(
    connection: obd.OBD,
    cmd: obd.OBDCommand,
    *,
    retries: int = 0,
    wait: float = 5.0,
) -> tuple[Any, int]:
    """Query a command, retrying on empty/null responses (slow-car workaround).

    Returns ``(response_or_error_tuple, attempts_used)``. On exception, the first
    element is ``("ERROR", message)``.
    """
    last_resp = None
    for attempt in range(retries + 1):
        try:
            resp = connection.query(cmd)
            last_resp = resp
            if not resp.is_null():
                return resp, attempt
        except Exception as e:  # noqa: BLE001 - report any driver/serial failure verbatim
            return ("ERROR", str(e)), attempt
        if attempt < retries:
            time.sleep(wait)
    return last_resp, retries

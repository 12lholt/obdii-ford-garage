"""Plain-language explanations for each OBD connection state.

Lifted verbatim from the original snapshot script -- this mapping is the part
that makes failures *legible*, so it is preserved as-is.
"""

from __future__ import annotations

from obd import OBDStatus

_TABLE: dict[str, tuple[str, list[str]]] = {
    str(OBDStatus.NOT_CONNECTED): (
        "NOT CONNECTED -- the script never reached the ELM327 chip at all.",
        [
            "Confirm the laptop is joined to the dongle's WiFi (e.g. WIFI_OBDII).",
            "Confirm the connection URL host/port match the dongle (often 192.168.0.10:35000).",
            "Try `ping 192.168.0.10` from a terminal -- if that fails, it's a network/routing "
            "problem, not the code.",
            "WiFi ELM327 clones are flaky; if it never connects, the adapter may be dead. "
            "A Bluetooth adapter is the more reliable path.",
        ],
    ),
    str(OBDStatus.ELM_CONNECTED): (
        "ELM CONNECTED -- talking to the ELM327 chip, but it is NOT connected to the car.",
        [
            "The 16-pin plug may not be seated fully in the OBD2 port. Re-seat it.",
            "The OBD2 port may not be getting power. Turn the ignition to RUN "
            "(or start the engine).",
            "If your car's port doesn't supply unswitched 12V (or the adapter misreads it), "
            "set check_voltage=False in the VehicleProfile.",
        ],
    ),
    str(OBDStatus.OBD_CONNECTED): (
        "OBD CONNECTED -- plugged into the car, but the IGNITION IS OFF (no vehicle "
        "communication).",
        [
            "Turn the ignition to RUN, or start the engine, then re-run. Live sensor data "
            "requires the car to be powered up.",
        ],
    ),
    str(OBDStatus.CAR_CONNECTED): (
        "CAR CONNECTED -- fully connected. ELM327 + car + ignition all good. This is the "
        "state you want.",
        [],
    ),
}


def diagnose_status(status: object) -> tuple[str, list[str]]:
    """Map an OBDStatus to a plain-language explanation + what to do next."""
    return _TABLE.get(str(status), (f"UNKNOWN STATUS: {status}", []))

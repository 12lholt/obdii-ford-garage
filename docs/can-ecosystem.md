# CAN / OBD-II / diagnostics ecosystem reference

A catalog of the Python libraries in this space, kept as a reference for the
project. The ones available on PyPI are installed via the `diagnostics` optional
extra:

```bash
uv sync --extra diagnostics
```

---

## OBD-II (ELM327-based, works on virtually all 1996+ cars)

- **python-OBD** — standard OBD2 library
- **py-obdii** — newer, actively developed OBD2 library
- **OBDIIPy** — alternative ELM327 diagnostic library

## Raw CAN bus (foundation + decoding)

- **python-can** — base library for raw CAN (SocketCAN, USB-CAN adapters)
- **cantools** — decodes raw CAN frames via DBC files
- **can-isotp** — ISO-TP (ISO 15765-2) transport layer for multi-frame messages
- **aioisotp** — async ISO-TP

## Diagnostics protocols (UDS, deeper than OBD2)

- **udsoncan** — UDS (ISO 14229) client
- **python-uds** — alternative UDS implementation
- **Scapy** — supports CAN/ISOTP/UDS/GMLAN

## DBC / signal definitions

- **opendbc (comma.ai)** — Python car API + huge community DBC file library (275+ models)

## Heavy vehicles (trucks, buses, equipment)

- **python-j1939** — J1939 codec/filtering (PGN)
- **J1939-Framework** — work with J1939 frames

## Testing without a car

- **ELM327-emulator** — simulate an ELM327 + multi-ECU
- **ECU-simulator** — simulate UDS/ISO-TP diagnostic services

## Reference

- **awesome-canbus** (GitHub list) — catalog of essentially everything above

---

## Install resolution notes

How the names above map to actual PyPI packages, and what's installed in the
`diagnostics` extra (all pinned to the versions current as of 2026-06-03):

| Reference name | PyPI package | Installed | Notes |
|---|---|---|---|
| python-OBD | `obd` | 0.7.3 | core dependency (always installed) |
| py-obdii | `py-obdii` | 0.10.2b0 | pre-release; the only published version |
| python-can | `python-can` | 4.6.1 | |
| cantools | `cantools` | 41.4.1 | |
| can-isotp | `can-isotp` | 2.0.7 | |
| udsoncan | `udsoncan` | 1.25.2 | actively maintained UDS client |
| python-uds | `python-uds` | 1.0.2 | unmaintained; emits SyntaxWarnings on 3.13 but imports |
| Scapy | `scapy` | 2.7.0 | |
| opendbc | `opendbc` | 0.3.1 | PyPI release lags comma.ai's GitHub repo; the 275+ DBC files live in the git repo |
| python-j1939 | `can-j1939` | 2.0.12 | "python-j1939" repo publishes as `can-j1939` (import `j1939`) |
| ELM327-emulator | `elm327-emulator` | 3.0.5 | needs a `setuptools<81` build override (see pyproject `[tool.uv.extra-build-dependencies]`) |

**Not on PyPI (GitHub-only — not installed):**

- **OBDIIPy**
- **J1939-Framework**
- **ECU-simulator**

These can be added later as git dependencies if needed.

**Intentionally excluded:**

- **aioisotp** — hard-pins `python-can ~=3.0`, which would hold the whole stack
  on python-can 3.x and cantools 40.x. Dropped in favor of an up-to-date
  python-can; `can-isotp` (maintained) covers the ISO-TP need.

- **awesome-canbus** — a GitHub list, not an installable package.

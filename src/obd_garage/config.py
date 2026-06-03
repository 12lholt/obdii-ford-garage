"""Vehicle profiles -- the multi-make generalization.

A vehicle is *data*, not code. Each car in the garage is a TOML file under
``vehicles/`` describing how to reach its dongle and how to poll it. The
hard-coded "2012 BMW 535xi" constants from the original scripts now live in
``vehicles/bmw-535xi-2012.toml``.

Secrets / environment-specific values (the dongle's address in particular) can be
overridden at runtime via ``OBD_CONNECTION_URL`` so they never have to be
committed to a public repo.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


def vehicles_dir() -> Path:
    """Directory holding vehicle profiles. Overridable via ``GARAGE_VEHICLES_DIR``."""
    env = os.environ.get("GARAGE_VEHICLES_DIR")
    if env:
        return Path(env)
    # Repo layout: <root>/vehicles, with this file at <root>/src/obd_garage/config.py
    return Path(__file__).resolve().parents[2] / "vehicles"


@dataclass(slots=True)
class VehicleProfile:
    """Everything needed to talk to one vehicle."""

    slug: str
    name: str
    connection_url: str | None
    # Logger cadence
    poll_interval: float = 5.0
    # Snapshot/diagnostic behavior
    connect_timeout: float = 30.0
    query_retries: int = 2
    retry_wait: float = 5.0
    check_voltage: bool = True

    @classmethod
    def load(cls, slug: str) -> VehicleProfile:
        """Load ``vehicles/<slug>.toml``, applying env overrides."""
        path = vehicles_dir() / f"{slug}.toml"
        if not path.exists():
            available = ", ".join(p.stem for p in sorted(vehicles_dir().glob("*.toml")))
            raise FileNotFoundError(
                f"No vehicle profile '{slug}' at {path}. Available: {available or '(none)'}"
            )
        return cls.from_dict(slug, tomllib.loads(path.read_text()))

    @classmethod
    def from_dict(cls, slug: str, data: dict) -> VehicleProfile:
        conn = data.get("connection", {})
        polling = data.get("polling", {})
        # OBD_CONNECTION_URL wins so the dongle address stays out of the repo.
        connection_url = os.environ.get("OBD_CONNECTION_URL") or conn.get("url")
        return cls(
            slug=slug,
            name=data.get("name", slug),
            connection_url=connection_url,
            poll_interval=float(polling.get("poll_interval", 5.0)),
            connect_timeout=float(conn.get("connect_timeout", 30.0)),
            query_retries=int(conn.get("query_retries", 2)),
            retry_wait=float(conn.get("retry_wait", 5.0)),
            check_voltage=bool(conn.get("check_voltage", True)),
        )


def list_vehicles() -> list[str]:
    """Slugs of all available vehicle profiles."""
    return [p.stem for p in sorted(vehicles_dir().glob("*.toml"))]

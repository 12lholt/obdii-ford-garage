"""Tests for vehicle profile loading and env overrides."""

from obd_garage.config import VehicleProfile, list_vehicles


def test_from_dict_defaults():
    profile = VehicleProfile.from_dict("x", {"name": "Test Car"})
    assert profile.name == "Test Car"
    assert profile.poll_interval == 5.0
    assert profile.query_retries == 2
    assert profile.check_voltage is True


def test_from_dict_full():
    data = {
        "name": "2018 Ford F-150",
        "connection": {
            "url": "socket://10.0.0.5:35000",
            "connect_timeout": 15,
            "query_retries": 4,
            "retry_wait": 3,
            "check_voltage": False,
        },
        "polling": {"poll_interval": 2},
    }
    profile = VehicleProfile.from_dict("ford-f150-2018", data)
    assert profile.connection_url == "socket://10.0.0.5:35000"
    assert profile.connect_timeout == 15
    assert profile.query_retries == 4
    assert profile.check_voltage is False
    assert profile.poll_interval == 2


def test_env_overrides_connection_url(monkeypatch):
    monkeypatch.setenv("OBD_CONNECTION_URL", "/dev/ttyUSB0")
    profile = VehicleProfile.from_dict("x", {"connection": {"url": "socket://1.2.3.4:35000"}})
    assert profile.connection_url == "/dev/ttyUSB0"


def test_load_from_dir(tmp_path, monkeypatch):
    (tmp_path / "demo.toml").write_text('name = "Demo"\n[connection]\nurl = "x"\n')
    monkeypatch.setenv("GARAGE_VEHICLES_DIR", str(tmp_path))
    monkeypatch.delenv("OBD_CONNECTION_URL", raising=False)
    profile = VehicleProfile.load("demo")
    assert profile.name == "Demo"
    assert profile.connection_url == "x"
    assert list_vehicles() == ["demo"]


def test_load_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("GARAGE_VEHICLES_DIR", str(tmp_path))
    try:
        VehicleProfile.load("nope")
    except FileNotFoundError as e:
        assert "nope" in str(e)
    else:
        raise AssertionError("expected FileNotFoundError")

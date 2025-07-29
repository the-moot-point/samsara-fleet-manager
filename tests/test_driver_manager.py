import os
import sys
import types
import importlib
import csv

# Set required env vars for config validation
os.environ.setdefault("SAMSARA_API_KEY", "dummy")
os.environ.setdefault("EMAIL_FROM", "test@example.com")
os.environ.setdefault("EMAIL_TO", "test@example.com")
os.environ.setdefault("USE_OUTLOOK", "True")


class MockAPI:
    """Simple mock of the Samsara API."""

    def __init__(self, *args, **kwargs):
        self.created = []
        self.updated = []
        self.deactivated = []
        self.drivers = {}

    def find_driver_by_external_id(self, key, payroll_id):
        return self.drivers.get(payroll_id)

    def create_driver(self, data):
        driver_id = f"id{len(self.created) + 1}"
        self.created.append(data)
        return {"id": driver_id, "name": data["name"]}

    def update_driver(self, driver_id, data):
        self.updated.append((driver_id, data))

    def deactivate_driver(self, driver_id, reason):
        self.deactivated.append((driver_id, reason))

    def update_driver_location(self, driver_id, location_tag_id):
        pass


def _install_stubs():
    api_mod = types.ModuleType("samsara_api")
    api_mod.SamsaraAPI = MockAPI
    sys.modules["samsara_api"] = api_mod

    mm_mod = types.ModuleType("mappings_manager")

    class DummyMappingsManager:
        pass

    mm_mod.MappingsManager = DummyMappingsManager
    sys.modules["mappings_manager"] = mm_mod


_install_stubs()

driver_manager = importlib.import_module("driver_manager")


def make_manager(tmp_path):
    api = MockAPI()
    manager = driver_manager.DriverManager(api, data_dir=tmp_path)
    manager._save_username_to_file = lambda u: None
    return manager, api


def test_create_driver_success(tmp_path):
    mgr, api = make_manager(tmp_path)
    row = {
        "name": "Alice",
        "username": "alice1",
        "phone": "123",
        "license_number": "ABC",
        "license_state": "CA",
        "payroll_id": "P123",
        "location_tag_id": "L1",
    }
    mgr._create_driver_from_row(row)

    assert len(api.created) == 1
    assert mgr.operations_log["created"]
    entry = mgr.operations_log["created"][0]
    assert entry["name"] == "Alice"
    assert entry["payroll_id"] == "P123"


def test_create_driver_existing(tmp_path):
    mgr, api = make_manager(tmp_path)
    api.drivers["P123"] = {"id": "existing", "name": "Bob"}

    row = {"name": "Bob", "username": "bob", "payroll_id": "P123"}
    mgr._create_driver_from_row(row)

    assert not api.created
    assert mgr.operations_log["errors"]
    err = mgr.operations_log["errors"][0]
    assert err["row"] == row
    assert err["error"] == "Driver already exists"

def test_process_with_headcount_update_only(tmp_path):
    mgr, api = make_manager(tmp_path)
    api.drivers["P1"] = {"id": "d1", "name": "Old Name", "externalIds": {}}
    hc_map = {
        "P1": {
            "name": "Dana Jones",
            "email": "d1@example.com",
            "phone": "555",
            "location_tag_id": "L1",
        }
    }
    csv_file = tmp_path / "drivers.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "action",
            "payroll_id",
            "name",
            "username",
            "phone",
            "license_number",
            "license_state",
            "location_tag_id",
            "deactivation_reason",
        ])
        writer.writerow(["update", "P1", "", "", "", "", "", "", ""])
    mgr.process_driver_updates_from_csv(str(csv_file), headcount_map=hc_map)
    driver_id, update_data = api.updated[0]
    assert driver_id == "d1"
    assert update_data["phone"] == "555"
    assert update_data["externalIds"]["email"] == "d1@example.com"
    assert update_data["tagIds"] == ["L1"]
    assert update_data["name"] == "Dana Jones"


def test_headcount_not_used_for_create(tmp_path):
    mgr, api = make_manager(tmp_path)
    hc_map = {
        "P1": {
            "name": "Dana Jones",
            "email": "d1@example.com",
            "phone": "555",
            "location_tag_id": "L1",
        }
    }
    csv_file = tmp_path / "drivers.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "action",
            "payroll_id",
            "name",
            "username",
            "phone",
            "license_number",
            "license_state",
            "location_tag_id",
            "deactivation_reason",
        ])
        writer.writerow(["create", "P1", "", "dana", "", "", "", "", ""])
    mgr.process_driver_updates_from_csv(str(csv_file), headcount_map=hc_map)
    # Creation should fail due to missing name
    assert not api.created
    assert mgr.operations_log["errors"]
    err = mgr.operations_log["errors"][0]
    assert err["error"] == "Driver name is required for creation"

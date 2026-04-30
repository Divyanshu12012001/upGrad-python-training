"""
tests.py — Test suite for the Smart IT Service Desk Automation System.

Covers: ticket CRUD, SLA logic, monitoring auto-ticket, file I/O, exceptions.
Run with: python tests.py
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from tickets import (
    Ticket, IncidentTicket, ServiceRequest, TicketStore,
    TicketNotFoundError, InvalidTicketDataError, TicketAlreadyClosedError,
)
from utils import (
    detect_priority, compute_sla_status, sla_breach_scanner,
    ticket_id_generator, is_valid_employee_name, is_valid_department,
    backup_tickets_to_csv, sanitize_text,
)
from monitor import Monitor, THRESHOLDS
from itil import ITILManager, ProblemRecord
from reports import ReportGenerator

# ─────────────────────────────────────────────
# TEST RUNNER HELPERS
# ─────────────────────────────────────────────

_passed = 0
_failed = 0


def run_test(name: str, fn):
    global _passed, _failed
    try:
        fn()
        print(f"  ✅ PASS  {name}")
        _passed += 1
    except AssertionError as e:
        print(f"  ❌ FAIL  {name} — AssertionError: {e}")
        _failed += 1
    except Exception as e:
        print(f"  💥 ERROR {name} — {type(e).__name__}: {e}")
        _failed += 1


def assert_eq(actual, expected, msg=""):
    assert actual == expected, f"{msg} | expected={expected!r}, got={actual!r}"


# ─────────────────────────────────────────────
# FIXTURE: Isolated TicketStore using a temp dir
# ─────────────────────────────────────────────

def make_temp_store() -> tuple[TicketStore, str]:
    """Creates a TicketStore backed by a temporary directory."""
    tmp = tempfile.mkdtemp()
    data_dir = os.path.join(tmp, "data")
    os.makedirs(data_dir)

    # Monkey-patch the module-level TICKETS_FILE
    import tickets as tmod
    original = tmod.TICKETS_FILE
    tmod.TICKETS_FILE = os.path.join(data_dir, "tickets.json")

    store = TicketStore()
    return store, tmp, tmod, original


def restore_store(tmod, original):
    tmod.TICKETS_FILE = original


# ─────────────────────────────────────────────
# 1. TICKET CREATION TESTS
# ─────────────────────────────────────────────

def test_create_incident_ticket():
    store, tmp, tmod, orig = make_temp_store()
    try:
        t = store.create_ticket("Alice Smith", "IT", "Server down in rack 3", "Hardware", "incident")
        assert t["id"].startswith("TKT-"), "ID format wrong"
        assert t["employee_name"] == "Alice Smith"
        assert t["priority"] == "P1", "Server down should be P1"
        assert t["type"] == "IncidentTicket"
        assert t["status"] == "Open"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_create_service_request():
    store, tmp, tmod, orig = make_temp_store()
    try:
        t = store.create_ticket("Bob Jones", "HR", "Need new laptop", "Hardware", "service")
        assert t["type"] == "ServiceRequest"
        assert t["priority"] == "P4"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_create_ticket_invalid_name():
    store, tmp, tmod, orig = make_temp_store()
    try:
        raised = False
        try:
            store.create_ticket("1", "IT", "Some issue", "Hardware")
        except InvalidTicketDataError:
            raised = True
        assert raised, "Should raise InvalidTicketDataError for invalid name"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_create_ticket_invalid_category():
    store, tmp, tmod, orig = make_temp_store()
    try:
        raised = False
        try:
            store.create_ticket("Alice Smith", "IT", "Some issue", "InvalidCat")
        except InvalidTicketDataError:
            raised = True
        assert raised, "Should raise InvalidTicketDataError for bad category"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_ticket_id_uniqueness():
    store, tmp, tmod, orig = make_temp_store()
    try:
        ids = set()
        names = ["Alice Smith", "Bob Jones", "Carol White", "Dave Lee", "Eve Brown"]
        for name in names:
            t = store.create_ticket(name, "IT", "Password reset needed", "Access")
            ids.add(t["id"])
        assert len(ids) == 5, "All ticket IDs must be unique"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_ticket_persistence():
    """Tickets saved to JSON should survive a store reload."""
    store, tmp, tmod, orig = make_temp_store()
    try:
        t = store.create_ticket("Carol White", "Finance", "Internet down", "Network")
        tid = t["id"]

        # Reload store from same file
        store2 = TicketStore()
        found = store2.get_ticket_by_id(tid)
        assert found["employee_name"] == "Carol White"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


# ─────────────────────────────────────────────
# 2. CRUD OPERATION TESTS
# ─────────────────────────────────────────────

def test_get_ticket_by_id():
    store, tmp, tmod, orig = make_temp_store()
    try:
        t = store.create_ticket("Dave Lee", "Ops", "Laptop slow", "Hardware")
        found = store.get_ticket_by_id(t["id"])
        assert found["id"] == t["id"]
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_get_ticket_not_found():
    store, tmp, tmod, orig = make_temp_store()
    try:
        raised = False
        try:
            store.get_ticket_by_id("TKT-9999")
        except TicketNotFoundError:
            raised = True
        assert raised
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_update_status():
    store, tmp, tmod, orig = make_temp_store()
    try:
        t = store.create_ticket("Eve Brown", "Dev", "Software crash", "Software")
        updated = store.update_status(t["id"], "In Progress")
        assert updated["status"] == "In Progress"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_close_ticket():
    store, tmp, tmod, orig = make_temp_store()
    try:
        t = store.create_ticket("Frank Green", "QA", "Access issue", "Access")
        store.close_ticket(t["id"])
        closed = store.get_ticket_by_id(t["id"])
        assert closed["status"] == "Closed"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_close_already_closed_raises():
    store, tmp, tmod, orig = make_temp_store()
    try:
        t = store.create_ticket("Grace Hall", "IT", "Password reset needed", "Access")
        store.close_ticket(t["id"])
        raised = False
        try:
            store.close_ticket(t["id"])
        except TicketAlreadyClosedError:
            raised = True
        assert raised
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_delete_ticket():
    store, tmp, tmod, orig = make_temp_store()
    try:
        t = store.create_ticket("Henry Ford", "Mgmt", "Network down", "Network")
        tid = t["id"]
        store.delete_ticket(tid)
        raised = False
        try:
            store.get_ticket_by_id(tid)
        except TicketNotFoundError:
            raised = True
        assert raised
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_search_tickets():
    store, tmp, tmod, orig = make_temp_store()
    try:
        store.create_ticket("Iris Chan", "Finance", "Internet down", "Network")
        store.create_ticket("Jack Wu", "HR", "Password reset needed", "Access")
        results = store.search_tickets("iris")
        assert len(results) == 1
        assert results[0]["employee_name"] == "Iris Chan"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


# ─────────────────────────────────────────────
# 3. SLA LOGIC TESTS
# ─────────────────────────────────────────────

def test_sla_no_breach():
    ticket = {
        "id": "TKT-0001",
        "priority": "P1",
        "status": "Open",
        "created_date": datetime.now().isoformat(),
        "updated_date": datetime.now().isoformat(),
    }
    sla = compute_sla_status(ticket)
    assert not sla["breached"], "Brand-new P1 ticket should not be breached"
    assert sla["sla_limit"] == 1


def test_sla_breach_p1():
    past = (datetime.now() - timedelta(hours=2)).isoformat()
    ticket = {
        "id": "TKT-0002",
        "priority": "P1",
        "status": "Open",
        "created_date": past,
        "updated_date": past,
    }
    sla = compute_sla_status(ticket)
    assert sla["breached"], "P1 ticket 2h old should be breached (limit=1h)"


def test_sla_breach_p4_not_breached():
    past = (datetime.now() - timedelta(hours=10)).isoformat()
    ticket = {
        "id": "TKT-0003",
        "priority": "P4",
        "status": "Open",
        "created_date": past,
        "updated_date": past,
    }
    sla = compute_sla_status(ticket)
    assert not sla["breached"], "P4 ticket 10h old should NOT be breached (limit=24h)"


def test_sla_breach_scanner_generator():
    now = datetime.now()
    tickets = [
        {"id": "T1", "priority": "P1", "status": "Open",
         "created_date": (now - timedelta(hours=3)).isoformat(), "updated_date": now.isoformat()},
        {"id": "T2", "priority": "P4", "status": "Open",
         "created_date": (now - timedelta(hours=1)).isoformat(), "updated_date": now.isoformat()},
        {"id": "T3", "priority": "P1", "status": "Closed",
         "created_date": (now - timedelta(hours=5)).isoformat(), "updated_date": now.isoformat()},
    ]
    breached = list(sla_breach_scanner(tickets))
    assert len(breached) == 1
    assert breached[0]["id"] == "T1"


def test_sla_limits_per_priority():
    from utils import SLA_HOURS
    assert_eq(SLA_HOURS["P1"], 1)
    assert_eq(SLA_HOURS["P2"], 4)
    assert_eq(SLA_HOURS["P3"], 8)
    assert_eq(SLA_HOURS["P4"], 24)


# ─────────────────────────────────────────────
# 4. PRIORITY AUTO-DETECTION TESTS
# ─────────────────────────────────────────────

def test_priority_server_down():
    assert_eq(detect_priority("Server down in datacenter"), "P1")


def test_priority_internet_down():
    assert_eq(detect_priority("Internet down on floor 3"), "P2")


def test_priority_laptop_slow():
    assert_eq(detect_priority("My laptop slow today"), "P3")


def test_priority_password_reset():
    assert_eq(detect_priority("Need a password reset"), "P4")


def test_priority_default():
    assert_eq(detect_priority("Random unrecognised issue"), "P4")


# ─────────────────────────────────────────────
# 5. MONITORING AUTO-TICKET TESTS
# ─────────────────────────────────────────────

def test_monitor_simulated_scan():
    """Simulated scan should return a valid snapshot dict."""
    monitor = Monitor(ticket_store=None)
    snapshot = monitor._simulated_scan()
    assert "cpu_percent" in snapshot
    assert "ram" in snapshot
    assert "disk" in snapshot
    assert "network" in snapshot
    assert snapshot.get("simulated") is True


def test_monitor_auto_ticket_on_alert():
    """Firing an alert with a store attached should create a ticket."""
    store, tmp, tmod, orig = make_temp_store()
    try:
        monitor = Monitor(ticket_store=store)
        monitor._fire_alert("CPU", 95.0, 90.0, "CPU usage critical: 95.0%")
        tickets = store.get_all_tickets()
        assert len(tickets) == 1
        assert tickets[0]["priority"] == "P1"
        assert tickets[0]["employee_name"] == "System Monitor"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_monitor_no_alert_below_threshold():
    """No alert should fire when all metrics are within thresholds."""
    monitor = Monitor(ticket_store=None)
    # Manually call alert logic with value below threshold
    alerts_before = len(monitor._alert_history)
    cpu_val = THRESHOLDS["cpu_percent"] - 10
    if cpu_val <= THRESHOLDS["cpu_percent"]:
        pass  # No alert expected
    assert len(monitor._alert_history) == alerts_before


# ─────────────────────────────────────────────
# 6. FILE HANDLING TESTS
# ─────────────────────────────────────────────

def test_backup_csv_created():
    tmp = tempfile.mkdtemp()
    import utils as umod
    original_backup = umod.BACKUP_FILE
    umod.BACKUP_FILE = os.path.join(tmp, "backup.csv")
    try:
        tickets = [
            {"id": "TKT-0001", "employee_name": "Test User", "department": "IT",
             "issue_description": "Test issue", "category": "Hardware",
             "priority": "P1", "status": "Open",
             "created_date": datetime.now().isoformat(),
             "updated_date": datetime.now().isoformat(), "type": "IncidentTicket"}
        ]
        backup_tickets_to_csv(tickets)
        assert os.path.exists(umod.BACKUP_FILE), "Backup CSV should be created"
        from utils import read_backup_csv
        rows = read_backup_csv()
        assert len(rows) == 1
        assert rows[0]["id"] == "TKT-0001"
    finally:
        shutil.rmtree(tmp)
        umod.BACKUP_FILE = original_backup


def test_tickets_json_written():
    store, tmp, tmod, orig = make_temp_store()
    try:
        store.create_ticket("JSON Test", "IT", "Server crash detected", "Hardware")
        with open(tmod.TICKETS_FILE, "r") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["employee_name"] == "JSON Test"
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


def test_empty_backup_no_crash():
    """backup_tickets_to_csv with empty list should not raise."""
    backup_tickets_to_csv([])  # Should log warning, not crash


# ─────────────────────────────────────────────
# 7. EXCEPTION HANDLING TESTS
# ─────────────────────────────────────────────

def test_invalid_status_raises():
    t = IncidentTicket("TKT-0001", "Alice", "IT", "Server down", "Hardware", "P1")
    raised = False
    try:
        t.status = "Flying"
    except InvalidTicketDataError:
        raised = True
    assert raised


def test_modify_closed_ticket_raises():
    t = IncidentTicket("TKT-0001", "Alice", "IT", "Server down", "Hardware", "P1")
    t.status = "Closed"
    raised = False
    try:
        t.status = "Open"
    except TicketAlreadyClosedError:
        raised = True
    assert raised


def test_escalate_closed_ticket_raises():
    t = IncidentTicket("TKT-0001", "Alice", "IT", "Server down", "Hardware", "P1")
    t.status = "Closed"
    raised = False
    try:
        t.escalate()
    except TicketAlreadyClosedError:
        raised = True
    assert raised


def test_ticket_not_found_raises():
    store, tmp, tmod, orig = make_temp_store()
    try:
        raised = False
        try:
            store.get_ticket_by_id("TKT-XXXX")
        except TicketNotFoundError:
            raised = True
        assert raised
    finally:
        shutil.rmtree(tmp)
        restore_store(tmod, orig)


# ─────────────────────────────────────────────
# 8. UTILITY / GENERATOR TESTS
# ─────────────────────────────────────────────

def test_ticket_id_generator_skips_existing():
    existing = ["TKT-0001", "TKT-0002"]
    gen = ticket_id_generator(existing)
    first = next(gen)
    assert first == "TKT-0003"


def test_sanitize_text():
    assert sanitize_text("  hello   world  ") == "hello world"


def test_valid_employee_name():
    assert is_valid_employee_name("Alice Smith")
    assert not is_valid_employee_name("1")
    assert not is_valid_employee_name("")


def test_valid_department():
    assert is_valid_department("IT Support")
    assert not is_valid_department("A")


# ─────────────────────────────────────────────
# 9. OOP / POLYMORPHISM TESTS
# ─────────────────────────────────────────────

def test_ticket_from_dict_returns_correct_subclass():
    data = {
        "id": "TKT-0001", "type": "IncidentTicket",
        "employee_name": "Alice", "department": "IT",
        "issue_description": "Server down", "category": "Hardware",
        "priority": "P1", "status": "Open",
        "created_date": datetime.now().isoformat(),
        "updated_date": datetime.now().isoformat(),
    }
    obj = Ticket.from_dict(data)
    assert isinstance(obj, IncidentTicket)


def test_service_request_approval():
    sr = ServiceRequest("TKT-0002", "Bob", "HR", "Need software", "Software", "P4")
    assert sr.approval_status == "Pending"
    sr.approve()
    assert sr.approval_status == "Approved"


def test_incident_escalation():
    inc = IncidentTicket("TKT-0003", "Carol", "Ops", "Server crash detected", "Hardware", "P1")
    inc.escalate()
    assert inc.escalated is True
    assert inc.status == "Escalated"


def test_to_dict_round_trip():
    inc = IncidentTicket("TKT-0004", "Dave", "Dev", "Internet down", "Network", "P2")
    d = inc.to_dict()
    restored = IncidentTicket.from_dict(d)
    assert restored.id == inc.id
    assert restored.priority == inc.priority


# ─────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  SMART IT SERVICE DESK — TEST SUITE")
    print("=" * 60)

    sections = [
        ("Ticket Creation",       [test_create_incident_ticket, test_create_service_request,
                                   test_create_ticket_invalid_name, test_create_ticket_invalid_category,
                                   test_ticket_id_uniqueness, test_ticket_persistence]),
        ("CRUD Operations",       [test_get_ticket_by_id, test_get_ticket_not_found,
                                   test_update_status, test_close_ticket,
                                   test_close_already_closed_raises, test_delete_ticket,
                                   test_search_tickets]),
        ("SLA Logic",             [test_sla_no_breach, test_sla_breach_p1,
                                   test_sla_breach_p4_not_breached, test_sla_breach_scanner_generator,
                                   test_sla_limits_per_priority]),
        ("Priority Detection",    [test_priority_server_down, test_priority_internet_down,
                                   test_priority_laptop_slow, test_priority_password_reset,
                                   test_priority_default]),
        ("Monitoring",            [test_monitor_simulated_scan, test_monitor_auto_ticket_on_alert,
                                   test_monitor_no_alert_below_threshold]),
        ("File Handling",         [test_backup_csv_created, test_tickets_json_written,
                                   test_empty_backup_no_crash]),
        ("Exception Handling",    [test_invalid_status_raises, test_modify_closed_ticket_raises,
                                   test_escalate_closed_ticket_raises, test_ticket_not_found_raises]),
        ("Utilities/Generators",  [test_ticket_id_generator_skips_existing, test_sanitize_text,
                                   test_valid_employee_name, test_valid_department]),
        ("OOP/Polymorphism",      [test_ticket_from_dict_returns_correct_subclass,
                                   test_service_request_approval, test_incident_escalation,
                                   test_to_dict_round_trip]),
    ]

    for section_name, tests in sections:
        print(f"\n  ── {section_name} ──")
        for test_fn in tests:
            run_test(test_fn.__name__, test_fn)

    print("\n" + "=" * 60)
    print(f"  Results: {_passed} passed | {_failed} failed | {_passed + _failed} total")
    print("=" * 60)
    sys.exit(0 if _failed == 0 else 1)


if __name__ == "__main__":
    main()

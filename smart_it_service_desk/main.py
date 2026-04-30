"""
main.py — CLI entry point for the Smart IT Service Desk Automation System.

Menu structure:
  1. Ticket Management
  2. ITIL Processes
  3. System Monitor
  4. Reports
  5. Backup & Restore
  0. Exit
"""

import sys
import os

# Ensure project root is on the path when running from any directory
sys.path.insert(0, os.path.dirname(__file__))

from tickets import TicketStore, TicketNotFoundError, InvalidTicketDataError, TicketAlreadyClosedError
from monitor import Monitor
from reports import ReportGenerator
from itil import ITILManager
from utils import (
    print_header, print_separator, TICKET_CATEGORIES,
    format_ticket_row, priority_color_label,
)
from logger import get_logger

log = get_logger("main")


# ─────────────────────────────────────────────
# INPUT HELPERS
# ─────────────────────────────────────────────

def prompt(label: str, required: bool = True) -> str:
    """Prompts user for input, re-prompts if required and blank."""
    while True:
        val = input(f"  {label}: ").strip()
        if val or not required:
            return val
        print("  ⚠  This field is required.")


def choose(label: str, options: tuple | list, allow_blank: bool = False) -> str:
    """Displays a numbered menu and returns the chosen value."""
    print(f"\n  {label}")
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    while True:
        raw = input("  Choice: ").strip()
        if allow_blank and raw == "":
            return ""
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"  ⚠  Enter a number between 1 and {len(options)}.")


def confirm(message: str) -> bool:
    return input(f"  {message} (y/n): ").strip().lower() == "y"


# ─────────────────────────────────────────────
# TICKET MANAGEMENT MENU
# ─────────────────────────────────────────────

def menu_tickets(store: TicketStore) -> None:
    while True:
        print_header("TICKET MANAGEMENT")
        print("  1. Create Ticket")
        print("  2. View All Tickets")
        print("  3. Search Ticket")
        print("  4. View Ticket Details")
        print("  5. Update Ticket Status")
        print("  6. Close Ticket")
        print("  7. Delete Ticket")
        print("  8. Escalate Ticket")
        print("  9. Check SLA Breaches")
        print("  0. Back")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            _create_ticket(store)
        elif choice == "2":
            _view_all(store)
        elif choice == "3":
            _search(store)
        elif choice == "4":
            _view_detail(store)
        elif choice == "5":
            _update_status(store)
        elif choice == "6":
            _close_ticket(store)
        elif choice == "7":
            _delete_ticket(store)
        elif choice == "8":
            _escalate(store)
        elif choice == "9":
            _check_sla(store)
        elif choice == "0":
            break
        else:
            print("  ⚠  Invalid choice.")


def _create_ticket(store: TicketStore) -> None:
    print_header("CREATE NEW TICKET")
    try:
        ticket_type = choose("Ticket Type", ["Incident", "Service Request"])
        employee    = prompt("Employee Name")
        department  = prompt("Department")
        issue       = prompt("Issue Description")
        category    = choose("Category", list(TICKET_CATEGORIES))
        use_auto    = confirm("Auto-detect priority from description?")
        priority    = None
        if not use_auto:
            priority = choose("Priority", ["P1", "P2", "P3", "P4"])

        t_type = "incident" if ticket_type == "Incident" else "service"
        ticket = store.create_ticket(
            employee_name=employee,
            department=department,
            issue_description=issue,
            category=category,
            ticket_type=t_type,
            priority=priority,
        )
        print(f"\n  ✅ Ticket created: {ticket['id']} | {priority_color_label(ticket['priority'])}")
    except (InvalidTicketDataError, ValueError) as e:
        print(f"\n  ❌ Validation error: {e}")
    except Exception as e:
        log.error(f"Unexpected error creating ticket: {e}")
        print(f"\n  ❌ Error: {e}")


def _view_all(store: TicketStore) -> None:
    tickets = store.get_all_tickets()
    print_header(f"ALL TICKETS ({len(tickets)})")
    if not tickets:
        print("  No tickets found.")
        return
    for t in tickets:
        print(f"  {format_ticket_row(t)}")
    print_separator()


def _search(store: TicketStore) -> None:
    kw = prompt("Search keyword (ID / name / dept / issue)")
    results = store.search_tickets(kw)
    print(f"\n  Found {len(results)} result(s):")
    for t in results:
        print(f"  {format_ticket_row(t)}")


def _view_detail(store: TicketStore) -> None:
    tid = prompt("Ticket ID")
    try:
        from tickets import Ticket
        t = store.get_ticket_by_id(tid)
        Ticket.from_dict(t).display()
    except TicketNotFoundError as e:
        print(f"\n  ❌ {e}")


def _update_status(store: TicketStore) -> None:
    tid = prompt("Ticket ID")
    from utils import VALID_STATUSES
    new_status = choose("New Status", list(VALID_STATUSES))
    try:
        store.update_status(tid, new_status)
        print(f"\n  ✅ Status updated → {new_status}")
    except (TicketNotFoundError, TicketAlreadyClosedError, InvalidTicketDataError) as e:
        print(f"\n  ❌ {e}")


def _close_ticket(store: TicketStore) -> None:
    tid = prompt("Ticket ID to close")
    try:
        store.close_ticket(tid)
        print(f"\n  ✅ Ticket {tid} closed.")
    except (TicketNotFoundError, TicketAlreadyClosedError) as e:
        print(f"\n  ❌ {e}")


def _delete_ticket(store: TicketStore) -> None:
    tid = prompt("Ticket ID to delete")
    if confirm(f"Permanently delete {tid}?"):
        try:
            store.delete_ticket(tid)
            print(f"\n  ✅ Ticket {tid} deleted.")
        except TicketNotFoundError as e:
            print(f"\n  ❌ {e}")


def _escalate(store: TicketStore) -> None:
    tid = prompt("Ticket ID to escalate")
    try:
        store.escalate_ticket(tid)
        print(f"\n  ✅ Ticket {tid} escalated.")
    except (TicketNotFoundError, InvalidTicketDataError, TicketAlreadyClosedError) as e:
        print(f"\n  ❌ {e}")


def _check_sla(store: TicketStore) -> None:
    breached = store.check_and_escalate_sla_breaches()
    if breached:
        print(f"\n  ⚠  {len(breached)} SLA breach(es) detected and processed.")
        for t in breached:
            print(f"    [{t['id']}] {t['employee_name']} | {t['priority']}")
    else:
        print("\n  ✅ No SLA breaches detected.")


# ─────────────────────────────────────────────
# ITIL MENU
# ─────────────────────────────────────────────

def menu_itil(itil: ITILManager) -> None:
    while True:
        print_header("ITIL PROCESSES")
        print("  1. Log Incident")
        print("  2. Log Service Request")
        print("  3. View Problem Records")
        print("  4. Create Change Request")
        print("  5. View Change Records")
        print("  6. Update Change State")
        print("  7. SLA Dashboard")
        print("  0. Back")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            _log_incident(itil)
        elif choice == "2":
            _log_service_request(itil)
        elif choice == "3":
            itil.display_problems()
        elif choice == "4":
            _create_change(itil)
        elif choice == "5":
            itil.display_changes()
        elif choice == "6":
            _update_change(itil)
        elif choice == "7":
            itil.sla_dashboard()
        elif choice == "0":
            break
        else:
            print("  ⚠  Invalid choice.")


def _log_incident(itil: ITILManager) -> None:
    print_header("LOG INCIDENT")
    try:
        employee   = prompt("Employee Name")
        department = prompt("Department")
        issue      = prompt("Issue Description")
        category   = choose("Category", list(TICKET_CATEGORIES))
        ticket = itil.handle_incident(employee, department, issue, category)
        print(f"\n  ✅ Incident logged: {ticket['id']} | {priority_color_label(ticket['priority'])}")
    except Exception as e:
        print(f"\n  ❌ {e}")


def _log_service_request(itil: ITILManager) -> None:
    print_header("LOG SERVICE REQUEST")
    try:
        employee   = prompt("Employee Name")
        department = prompt("Department")
        issue      = prompt("Request Description")
        category   = choose("Category", list(TICKET_CATEGORIES))
        ticket = itil.handle_service_request(employee, department, issue, category)
        print(f"\n  ✅ Service request logged: {ticket['id']}")
    except Exception as e:
        print(f"\n  ❌ {e}")


def _create_change(itil: ITILManager) -> None:
    print_header("CREATE CHANGE REQUEST")
    try:
        from itil import ChangeRecord
        title       = prompt("Change Title")
        description = prompt("Description")
        change_type = choose("Change Type", list(ChangeRecord.CHANGE_TYPES))
        requested   = prompt("Requested By")
        chg = itil.create_change_request(title, description, change_type, requested)
        print(f"\n  ✅ Change request created: {chg['change_id']} | {change_type}")
    except Exception as e:
        print(f"\n  ❌ {e}")


def _update_change(itil: ITILManager) -> None:
    from itil import ChangeRecord
    cid       = prompt("Change ID")
    new_state = choose("New State", list(ChangeRecord.CHANGE_STATES))
    try:
        itil.update_change_state(cid, new_state)
        print(f"\n  ✅ Change {cid} → {new_state}")
    except (KeyError, ValueError) as e:
        print(f"\n  ❌ {e}")


# ─────────────────────────────────────────────
# MONITOR MENU
# ─────────────────────────────────────────────

def menu_monitor(monitor: Monitor) -> None:
    while True:
        print_header("SYSTEM MONITOR")
        print("  1. Run Single Scan")
        print("  2. Continuous Monitor (5 cycles)")
        print("  3. View Alert History")
        print("  0. Back")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            snapshot = monitor.run_scan()
            monitor.display_snapshot(snapshot)
        elif choice == "2":
            monitor.continuous_monitor(interval_seconds=5, max_cycles=5)
        elif choice == "3":
            history = monitor.get_alert_history()
            if history:
                print_header(f"ALERT HISTORY ({len(history)} alerts)")
                for a in history:
                    print(f"  [{a['timestamp']}] {a['resource']} | {a['message']}")
            else:
                print("\n  No alerts in this session.")
        elif choice == "0":
            break
        else:
            print("  ⚠  Invalid choice.")


# ─────────────────────────────────────────────
# REPORTS MENU
# ─────────────────────────────────────────────

def menu_reports(reporter: ReportGenerator) -> None:
    while True:
        print_header("REPORTS")
        print("  1. Daily Report")
        print("  2. Monthly Report")
        print("  3. All Tickets Table")
        print("  4. Export Daily Report to File")
        print("  5. Export Monthly Report to File")
        print("  0. Back")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            reporter.daily_report()
        elif choice == "2":
            reporter.monthly_report()
        elif choice == "3":
            reporter.print_all_tickets_table()
        elif choice == "4":
            reporter.export_report_to_txt("daily")
        elif choice == "5":
            reporter.export_report_to_txt("monthly")
        elif choice == "0":
            break
        else:
            print("  ⚠  Invalid choice.")


# ─────────────────────────────────────────────
# BACKUP MENU
# ─────────────────────────────────────────────

def menu_backup(store: TicketStore) -> None:
    print_header("BACKUP & RESTORE")
    print("  1. Backup tickets to CSV")
    print("  2. View CSV backup contents")
    print("  0. Back")
    choice = input("\n  Select: ").strip()

    if choice == "1":
        store.backup()
        print("\n  ✅ Backup complete → data/backup.csv")
    elif choice == "2":
        from utils import read_backup_csv
        rows = read_backup_csv()
        if rows:
            print(f"\n  {len(rows)} records in backup:")
            for r in rows:
                print(f"  {r.get('id')} | {r.get('employee_name')} | {r.get('status')}")
        else:
            print("\n  No backup found. Run a backup first.")


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def main() -> None:
    """Initialises all components and runs the main CLI loop."""
    print_header("🖥  SMART IT SERVICE DESK AUTOMATION SYSTEM")
    print("  Initialising components...")

    store    = TicketStore()
    monitor  = Monitor(ticket_store=store)
    itil     = ITILManager(ticket_store=store)
    reporter = ReportGenerator(ticket_store=store, itil_manager=itil)

    print("  ✅ System ready.\n")

    while True:
        print_header("MAIN MENU")
        print("  1. 🎫  Ticket Management")
        print("  2. 📋  ITIL Processes")
        print("  3. 📡  System Monitor")
        print("  4. 📊  Reports")
        print("  5. 💾  Backup & Restore")
        print("  0. 🚪  Exit")
        choice = input("\n  Select: ").strip()

        if choice == "1":
            menu_tickets(store)
        elif choice == "2":
            menu_itil(itil)
        elif choice == "3":
            menu_monitor(monitor)
        elif choice == "4":
            menu_reports(reporter)
        elif choice == "5":
            menu_backup(store)
        elif choice == "0":
            if confirm("Exit the system?"):
                print("\n  👋 Goodbye. All data saved.\n")
                sys.exit(0)
        else:
            print("  ⚠  Invalid choice. Enter 0–5.")


if __name__ == "__main__":
    main()

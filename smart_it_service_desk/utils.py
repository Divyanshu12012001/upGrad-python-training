"""
utils.py — Shared utilities: decorators, generators, regex validators, helpers.
Used across all modules to avoid code duplication.
"""

import re
import time
import functools
import csv
import os
from datetime import datetime
from typing import Generator, Any

from logger import get_logger

log = get_logger("utils")

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

# SLA resolution time in hours per priority
SLA_HOURS: dict[str, int] = {
    "P1": 1,
    "P2": 4,
    "P3": 8,
    "P4": 24,
}

# Keyword → priority mapping for auto-classification
PRIORITY_RULES: dict[str, str] = {
    "server down":     "P1",
    "server crash":    "P1",
    "internet down":   "P2",
    "network down":    "P2",
    "laptop slow":     "P3",
    "system slow":     "P3",
    "password reset":  "P4",
    "password change": "P4",
}

TICKET_CATEGORIES = ("Hardware", "Software", "Network", "Security", "Access", "Other")
VALID_STATUSES    = ("Open", "In Progress", "Resolved", "Closed", "Escalated")
BACKUP_FILE       = os.path.join(os.path.dirname(__file__), "data", "backup.csv")


# ─────────────────────────────────────────────
# DECORATORS
# ─────────────────────────────────────────────

def log_action(func):
    """
    Decorator — logs function entry/exit with elapsed time.
    Catches and re-raises exceptions after logging them as ERROR.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        log.info(f"CALL  → {func.__qualname__}()")
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            log.info(f"DONE  ← {func.__qualname__}() [{elapsed:.1f}ms]")
            return result
        except Exception as exc:
            log.error(f"ERROR in {func.__qualname__}(): {exc}")
            raise
    return wrapper


def validate_input(func):
    """
    Decorator — strips and checks that string arguments are non-empty.
    Raises ValueError for blank required fields.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for i, arg in enumerate(args):
            if isinstance(arg, str) and arg.strip() == "":
                raise ValueError(f"Argument {i} passed to {func.__name__}() must not be empty.")
        return func(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
# GENERATORS
# ─────────────────────────────────────────────

def ticket_id_generator(existing_ids: list[str]) -> Generator[str, None, None]:
    """
    Infinite generator that yields the next unique ticket ID.
    Format: TKT-0001, TKT-0002, …
    Skips IDs already present in existing_ids.
    """
    counter = 1
    while True:
        tid = f"TKT-{counter:04d}"
        if tid not in existing_ids:
            yield tid
        counter += 1


def sla_breach_scanner(tickets: list[dict]) -> Generator[dict, None, None]:
    """
    Generator — lazily yields only tickets that have breached their SLA.
    A ticket breaches SLA when it is still open/in-progress past the SLA window.
    """
    now = datetime.now()
    for ticket in tickets:
        if ticket.get("status") in ("Closed", "Resolved"):
            continue
        created = datetime.fromisoformat(ticket["created_date"])
        sla_hrs  = SLA_HOURS.get(ticket.get("priority", "P4"), 24)
        elapsed  = (now - created).total_seconds() / 3600
        if elapsed > sla_hrs:
            yield ticket


def open_tickets_generator(tickets: list[dict]) -> Generator[dict, None, None]:
    """Generator — yields tickets that are not yet closed or resolved."""
    for t in tickets:
        if t.get("status") not in ("Closed", "Resolved"):
            yield t


# ─────────────────────────────────────────────
# REGEX VALIDATORS
# ─────────────────────────────────────────────

def is_valid_employee_name(name: str) -> bool:
    """Allows letters, spaces, dots, hyphens — min 2 chars."""
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z\s.\-]{1,48}", name.strip()))


def is_valid_department(dept: str) -> bool:
    """Alphanumeric department name, 2–40 chars."""
    return bool(re.fullmatch(r"[A-Za-z0-9\s&\-]{2,40}", dept.strip()))


def sanitize_text(text: str) -> str:
    """Strips leading/trailing whitespace and collapses internal spaces."""
    return re.sub(r"\s+", " ", text.strip())


# ─────────────────────────────────────────────
# PRIORITY AUTO-DETECTION
# ─────────────────────────────────────────────

def detect_priority(description: str) -> str:
    """
    Scans issue description against PRIORITY_RULES keywords (case-insensitive).
    Returns matched priority or 'P4' as default.
    """
    desc_lower = description.lower()
    for keyword, priority in PRIORITY_RULES.items():
        if keyword in desc_lower:
            log.info(f"Auto-priority '{priority}' matched keyword '{keyword}'")
            return priority
    return "P4"


# ─────────────────────────────────────────────
# SLA HELPERS
# ─────────────────────────────────────────────

def compute_sla_status(ticket: dict) -> dict:
    """
    Returns a dict with:
      elapsed_hours, sla_limit, breached (bool), remaining_hours
    """
    now     = datetime.now()
    created = datetime.fromisoformat(ticket["created_date"])
    elapsed = (now - created).total_seconds() / 3600
    limit   = SLA_HOURS.get(ticket.get("priority", "P4"), 24)
    return {
        "elapsed_hours":   round(elapsed, 2),
        "sla_limit":       limit,
        "breached":        elapsed > limit,
        "remaining_hours": round(max(limit - elapsed, 0), 2),
    }


# ─────────────────────────────────────────────
# CSV BACKUP
# ─────────────────────────────────────────────

@log_action
def backup_tickets_to_csv(tickets: list[dict]) -> None:
    """
    Writes all tickets to data/backup.csv.
    Creates the file with headers if it doesn't exist.
    """
    if not tickets:
        log.warning("backup_tickets_to_csv: no tickets to back up.")
        return

    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    fieldnames = list(tickets[0].keys())

    with open(BACKUP_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tickets)

    log.info(f"Backed up {len(tickets)} tickets → {BACKUP_FILE}")


def read_backup_csv() -> list[dict]:
    """Reads backup.csv and returns list of ticket dicts."""
    if not os.path.exists(BACKUP_FILE):
        return []
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ─────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────

def print_separator(char: str = "─", width: int = 70) -> None:
    print(char * width)


def print_header(title: str) -> None:
    print_separator("═")
    print(f"  {title}")
    print_separator("═")


def format_ticket_row(ticket: dict) -> str:
    """Returns a single-line summary string for a ticket."""
    sla = compute_sla_status(ticket)
    breach_flag = " ⚠ SLA BREACH" if sla["breached"] else ""
    return (
        f"[{ticket['id']}] {ticket['employee_name']:<20} "
        f"| {ticket['priority']} | {ticket['status']:<12} "
        f"| {ticket['category']:<10} | {ticket['department']}{breach_flag}"
    )


def priority_color_label(priority: str) -> str:
    """Returns a visual label for priority (CLI-friendly)."""
    labels = {"P1": "🔴 P1-CRITICAL", "P2": "🟠 P2-HIGH", "P3": "🟡 P3-MEDIUM", "P4": "🟢 P4-LOW"}
    return labels.get(priority, priority)

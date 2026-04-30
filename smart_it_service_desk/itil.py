"""
itil.py — ITIL process implementations:
  - Incident Management
  - Service Request Management
  - Problem Management (auto-create if issue repeats 5+ times)
  - Change Management (basic tracking)
  - SLA Tracking
"""

import json
import os
import re
from datetime import datetime
from typing import Optional

from logger import get_logger
from utils import log_action, print_separator, print_header, SLA_HOURS, compute_sla_status

log = get_logger("itil")

PROBLEMS_FILE = os.path.join(os.path.dirname(__file__), "data", "problems.json")
PROBLEM_THRESHOLD = 5   # Number of similar incidents before a Problem Record is raised


# ─────────────────────────────────────────────
# PROBLEM RECORD CLASS
# ─────────────────────────────────────────────

class ProblemRecord:
    """
    Represents an ITIL Problem — the root cause behind recurring incidents.
    Auto-created when the same issue description pattern repeats >= PROBLEM_THRESHOLD times.
    """

    def __init__(
        self,
        problem_id: str,
        pattern: str,
        linked_ticket_ids: list[str],
        status: str = "Open",
        root_cause: str = "",
        workaround: str = "",
        created_date: Optional[str] = None,
    ):
        self.problem_id        = problem_id
        self.pattern           = pattern
        self.linked_ticket_ids = linked_ticket_ids
        self.status            = status
        self.root_cause        = root_cause
        self.workaround        = workaround
        self.created_date      = created_date or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "problem_id":        self.problem_id,
            "pattern":           self.pattern,
            "linked_ticket_ids": self.linked_ticket_ids,
            "status":            self.status,
            "root_cause":        self.root_cause,
            "workaround":        self.workaround,
            "created_date":      self.created_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProblemRecord":
        return cls(**data)

    def display(self) -> None:
        print_separator()
        print(f"  Problem ID  : {self.problem_id}")
        print(f"  Pattern     : {self.pattern}")
        print(f"  Status      : {self.status}")
        print(f"  Root Cause  : {self.root_cause or 'Under Investigation'}")
        print(f"  Workaround  : {self.workaround or 'None documented'}")
        print(f"  Linked Tkts : {', '.join(self.linked_ticket_ids)}")
        print(f"  Created     : {self.created_date}")
        print_separator()


# ─────────────────────────────────────────────
# CHANGE RECORD
# ─────────────────────────────────────────────

class ChangeRecord:
    """Basic ITIL Change Management record."""

    CHANGE_TYPES = ("Standard", "Normal", "Emergency")
    CHANGE_STATES = ("Requested", "Approved", "Scheduled", "Implemented", "Closed", "Rejected")

    def __init__(
        self,
        change_id: str,
        title: str,
        description: str,
        change_type: str,
        requested_by: str,
        state: str = "Requested",
        created_date: Optional[str] = None,
    ):
        self.change_id    = change_id
        self.title        = title
        self.description  = description
        self.change_type  = change_type
        self.requested_by = requested_by
        self.state        = state
        self.created_date = created_date or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return self.__dict__

    @classmethod
    def from_dict(cls, data: dict) -> "ChangeRecord":
        return cls(**data)


# ─────────────────────────────────────────────
# ITIL MANAGER
# ─────────────────────────────────────────────

class ITILManager:
    """
    Central ITIL process coordinator.
    Wraps TicketStore and adds Problem + Change management layers.
    """

    def __init__(self, ticket_store):
        self._store          = ticket_store
        self._problems: list[dict] = []
        self._changes:  list[dict] = []
        self._load_problems()

    # ── Persistence ──────────────────────────────

    def _load_problems(self) -> None:
        os.makedirs(os.path.dirname(PROBLEMS_FILE), exist_ok=True)
        if not os.path.exists(PROBLEMS_FILE):
            self._problems = []
            return
        try:
            with open(PROBLEMS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._problems = data.get("problems", [])
                self._changes  = data.get("changes", [])
        except (json.JSONDecodeError, OSError) as e:
            log.error(f"Failed to load problems.json: {e}")
            self._problems, self._changes = [], []

    def _save_problems(self) -> None:
        try:
            with open(PROBLEMS_FILE, "w", encoding="utf-8") as f:
                json.dump({"problems": self._problems, "changes": self._changes}, f, indent=2)
        except OSError as e:
            log.error(f"Failed to save problems.json: {e}")

    def _next_problem_id(self) -> str:
        return f"PRB-{len(self._problems) + 1:04d}"

    def _next_change_id(self) -> str:
        return f"CHG-{len(self._changes) + 1:04d}"

    # ── Incident Management ──────────────────────

    @log_action
    def handle_incident(
        self,
        employee_name: str,
        department: str,
        issue_description: str,
        category: str,
        priority: Optional[str] = None,
    ) -> dict:
        """
        Creates an IncidentTicket, then checks if a Problem Record should be raised.
        Returns the created ticket dict.
        """
        ticket = self._store.create_ticket(
            employee_name=employee_name,
            department=department,
            issue_description=issue_description,
            category=category,
            ticket_type="incident",
            priority=priority,
        )
        log.info(f"Incident handled: {ticket['id']}")
        self._check_problem_threshold(issue_description, ticket["id"])
        return ticket

    # ── Service Request Management ───────────────

    @log_action
    def handle_service_request(
        self,
        employee_name: str,
        department: str,
        issue_description: str,
        category: str,
    ) -> dict:
        """Creates a ServiceRequest ticket with default P4 priority."""
        ticket = self._store.create_ticket(
            employee_name=employee_name,
            department=department,
            issue_description=issue_description,
            category=category,
            ticket_type="service",
            priority="P4",
        )
        log.info(f"Service request created: {ticket['id']}")
        return ticket

    # ── Problem Management ───────────────────────

    def _normalize_pattern(self, description: str) -> str:
        """Extracts a normalized keyword pattern from an issue description."""
        desc = description.lower()
        # Extract first 5 meaningful words as the pattern key
        words = re.findall(r"[a-z]+", desc)
        stop_words = {"the", "a", "an", "is", "in", "on", "at", "to", "for", "of", "and", "or"}
        meaningful = [w for w in words if w not in stop_words][:5]
        return " ".join(meaningful)

    def _check_problem_threshold(self, issue_description: str, ticket_id: str) -> None:
        """
        Counts how many tickets share a similar issue pattern.
        Auto-creates a ProblemRecord if count >= PROBLEM_THRESHOLD.
        """
        pattern = self._normalize_pattern(issue_description)
        all_tickets = self._store.get_all_tickets()

        # Find tickets matching this pattern
        matching_ids = [
            t["id"] for t in all_tickets
            if self._normalize_pattern(t.get("issue_description", "")) == pattern
        ]

        if len(matching_ids) >= PROBLEM_THRESHOLD:
            # Check if a problem record already exists for this pattern
            existing = next((p for p in self._problems if p["pattern"] == pattern), None)
            if existing:
                # Update linked tickets
                for mid in matching_ids:
                    if mid not in existing["linked_ticket_ids"]:
                        existing["linked_ticket_ids"].append(mid)
                self._save_problems()
                log.warning(f"Problem record {existing['problem_id']} updated with new linked tickets.")
            else:
                # Create new problem record
                prob = ProblemRecord(
                    problem_id=self._next_problem_id(),
                    pattern=pattern,
                    linked_ticket_ids=matching_ids,
                )
                self._problems.append(prob.to_dict())
                self._save_problems()
                log.warning(
                    f"PROBLEM RECORD CREATED: {prob.problem_id} | Pattern: '{pattern}' | "
                    f"{len(matching_ids)} linked tickets"
                )
                print(f"\n  ⚠  Problem Record raised: {prob.problem_id} (pattern: '{pattern}')")

    @log_action
    def create_problem_record(self, pattern: str, linked_ids: list[str]) -> dict:
        """Manually creates a Problem Record."""
        prob = ProblemRecord(
            problem_id=self._next_problem_id(),
            pattern=pattern,
            linked_ticket_ids=linked_ids,
        )
        self._problems.append(prob.to_dict())
        self._save_problems()
        log.info(f"Manual problem record created: {prob.problem_id}")
        return prob.to_dict()

    def get_all_problems(self) -> list[dict]:
        return list(self._problems)

    def display_problems(self) -> None:
        print_header("PROBLEM RECORDS")
        if not self._problems:
            print("  No problem records found.")
            return
        for p in self._problems:
            ProblemRecord.from_dict(p).display()

    # ── Change Management ────────────────────────

    @log_action
    def create_change_request(
        self,
        title: str,
        description: str,
        change_type: str,
        requested_by: str,
    ) -> dict:
        """Creates a new Change Request."""
        if change_type not in ChangeRecord.CHANGE_TYPES:
            raise ValueError(f"change_type must be one of {ChangeRecord.CHANGE_TYPES}")
        chg = ChangeRecord(
            change_id=self._next_change_id(),
            title=title,
            description=description,
            change_type=change_type,
            requested_by=requested_by,
        )
        self._changes.append(chg.to_dict())
        self._save_problems()
        log.info(f"Change request created: {chg.change_id} | {change_type} | {title}")
        return chg.to_dict()

    def update_change_state(self, change_id: str, new_state: str) -> dict:
        """Updates the state of a change record."""
        if new_state not in ChangeRecord.CHANGE_STATES:
            raise ValueError(f"State must be one of {ChangeRecord.CHANGE_STATES}")
        for chg in self._changes:
            if chg["change_id"] == change_id:
                chg["state"] = new_state
                self._save_problems()
                log.info(f"Change {change_id} state → {new_state}")
                return chg
        raise KeyError(f"Change '{change_id}' not found.")

    def get_all_changes(self) -> list[dict]:
        return list(self._changes)

    def display_changes(self) -> None:
        print_header("CHANGE RECORDS")
        if not self._changes:
            print("  No change records found.")
            return
        for c in self._changes:
            print_separator("─")
            print(f"  [{c['change_id']}] {c['title']} | {c['change_type']} | {c['state']}")
            print(f"  Requested by: {c['requested_by']}  |  Created: {c['created_date']}")
            print(f"  Description : {c['description']}")
        print_separator("─")

    # ── SLA Tracking ─────────────────────────────

    def sla_dashboard(self) -> None:
        """Prints a full SLA status dashboard for all open tickets."""
        print_header("SLA TRACKING DASHBOARD")
        tickets = self._store.get_all_tickets()
        open_tickets = [t for t in tickets if t["status"] not in ("Closed", "Resolved")]

        if not open_tickets:
            print("  No open tickets.")
            return

        breached, healthy = [], []
        for t in open_tickets:
            sla = compute_sla_status(t)
            entry = {**t, **sla}
            (breached if sla["breached"] else healthy).append(entry)

        if breached:
            print(f"\n  🔴 SLA BREACHED ({len(breached)} tickets):")
            print_separator("─")
            for t in breached:
                print(f"  [{t['id']}] {t['employee_name']:<20} | {t['priority']} | "
                      f"Elapsed: {t['elapsed_hours']}h / Limit: {t['sla_limit']}h | {t['issue_description'][:40]}")

        if healthy:
            print(f"\n  🟢 WITHIN SLA ({len(healthy)} tickets):")
            print_separator("─")
            for t in healthy:
                print(f"  [{t['id']}] {t['employee_name']:<20} | {t['priority']} | "
                      f"Remaining: {t['remaining_hours']}h | {t['issue_description'][:40]}")

        print_separator()
        print(f"  Summary: {len(breached)} breached | {len(healthy)} healthy | {len(open_tickets)} total open")
        print_separator()

    def get_sla_summary(self) -> dict:
        """Returns SLA stats as a dict for use in reports."""
        tickets = self._store.get_all_tickets()
        open_tickets = [t for t in tickets if t["status"] not in ("Closed", "Resolved")]
        breached = [t for t in open_tickets if compute_sla_status(t)["breached"]]
        return {
            "total_open":    len(open_tickets),
            "sla_breached":  len(breached),
            "sla_healthy":   len(open_tickets) - len(breached),
            "breach_rate":   round(len(breached) / len(open_tickets) * 100, 1) if open_tickets else 0.0,
        }

"""
tickets.py — OOP ticket class hierarchy + full CRUD operations.

Class hierarchy:
    Ticket (base)
    ├── IncidentTicket
    └── ServiceRequest
"""

import json
import os
from datetime import datetime
from typing import Optional

from logger import get_logger
from utils import (
    log_action, validate_input,
    ticket_id_generator, detect_priority,
    sanitize_text, is_valid_employee_name, is_valid_department,
    VALID_STATUSES, TICKET_CATEGORIES, backup_tickets_to_csv,
)

log = get_logger("tickets")
TICKETS_FILE = os.path.join(os.path.dirname(__file__), "data", "tickets.json")


# ─────────────────────────────────────────────
# CUSTOM EXCEPTIONS
# ─────────────────────────────────────────────

class TicketNotFoundError(Exception):
    """Raised when a ticket ID does not exist in the store."""


class InvalidTicketDataError(Exception):
    """Raised when ticket fields fail validation."""


class TicketAlreadyClosedError(Exception):
    """Raised when attempting to modify a closed ticket."""


# ─────────────────────────────────────────────
# BASE CLASS
# ─────────────────────────────────────────────

class Ticket:
    """
    Base class representing a generic IT service desk ticket.

    Attributes (encapsulated via properties):
        _id, _employee_name, _department, _issue_description,
        _category, _priority, _status, _created_date, _updated_date
    """

    def __init__(
        self,
        ticket_id: str,
        employee_name: str,
        department: str,
        issue_description: str,
        category: str,
        priority: str,
        status: str = "Open",
        created_date: Optional[str] = None,
        updated_date: Optional[str] = None,
    ):
        self._id                = ticket_id
        self._employee_name     = sanitize_text(employee_name)
        self._department        = sanitize_text(department)
        self._issue_description = sanitize_text(issue_description)
        self._category          = category
        self._priority          = priority
        self._status            = status
        self._created_date      = created_date or datetime.now().isoformat()
        self._updated_date      = updated_date or self._created_date

    # ── Properties (encapsulation) ──────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def employee_name(self) -> str:
        return self._employee_name

    @property
    def department(self) -> str:
        return self._department

    @property
    def issue_description(self) -> str:
        return self._issue_description

    @property
    def category(self) -> str:
        return self._category

    @property
    def priority(self) -> str:
        return self._priority

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, new_status: str):
        if new_status not in VALID_STATUSES:
            raise InvalidTicketDataError(f"Invalid status '{new_status}'. Choose from {VALID_STATUSES}")
        if self._status == "Closed":
            raise TicketAlreadyClosedError(f"Ticket {self._id} is already closed.")
        self._status      = new_status
        self._updated_date = datetime.now().isoformat()

    @property
    def created_date(self) -> str:
        return self._created_date

    @property
    def updated_date(self) -> str:
        return self._updated_date

    # ── Serialization ───────────────────────────

    def to_dict(self) -> dict:
        """Converts ticket to a plain dict for JSON storage."""
        return {
            "id":                self._id,
            "type":              self.__class__.__name__,
            "employee_name":     self._employee_name,
            "department":        self._department,
            "issue_description": self._issue_description,
            "category":          self._category,
            "priority":          self._priority,
            "status":            self._status,
            "created_date":      self._created_date,
            "updated_date":      self._updated_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ticket":
        """Reconstructs a Ticket (or subclass) from a stored dict."""
        ticket_type = data.get("type", "Ticket")
        klass = {"IncidentTicket": IncidentTicket, "ServiceRequest": ServiceRequest}.get(
            ticket_type, Ticket
        )
        return klass(
            ticket_id=data["id"],
            employee_name=data["employee_name"],
            department=data["department"],
            issue_description=data["issue_description"],
            category=data["category"],
            priority=data["priority"],
            status=data.get("status", "Open"),
            created_date=data.get("created_date"),
            updated_date=data.get("updated_date"),
        )

    def display(self) -> None:
        """Prints a formatted ticket detail view."""
        from utils import print_separator, priority_color_label, compute_sla_status
        print_separator()
        print(f"  Ticket ID   : {self._id}  [{self.__class__.__name__}]")
        print(f"  Employee    : {self._employee_name}")
        print(f"  Department  : {self._department}")
        print(f"  Category    : {self._category}")
        print(f"  Priority    : {priority_color_label(self._priority)}")
        print(f"  Status      : {self._status}")
        print(f"  Created     : {self._created_date}")
        print(f"  Updated     : {self._updated_date}")
        print(f"  Issue       : {self._issue_description}")
        sla = compute_sla_status(self.to_dict())
        breach = "⚠  BREACHED" if sla["breached"] else f"{sla['remaining_hours']}h remaining"
        print(f"  SLA         : {sla['elapsed_hours']}h elapsed / {sla['sla_limit']}h limit → {breach}")
        print_separator()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self._id} priority={self._priority} status={self._status}>"


# ─────────────────────────────────────────────
# SUBCLASS — INCIDENT TICKET
# ─────────────────────────────────────────────

class IncidentTicket(Ticket):
    """
    Represents an unplanned interruption or degradation of IT service.
    Inherits all Ticket behaviour; adds incident-specific escalation logic.
    """

    def __init__(self, *args, escalated: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self._escalated = escalated

    @property
    def escalated(self) -> bool:
        return self._escalated

    def escalate(self) -> None:
        """Marks the incident as escalated and bumps status."""
        if self._status == "Closed":
            raise TicketAlreadyClosedError(f"Cannot escalate closed ticket {self._id}.")
        self._escalated    = True
        self._status       = "Escalated"
        self._updated_date = datetime.now().isoformat()
        log.warning(f"Ticket {self._id} ESCALATED.")

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["escalated"] = self._escalated
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "IncidentTicket":
        obj = cls(
            ticket_id=data["id"],
            employee_name=data["employee_name"],
            department=data["department"],
            issue_description=data["issue_description"],
            category=data["category"],
            priority=data["priority"],
            status=data.get("status", "Open"),
            created_date=data.get("created_date"),
            updated_date=data.get("updated_date"),
            escalated=data.get("escalated", False),
        )
        return obj


# ─────────────────────────────────────────────
# SUBCLASS — SERVICE REQUEST
# ─────────────────────────────────────────────

class ServiceRequest(Ticket):
    """
    Represents a formal request for something new (access, software, hardware).
    Adds approval workflow on top of base Ticket.
    """

    APPROVAL_STATES = ("Pending", "Approved", "Rejected")

    def __init__(self, *args, approval_status: str = "Pending", **kwargs):
        super().__init__(*args, **kwargs)
        self._approval_status = approval_status

    @property
    def approval_status(self) -> str:
        return self._approval_status

    def approve(self) -> None:
        self._approval_status = "Approved"
        self._updated_date    = datetime.now().isoformat()
        log.info(f"ServiceRequest {self._id} approved.")

    def reject(self) -> None:
        self._approval_status = "Rejected"
        self._status          = "Closed"
        self._updated_date    = datetime.now().isoformat()
        log.info(f"ServiceRequest {self._id} rejected and closed.")

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["approval_status"] = self._approval_status
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceRequest":
        obj = cls(
            ticket_id=data["id"],
            employee_name=data["employee_name"],
            department=data["department"],
            issue_description=data["issue_description"],
            category=data["category"],
            priority=data["priority"],
            status=data.get("status", "Open"),
            created_date=data.get("created_date"),
            updated_date=data.get("updated_date"),
            approval_status=data.get("approval_status", "Pending"),
        )
        return obj


# ─────────────────────────────────────────────
# TICKET STORE — FILE I/O + CRUD
# ─────────────────────────────────────────────

class TicketStore:
    """
    Manages persistence and CRUD operations for all tickets.
    Loads from / saves to data/tickets.json.
    """

    def __init__(self):
        self._tickets: list[dict] = []
        self._load()

    # ── Private I/O ─────────────────────────────

    def _load(self) -> None:
        """Loads tickets from JSON file into memory."""
        os.makedirs(os.path.dirname(TICKETS_FILE), exist_ok=True)
        if not os.path.exists(TICKETS_FILE):
            self._tickets = []
            return
        try:
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                self._tickets = json.load(f)
            log.info(f"Loaded {len(self._tickets)} tickets from {TICKETS_FILE}")
        except (json.JSONDecodeError, OSError) as e:
            log.error(f"Failed to load tickets: {e}")
            self._tickets = []

    def _save(self) -> None:
        """Persists current in-memory tickets to JSON file."""
        try:
            with open(TICKETS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._tickets, f, indent=2, ensure_ascii=False)
            log.info(f"Saved {len(self._tickets)} tickets → {TICKETS_FILE}")
        except OSError as e:
            log.error(f"Failed to save tickets: {e}")
            raise

    def _next_id(self) -> str:
        existing = [t["id"] for t in self._tickets]
        gen = ticket_id_generator(existing)
        return next(gen)

    # ── CRUD ────────────────────────────────────

    @log_action
    @validate_input
    def create_ticket(
        self,
        employee_name: str,
        department: str,
        issue_description: str,
        category: str,
        ticket_type: str = "incident",
        priority: Optional[str] = None,
    ) -> dict:
        """
        Creates a new ticket, auto-detects priority if not supplied,
        persists to JSON, and returns the ticket dict.
        """
        # Validate inputs
        if not is_valid_employee_name(employee_name):
            raise InvalidTicketDataError(f"Invalid employee name: '{employee_name}'")
        if not is_valid_department(department):
            raise InvalidTicketDataError(f"Invalid department: '{department}'")
        if category not in TICKET_CATEGORIES:
            raise InvalidTicketDataError(f"Category must be one of {TICKET_CATEGORIES}")

        resolved_priority = priority or detect_priority(issue_description)
        tid = self._next_id()

        if ticket_type.lower() == "service":
            ticket = ServiceRequest(
                ticket_id=tid,
                employee_name=employee_name,
                department=department,
                issue_description=issue_description,
                category=category,
                priority=resolved_priority,
            )
        else:
            ticket = IncidentTicket(
                ticket_id=tid,
                employee_name=employee_name,
                department=department,
                issue_description=issue_description,
                category=category,
                priority=resolved_priority,
            )

        self._tickets.append(ticket.to_dict())
        self._save()
        log.info(f"Created {ticket.__class__.__name__} {tid} | {resolved_priority} | {employee_name}")
        return ticket.to_dict()

    def get_all_tickets(self) -> list[dict]:
        """Returns a shallow copy of all ticket dicts."""
        return list(self._tickets)

    def get_ticket_by_id(self, ticket_id: str) -> dict:
        """
        Searches for a ticket by ID.
        Raises TicketNotFoundError if not found.
        """
        for t in self._tickets:
            if t["id"] == ticket_id:
                return t
        raise TicketNotFoundError(f"Ticket '{ticket_id}' not found.")

    @log_action
    def update_status(self, ticket_id: str, new_status: str) -> dict:
        """Updates ticket status; validates via the Ticket property setter."""
        ticket_dict = self.get_ticket_by_id(ticket_id)
        # Reconstruct object to use property validation
        obj = Ticket.from_dict(ticket_dict)
        obj.status = new_status          # raises if invalid or closed
        # Sync back to store
        idx = next(i for i, t in enumerate(self._tickets) if t["id"] == ticket_id)
        self._tickets[idx] = obj.to_dict()
        self._save()
        log.info(f"Ticket {ticket_id} status → {new_status}")
        return self._tickets[idx]

    @log_action
    def close_ticket(self, ticket_id: str) -> dict:
        """Closes a ticket (sets status to Closed)."""
        return self.update_status(ticket_id, "Closed")

    @log_action
    def delete_ticket(self, ticket_id: str) -> None:
        """Permanently removes a ticket from the store."""
        before = len(self._tickets)
        self._tickets = [t for t in self._tickets if t["id"] != ticket_id]
        if len(self._tickets) == before:
            raise TicketNotFoundError(f"Ticket '{ticket_id}' not found — cannot delete.")
        self._save()
        log.info(f"Deleted ticket {ticket_id}")

    def search_tickets(self, keyword: str) -> list[dict]:
        """
        Case-insensitive search across id, employee_name,
        department, issue_description, and category.
        Uses map + filter for functional style.
        """
        kw = keyword.lower()
        fields = ("id", "employee_name", "department", "issue_description", "category")
        return list(filter(
            lambda t: any(kw in str(t.get(f, "")).lower() for f in fields),
            self._tickets,
        ))

    @log_action
    def escalate_ticket(self, ticket_id: str) -> dict:
        """Escalates an IncidentTicket."""
        ticket_dict = self.get_ticket_by_id(ticket_id)
        if ticket_dict.get("type") != "IncidentTicket":
            raise InvalidTicketDataError("Only IncidentTickets can be escalated.")
        obj = IncidentTicket.from_dict(ticket_dict)
        obj.escalate()
        idx = next(i for i, t in enumerate(self._tickets) if t["id"] == ticket_id)
        self._tickets[idx] = obj.to_dict()
        self._save()
        return self._tickets[idx]

    def check_and_escalate_sla_breaches(self) -> list[dict]:
        """
        Scans all open tickets via the sla_breach_scanner generator.
        Auto-escalates P1/P2 breaches and logs warnings for others.
        Returns list of breached ticket dicts.
        """
        from utils import sla_breach_scanner
        breached = list(sla_breach_scanner(self._tickets))
        for t in breached:
            log.warning(f"SLA BREACH: {t['id']} | {t['priority']} | {t['employee_name']}")
            if t["priority"] in ("P1", "P2") and t.get("type") == "IncidentTicket":
                try:
                    self.escalate_ticket(t["id"])
                except (TicketAlreadyClosedError, InvalidTicketDataError):
                    pass
        return breached

    def backup(self) -> None:
        """Triggers CSV backup of all tickets."""
        backup_tickets_to_csv(self._tickets)

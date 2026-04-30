"""
reports.py — Daily and monthly report generation for the IT Service Desk.

ReportGenerator uses generators and map/filter for efficient data processing.
"""

import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

from logger import get_logger
from utils import (
    log_action, print_header, print_separator,
    sla_breach_scanner, open_tickets_generator,
    compute_sla_status, priority_color_label,
)

log = get_logger("reports")


class ReportGenerator:
    """
    Generates daily and monthly reports from ticket data.
    All heavy lifting uses generators and functional constructs (map/filter/Counter).
    """

    def __init__(self, ticket_store, itil_manager=None):
        self._store  = ticket_store
        self._itil   = itil_manager

    # ── Internal Helpers ─────────────────────────

    def _tickets_in_range(self, days: int) -> list[dict]:
        """Returns tickets created within the last `days` days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            t for t in self._store.get_all_tickets()
            if datetime.fromisoformat(t["created_date"]) >= cutoff
        ]

    def _avg_resolution_hours(self, tickets: list[dict]) -> float:
        """
        Computes average resolution time in hours for closed/resolved tickets.
        Uses a generator expression for memory efficiency.
        """
        resolved = [
            t for t in tickets
            if t.get("status") in ("Closed", "Resolved")
        ]
        if not resolved:
            return 0.0

        def hours(t):
            created = datetime.fromisoformat(t["created_date"])
            updated = datetime.fromisoformat(t["updated_date"])
            return (updated - created).total_seconds() / 3600

        total = sum(hours(t) for t in resolved)
        return round(total / len(resolved), 2)

    def _priority_breakdown(self, tickets: list[dict]) -> dict:
        """Returns a Counter of tickets per priority."""
        return dict(Counter(t.get("priority", "P4") for t in tickets))

    def _status_breakdown(self, tickets: list[dict]) -> dict:
        """Returns a Counter of tickets per status."""
        return dict(Counter(t.get("status", "Open") for t in tickets))

    def _department_breakdown(self, tickets: list[dict]) -> dict:
        """Returns a Counter of tickets per department."""
        return dict(Counter(t.get("department", "Unknown") for t in tickets))

    def _most_common_issue(self, tickets: list[dict]) -> str:
        """Finds the most frequently occurring issue category."""
        if not tickets:
            return "N/A"
        counter = Counter(t.get("category", "Other") for t in tickets)
        return counter.most_common(1)[0][0]

    # ── Daily Report ─────────────────────────────

    @log_action
    def daily_report(self, print_output: bool = True) -> dict:
        """
        Generates a daily report covering the last 24 hours.
        Returns a structured dict and optionally prints to console.
        """
        tickets = self._tickets_in_range(days=1)
        all_tickets = self._store.get_all_tickets()

        # SLA breaches via generator
        breached = list(sla_breach_scanner(all_tickets))

        # High priority = P1 + P2
        high_priority = [t for t in tickets if t.get("priority") in ("P1", "P2")]

        report = {
            "report_type":      "Daily",
            "generated_at":     datetime.now().isoformat(),
            "period":           "Last 24 hours",
            "total_tickets":    len(tickets),
            "open_tickets":     len([t for t in tickets if t["status"] not in ("Closed", "Resolved")]),
            "closed_tickets":   len([t for t in tickets if t["status"] in ("Closed", "Resolved")]),
            "high_priority":    len(high_priority),
            "sla_breaches":     len(breached),
            "priority_breakdown": self._priority_breakdown(tickets),
            "status_breakdown":   self._status_breakdown(tickets),
            "avg_resolution_hrs": self._avg_resolution_hours(tickets),
            "breached_ticket_ids": [t["id"] for t in breached],
        }

        if print_output:
            self._print_daily_report(report, breached)

        log.info(f"Daily report generated: {len(tickets)} tickets, {len(breached)} SLA breaches")
        return report

    def _print_daily_report(self, report: dict, breached: list[dict]) -> None:
        print_header(f"📋 DAILY REPORT — {datetime.now().strftime('%Y-%m-%d')}")
        print(f"  Period          : {report['period']}")
        print(f"  Total Tickets   : {report['total_tickets']}")
        print(f"  Open            : {report['open_tickets']}")
        print(f"  Closed/Resolved : {report['closed_tickets']}")
        print(f"  High Priority   : {report['high_priority']}  (P1 + P2)")
        print(f"  SLA Breaches    : {report['sla_breaches']}")
        print(f"  Avg Resolution  : {report['avg_resolution_hrs']}h")

        print("\n  Priority Breakdown:")
        for p, count in sorted(report["priority_breakdown"].items()):
            bar = "█" * count
            print(f"    {priority_color_label(p):<20} {bar} ({count})")

        print("\n  Status Breakdown:")
        for s, count in report["status_breakdown"].items():
            print(f"    {s:<15} : {count}")

        if breached:
            print(f"\n  ⚠  SLA Breached Tickets:")
            for t in breached:
                sla = compute_sla_status(t)
                print(f"    [{t['id']}] {t['employee_name']:<18} | {t['priority']} | "
                      f"Overdue by {round(sla['elapsed_hours'] - sla['sla_limit'], 1)}h")
        print_separator()

    # ── Monthly Report ────────────────────────────

    @log_action
    def monthly_report(self, print_output: bool = True) -> dict:
        """
        Generates a monthly report covering the last 30 days.
        Returns a structured dict and optionally prints to console.
        """
        tickets = self._tickets_in_range(days=30)

        dept_counter   = Counter(t.get("department", "Unknown") for t in tickets)
        top_department = dept_counter.most_common(1)[0] if dept_counter else ("N/A", 0)

        report = {
            "report_type":          "Monthly",
            "generated_at":         datetime.now().isoformat(),
            "period":               "Last 30 days",
            "total_tickets":        len(tickets),
            "most_common_issue":    self._most_common_issue(tickets),
            "avg_resolution_hrs":   self._avg_resolution_hours(tickets),
            "top_department":       top_department[0],
            "top_dept_count":       top_department[1],
            "priority_breakdown":   self._priority_breakdown(tickets),
            "status_breakdown":     self._status_breakdown(tickets),
            "department_breakdown": self._department_breakdown(tickets),
            "sla_breaches":         len(list(sla_breach_scanner(tickets))),
        }

        if print_output:
            self._print_monthly_report(report)

        log.info(f"Monthly report generated: {len(tickets)} tickets over 30 days")
        return report

    def _print_monthly_report(self, report: dict) -> None:
        print_header(f"📊 MONTHLY REPORT — {datetime.now().strftime('%B %Y')}")
        print(f"  Period              : {report['period']}")
        print(f"  Total Tickets       : {report['total_tickets']}")
        print(f"  Most Common Issue   : {report['most_common_issue']}")
        print(f"  Avg Resolution Time : {report['avg_resolution_hrs']}h")
        print(f"  Top Department      : {report['top_department']} ({report['top_dept_count']} tickets)")
        print(f"  SLA Breaches        : {report['sla_breaches']}")

        print("\n  Priority Breakdown:")
        for p, count in sorted(report["priority_breakdown"].items()):
            bar = "█" * min(count, 40)
            print(f"    {priority_color_label(p):<20} {bar} ({count})")

        print("\n  Department Breakdown (Top 5):")
        dept_sorted = sorted(report["department_breakdown"].items(), key=lambda x: x[1], reverse=True)[:5]
        for dept, count in dept_sorted:
            bar = "█" * min(count, 40)
            print(f"    {dept:<25} {bar} ({count})")

        print("\n  Status Breakdown:")
        for s, count in report["status_breakdown"].items():
            print(f"    {s:<15} : {count}")
        print_separator()

    # ── Ticket Summary Table ──────────────────────

    def print_all_tickets_table(self) -> None:
        """Prints a compact table of all tickets."""
        tickets = self._store.get_all_tickets()
        print_header(f"ALL TICKETS ({len(tickets)} total)")
        if not tickets:
            print("  No tickets found.")
            return

        print(f"  {'ID':<10} {'Employee':<20} {'Dept':<15} {'Priority':<6} {'Status':<12} {'Category':<12} {'SLA'}")
        print_separator("─")
        for t in tickets:
            sla = compute_sla_status(t)
            sla_str = "⚠ BREACH" if sla["breached"] else f"{sla['remaining_hours']}h left"
            print(
                f"  {t['id']:<10} {t['employee_name']:<20} {t['department']:<15} "
                f"{t['priority']:<6} {t['status']:<12} {t['category']:<12} {sla_str}"
            )
        print_separator()

    def export_report_to_txt(self, report_type: str = "daily") -> str:
        """
        Exports a report to a timestamped .txt file in data/.
        Returns the file path.
        """
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(data_dir, f"report_{report_type}_{ts}.txt")

        if report_type == "daily":
            report = self.daily_report(print_output=False)
        else:
            report = self.monthly_report(print_output=False)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"MindHire IT Service Desk — {report['report_type']} Report\n")
            f.write(f"Generated: {report['generated_at']}\n")
            f.write("=" * 60 + "\n")
            for key, val in report.items():
                f.write(f"{key:<30}: {val}\n")

        log.info(f"Report exported → {filename}")
        print(f"\n  ✅ Report exported → {filename}")
        return filename

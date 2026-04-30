"""
monitor.py — System resource monitoring with auto-ticket creation.

Monitors CPU, RAM, Disk, and Network.
Automatically creates P1 incident tickets when thresholds are breached.
"""

import os
import time
from datetime import datetime
from typing import Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from logger import get_logger
from utils import log_action, print_separator

log = get_logger("monitor")

# ─────────────────────────────────────────────
# THRESHOLDS
# ─────────────────────────────────────────────

THRESHOLDS = {
    "cpu_percent":   90.0,   # Alert if CPU usage exceeds this %
    "ram_percent":   95.0,   # Alert if RAM usage exceeds this %
    "disk_percent":  90.0,   # Alert if disk usage exceeds this % (i.e. < 10% free)
    "net_errors":    100,    # Alert if network errors exceed this count
}


class MonitorAlert:
    """Represents a single monitoring alert with metadata."""

    def __init__(self, resource: str, value: float, threshold: float, message: str):
        self.resource  = resource
        self.value     = value
        self.threshold = threshold
        self.message   = message
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "resource":  self.resource,
            "value":     self.value,
            "threshold": self.threshold,
            "message":   self.message,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        return f"<MonitorAlert resource={self.resource} value={self.value}>"


class Monitor:
    """
    Polls system resources and fires alerts when thresholds are exceeded.
    Integrates with TicketStore to auto-create P1 incident tickets.
    """

    def __init__(self, ticket_store=None):
        """
        Args:
            ticket_store: Optional TicketStore instance for auto-ticket creation.
        """
        self._store         = ticket_store
        self._alert_history: list[MonitorAlert] = []

    # ── Resource Collectors ──────────────────────

    def _get_cpu(self) -> Optional[float]:
        """Returns current CPU usage percentage (1-second interval)."""
        if not PSUTIL_AVAILABLE:
            return None
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            log.error(f"CPU read error: {e}")
            return None

    def _get_ram(self) -> Optional[dict]:
        """Returns RAM usage stats as a dict."""
        if not PSUTIL_AVAILABLE:
            return None
        try:
            mem = psutil.virtual_memory()
            return {"percent": mem.percent, "used_gb": round(mem.used / 1e9, 2), "total_gb": round(mem.total / 1e9, 2)}
        except Exception as e:
            log.error(f"RAM read error: {e}")
            return None

    def _get_disk(self, path: str = "/") -> Optional[dict]:
        """Returns disk usage stats for the given path."""
        if not PSUTIL_AVAILABLE:
            return None
        # Use C:\ on Windows
        if os.name == "nt":
            path = "C:\\"
        try:
            disk = psutil.disk_usage(path)
            return {"percent": disk.percent, "free_gb": round(disk.free / 1e9, 2), "total_gb": round(disk.total / 1e9, 2)}
        except Exception as e:
            log.error(f"Disk read error: {e}")
            return None

    def _get_network(self) -> Optional[dict]:
        """Returns cumulative network I/O counters."""
        if not PSUTIL_AVAILABLE:
            return None
        try:
            net = psutil.net_io_counters()
            return {
                "bytes_sent":   net.bytes_sent,
                "bytes_recv":   net.bytes_recv,
                "errin":        net.errin,
                "errout":       net.errout,
                "dropin":       net.dropin,
                "dropout":      net.dropout,
            }
        except Exception as e:
            log.error(f"Network read error: {e}")
            return None

    # ── Alert Logic ──────────────────────────────

    def _fire_alert(self, resource: str, value: float, threshold: float, message: str) -> MonitorAlert:
        """Creates an alert, logs it as CRITICAL, and optionally auto-creates a ticket."""
        alert = MonitorAlert(resource, value, threshold, message)
        self._alert_history.append(alert)
        log.critical(f"MONITOR ALERT | {resource} | {message}")

        if self._store:
            self._auto_create_ticket(alert)

        return alert

    def _auto_create_ticket(self, alert: MonitorAlert) -> None:
        """Auto-creates a P1 IncidentTicket for a monitoring alert."""
        try:
            ticket = self._store.create_ticket(
                employee_name="System Monitor",
                department="IT Infrastructure",
                issue_description=alert.message,
                category="Hardware",
                ticket_type="incident",
                priority="P1",
            )
            log.critical(f"Auto-ticket created: {ticket['id']} for alert: {alert.resource}")
            print(f"\n  🚨 AUTO-TICKET CREATED: {ticket['id']} | P1 | {alert.message}")
        except Exception as e:
            log.error(f"Failed to auto-create ticket for alert {alert.resource}: {e}")

    # ── Main Scan ────────────────────────────────

    @log_action
    def run_scan(self) -> dict:
        """
        Performs a full system scan.
        Returns a snapshot dict and fires alerts for any threshold breaches.
        """
        if not PSUTIL_AVAILABLE:
            log.warning("psutil not installed — using simulated monitoring data.")
            return self._simulated_scan()

        alerts_fired: list[dict] = []
        snapshot: dict = {"timestamp": datetime.now().isoformat()}

        # CPU
        cpu = self._get_cpu()
        snapshot["cpu_percent"] = cpu
        if cpu is not None and cpu > THRESHOLDS["cpu_percent"]:
            a = self._fire_alert("CPU", cpu, THRESHOLDS["cpu_percent"],
                                 f"CPU usage critical: {cpu:.1f}% (threshold {THRESHOLDS['cpu_percent']}%)")
            alerts_fired.append(a.to_dict())

        # RAM
        ram = self._get_ram()
        snapshot["ram"] = ram
        if ram and ram["percent"] > THRESHOLDS["ram_percent"]:
            a = self._fire_alert("RAM", ram["percent"], THRESHOLDS["ram_percent"],
                                 f"RAM usage critical: {ram['percent']:.1f}% ({ram['used_gb']}GB / {ram['total_gb']}GB)")
            alerts_fired.append(a.to_dict())

        # Disk
        disk = self._get_disk()
        snapshot["disk"] = disk
        if disk and disk["percent"] > THRESHOLDS["disk_percent"]:
            a = self._fire_alert("Disk", disk["percent"], THRESHOLDS["disk_percent"],
                                 f"Disk critically full: {disk['percent']:.1f}% used, only {disk['free_gb']}GB free")
            alerts_fired.append(a.to_dict())

        # Network
        net = self._get_network()
        snapshot["network"] = net
        if net:
            total_errors = net["errin"] + net["errout"]
            if total_errors > THRESHOLDS["net_errors"]:
                a = self._fire_alert("Network", total_errors, THRESHOLDS["net_errors"],
                                     f"Network errors detected: {total_errors} errors (in:{net['errin']} out:{net['errout']})")
                alerts_fired.append(a.to_dict())

        snapshot["alerts"] = alerts_fired
        return snapshot

    def _simulated_scan(self) -> dict:
        """
        Returns a simulated snapshot when psutil is unavailable.
        Useful for demo/testing environments.
        """
        import random
        snapshot = {
            "timestamp":   datetime.now().isoformat(),
            "cpu_percent": round(random.uniform(10, 85), 1),
            "ram":         {"percent": round(random.uniform(40, 80), 1), "used_gb": 6.2, "total_gb": 16.0},
            "disk":        {"percent": round(random.uniform(30, 70), 1), "free_gb": 120.0, "total_gb": 500.0},
            "network":     {"bytes_sent": 1024000, "bytes_recv": 2048000, "errin": 0, "errout": 0, "dropin": 0, "dropout": 0},
            "alerts":      [],
            "simulated":   True,
        }
        return snapshot

    def display_snapshot(self, snapshot: dict) -> None:
        """Prints a formatted system health dashboard."""
        print_separator("─")
        print(f"  📊 SYSTEM HEALTH SNAPSHOT — {snapshot['timestamp']}")
        print_separator("─")

        cpu = snapshot.get("cpu_percent")
        if cpu is not None:
            bar = self._bar(cpu, 100)
            flag = " ⚠ ALERT" if cpu > THRESHOLDS["cpu_percent"] else ""
            print(f"  CPU   : {bar} {cpu:.1f}%{flag}")

        ram = snapshot.get("ram")
        if ram:
            bar = self._bar(ram["percent"], 100)
            flag = " ⚠ ALERT" if ram["percent"] > THRESHOLDS["ram_percent"] else ""
            print(f"  RAM   : {bar} {ram['percent']:.1f}% ({ram['used_gb']}GB / {ram['total_gb']}GB){flag}")

        disk = snapshot.get("disk")
        if disk:
            bar = self._bar(disk["percent"], 100)
            flag = " ⚠ ALERT" if disk["percent"] > THRESHOLDS["disk_percent"] else ""
            print(f"  Disk  : {bar} {disk['percent']:.1f}% used ({disk['free_gb']}GB free){flag}")

        net = snapshot.get("network")
        if net:
            print(f"  Net   : ↑ {net['bytes_sent']//1024}KB  ↓ {net['bytes_recv']//1024}KB  Errors: {net.get('errin',0)+net.get('errout',0)}")

        if snapshot.get("simulated"):
            print("  ℹ  [Simulated data — install psutil for live metrics]")

        alerts = snapshot.get("alerts", [])
        if alerts:
            print(f"\n  🚨 {len(alerts)} ALERT(S) FIRED — tickets auto-created.")
        else:
            print("\n  ✅ All systems within normal thresholds.")
        print_separator("─")

    @staticmethod
    def _bar(value: float, total: float, width: int = 20) -> str:
        """Renders a simple ASCII progress bar."""
        filled = int((value / total) * width)
        return f"[{'█' * filled}{'░' * (width - filled)}]"

    def get_alert_history(self) -> list[dict]:
        """Returns all alerts fired in this session."""
        return [a.to_dict() for a in self._alert_history]

    def continuous_monitor(self, interval_seconds: int = 30, max_cycles: int = 5) -> None:
        """
        Runs repeated scans at a fixed interval.
        Useful for background monitoring loops.
        """
        print(f"\n  🔄 Starting continuous monitor ({max_cycles} cycles, {interval_seconds}s interval)")
        print("  Press Ctrl+C to stop.\n")
        try:
            for cycle in range(1, max_cycles + 1):
                print(f"\n  ── Cycle {cycle}/{max_cycles} ──")
                snapshot = self.run_scan()
                self.display_snapshot(snapshot)
                if cycle < max_cycles:
                    time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n  Monitor stopped by user.")

# 🖥 Smart IT Service Desk Automation System

A production-level Python backend system that automates IT helpdesk operations including ticket management, SLA tracking, system monitoring, ITIL processes, and reporting.

---

## 📁 Project Structure

```
smart_it_service_desk/
├── main.py          — CLI entry point & menu routing
├── tickets.py       — OOP ticket classes + full CRUD
├── monitor.py       — System resource monitoring + auto-tickets
├── reports.py       — Daily & monthly report generation
├── itil.py          — ITIL: Incident, Problem, Change, SLA
├── utils.py         — Decorators, generators, validators, helpers
├── logger.py        — Centralised rotating file + console logger
├── tests.py         — Full test suite (40+ tests)
├── data/
│   ├── tickets.json     — Ticket persistence store
│   ├── logs.txt         — Rotating application log
│   ├── backup.csv       — CSV backup of all tickets
│   └── problems.json    — Problem & Change records
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation

```bash
# 1. Clone or download the project
cd smart_it_service_desk

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py

# 5. Run the test suite
python tests.py
```

> **Note:** `psutil` is the only dependency. If not installed, the monitor falls back to simulated data automatically — the rest of the system works with zero dependencies.

---

## 🚀 Features

### 🎫 Ticket Management
| Feature | Description |
|---|---|
| Create Ticket | Incident or Service Request with auto-priority detection |
| View All | Tabular view with SLA status indicators |
| Search | Full-text search across all ticket fields |
| Update Status | Validated status transitions |
| Close / Delete | With confirmation and error handling |
| Escalate | Auto-escalates P1/P2 on SLA breach |

### 🔴 Priority Rules (Auto-detected from description)
| Keyword | Priority | SLA |
|---|---|---|
| server down / server crash | P1 🔴 | 1 hour |
| internet down / network down | P2 🟠 | 4 hours |
| laptop slow / system slow | P3 🟡 | 8 hours |
| password reset / password change | P4 🟢 | 24 hours |

### 📋 ITIL Processes
- **Incident Management** — Full lifecycle from creation to closure
- **Service Request Management** — With approval workflow
- **Problem Management** — Auto-creates Problem Records when the same issue pattern repeats ≥ 5 times
- **Change Management** — Standard / Normal / Emergency change tracking with state machine
- **SLA Dashboard** — Real-time breach detection and remaining time display

### 📡 System Monitoring
Monitors CPU, RAM, Disk, and Network via `psutil`.

| Resource | Alert Threshold | Action |
|---|---|---|
| CPU | > 90% | Auto-create P1 ticket + CRITICAL log |
| RAM | > 95% | Auto-create P1 ticket + CRITICAL log |
| Disk | > 90% used | Auto-create P1 ticket + CRITICAL log |
| Network | > 100 errors | Auto-create P1 ticket + CRITICAL log |

### 📊 Reports
- **Daily Report** — Tickets in last 24h, open/closed counts, high priority, SLA breaches, priority breakdown
- **Monthly Report** — 30-day summary, most common issue, avg resolution time, top department
- **Export** — Save any report to a timestamped `.txt` file

---

## 🐍 Python Concepts Used

| Concept | Where Used |
|---|---|
| OOP — Inheritance | `Ticket → IncidentTicket / ServiceRequest` |
| OOP — Polymorphism | `to_dict()` / `from_dict()` overridden in each subclass |
| OOP — Encapsulation | Private `_attributes` with `@property` getters/setters |
| Decorators | `@log_action`, `@validate_input` in `utils.py` |
| Generators | `ticket_id_generator`, `sla_breach_scanner`, `open_tickets_generator` |
| Custom Exceptions | `TicketNotFoundError`, `InvalidTicketDataError`, `TicketAlreadyClosedError` |
| File Handling | JSON read/write, CSV backup, rotating log files |
| Regex | `is_valid_employee_name`, `is_valid_department`, `sanitize_text`, `_normalize_pattern` |
| map / filter | `search_tickets` uses `filter` + `map` |
| Counter / defaultdict | Report breakdowns in `reports.py` |
| Data Structures | Lists, dicts, sets, tuples throughout |

---

## 🧪 Test Suite

Run with:
```bash
python tests.py
```

Covers 40+ tests across 9 categories:
1. Ticket Creation (6 tests)
2. CRUD Operations (7 tests)
3. SLA Logic (5 tests)
4. Priority Auto-Detection (5 tests)
5. Monitoring & Auto-Tickets (3 tests)
6. File Handling (3 tests)
7. Exception Handling (4 tests)
8. Utilities & Generators (4 tests)
9. OOP & Polymorphism (4 tests)

---

## 📝 Logging

All events are logged to `data/logs.txt` with rotating file handler (2MB max, 3 backups).

Log levels used:
- `INFO` — Ticket creation, updates, normal operations
- `WARNING` — SLA breaches, problem record creation, escalations
- `ERROR` — File I/O failures, unexpected exceptions
- `CRITICAL` — Monitoring alerts (CPU/RAM/Disk threshold breaches)

---

## 🔄 GitHub Upload Steps

```bash
# Step 1: Initialise git repo
cd smart_it_service_desk
git init

# Step 2: Create .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "venv/" >> .gitignore
echo "data/logs.txt" >> .gitignore

# Step 3: Stage all files
git add .

# Step 4: Initial commit
git commit -m "feat: initial release — Smart IT Service Desk Automation System"

# Step 5: Add remote origin (replace with your repo URL)
git remote add origin https://github.com/<your-username>/smart-it-service-desk.git

# Step 6: Push
git branch -M main
git push -u origin main
```

---

## 📌 Sample CLI Session

```
══════════════════════════════════════════════════════════════════════
  🖥  SMART IT SERVICE DESK AUTOMATION SYSTEM
══════════════════════════════════════════════════════════════════════
  Initialising components...
  ✅ System ready.

══════════════════════════════════════════════════════════════════════
  MAIN MENU
══════════════════════════════════════════════════════════════════════
  1. 🎫  Ticket Management
  2. 📋  ITIL Processes
  3. 📡  System Monitor
  4. 📊  Reports
  5. 💾  Backup & Restore
  0. 🚪  Exit

  Select: 1
```

---

## 👤 Author

Built as a production-level Python portfolio project demonstrating clean architecture, ITIL best practices, and advanced Python concepts.

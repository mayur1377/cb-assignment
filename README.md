# cb_maintenance — California Burrito Maintenance Ops

Frappe custom app replacing spreadsheet-based maintenance tracking for California Burrito's 133 stores across 5 Indian cities.

---

## Live Demo

| | |
|---|---|
| **URL** | *(add after Frappe Cloud deploy)* |
| **Email** | maintenance@californiaburrito.in |
| **Password** | Admin@CB2024 |
| **Role** | Maintenance Manager |

> Log in → open the **Maintenance Ops** workspace from the top-left app switcher.

---

## What's built

### Core v1
| Requirement | Implementation |
|---|---|
| Define PM once, roll everywhere | `CB PM Program` — one program per asset type, **Roll Out to Stores** button creates tasks across all 133 outlets |
| See due / overdue, mark done | `CB PM Task` with Scheduled → Due → Overdue → Completed / Failed lifecycle; daily scheduler auto-refreshes |
| Raise a reactive ticket | `CB Maintenance Ticket` — outlet + asset + issue type, auto-assigned to zonal incharge |
| Handle messy data | Asset name normalisation (`ASSET_ALIASES`), blank-frequency → one-time, outlet/asset pairs inferred from PM tracker |

### Go further
| Feature | How |
|---|---|
| Shared equipment taxonomy | Both PM tasks and tickets use `CB Asset Type` + `CB Issue Type` — same hierarchy, two workflows |
| Zonal routing | Outlet → city → `CB Zonal Office` → `CB Maintenance Team Member` (incharge flag). Auto-assigned on every ticket and PM failure |
| Spare parts suggestion | When `issue_type` is selected on a ticket, JS looks up `CB Spare Part` records and prefills the field. PM-failure tickets do the same server-side |
| PM failure → ticket | Mark a PM task result as **Failed** → `on_update` auto-creates a linked `CB Maintenance Ticket` with issue type, spare part, and assignee already filled |
| Overdue alerts | Two layers: (1) Python scheduler emails zonal incharge on first day of overdue; (2) declarative `Notification` fixture fires 1 day after due date for all Maintenance Managers |

### Reports
| Report | What it shows |
|---|---|
| **PM Health by Outlet** | Per-outlet: total tasks, completed, overdue, open tickets, completion %, health status (🟢/🟡/🔴). Bar chart + summary row |
| **Asset Failure Analysis** | Per-asset type: PM failure rate, reactive ticket count, top issue category, most-needed spare part. Connects all 4 source files |

---

## Data model

```
CB Zonal Office  ←─  CB Outlet  ─→  CB Store Asset  ←─  CB PM Task
                                          │                    │
                                     CB Asset Type        CB PM Program
                                                               │
CB Maintenance Ticket  ─→  CB Issue Type  ─→  CB Spare Part   │
        │                                                      │
        └─────────────────── linked_ticket ───────────────────┘
```

| DocType | Purpose |
|---|---|
| CB Zonal Office | 5 city offices (BLR / NCR / HYD / CHN / PUN) |
| CB Outlet | 133 stores |
| CB Asset Type | Normalised equipment taxonomy (~18 types) |
| CB PM Program | PM template per asset type — tasks + frequencies |
| CB Store Asset | Asset instance at a specific outlet |
| CB PM Task | Scheduled work — auto-created, auto-recurs |
| CB Issue Type | Ticket taxonomy: Dept → Category → Sub-category |
| CB Spare Part | Coded parts catalog linked to issue types |
| CB Maintenance Team Member | Technicians with reporting chain + incharge flag |
| CB Maintenance Ticket | Reactive + PM-failure tickets |

---

## Walkthrough Q&A

**A new store opens — what do you create?**
1. Create `CB Outlet` (code + city). City auto-links to the right `CB Zonal Office`.
2. Create one `CB Store Asset` per piece of equipment.
3. Done — `after_insert` scans active PM programs for that asset type and creates all `CB PM Task` rows automatically.

**AC coil cleaning → bi-monthly chain-wide — what do you touch?**
Open the `AC Plant PM Program`, change the task frequency to `6 month`. Click **Roll Out to Stores**. The rollout skips stores that already have an open task for that task name. Going forward, `generate_recurring_pm_tasks` (daily scheduler) uses the new frequency after each completion.

**How many records after 1 year / 5 years?**

| Table | 1 year | 5 years | Notes |
|---|---|---|---|
| CB PM Program | ~18 | ~18 | Templates never grow |
| CB Store Asset | ~1,300 | ~1,400 | ~10 assets × 133 stores |
| CB PM Task | ~25,000 | ~125,000 | Assets × tasks × recurrences |
| CB Maintenance Ticket | ~2,000–5,000 | ~10,000–25,000 | Depends on failure rate |

All list views filter by indexed fields (`status`, `outlet`, `due_date`) — stays fast at 100k+ rows. The **PM Health by Outlet** report aggregates this in one query.

**How would you route a ticket to the right technician?**
`CB Outlet.city` → hardcoded city-to-office map → query `CB Maintenance Team Member` where `zonal_office = X AND is_incharge = 1` → fall back to first active member. Runs in `CBMaintenanceTicket.validate()` so every ticket arrives pre-assigned.

---

## Run locally (Docker)

```bash
# macOS — start Colima if using it instead of Docker Desktop
colima start
export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock

cd cb_maintenance
docker-compose up --build
```

First run takes ~10 min (downloads Frappe, creates site). Visit **http://localhost:8000** — login `Administrator` / `admin`.

Then import seed data:

```bash
docker compose exec frappe bench --site site1.local \
  execute cb_maintenance.maintenance_ops.setup.import_case_data.run
```

---

## Deploy to Frappe Cloud

1. [frappecloud.com](https://frappecloud.com) → free trial → **New Site** → Frappe v15
2. Add app → GitHub → `mayur1377/cb-assignment` → branch `main`
3. After site is up, open Console and run the import command above (replace `site1.local` with your site name)
4. Create a user → assign role **Maintenance Manager** → share credentials

---

## Design decisions

- **Asset normalisation** — messy names (`"Fire Ext."`, `"Walk-IN Chiller"`) map to canonical `CB Asset Type` records via `ASSET_ALIASES` dict; aliases stored for traceability.
- **Frequency gaps** — blank frequency in the legacy sheet → `One-time`; excluded from auto-recurrence.
- **Store assets inferred** — only outlet + asset pairs that appear in the PM tracker are created; not every outlet is assumed to have every asset type.
- **Scope cut** — no ERPNext Asset module, no mobile app, no WhatsApp integration. Daily scheduler is the overdue notification hook; email notifications handle escalation.

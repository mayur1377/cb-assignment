# cb_maintenance

**Live site:** *(add URL after deploy)*
**Login:** `maintenance@californiaburrito.in` / `Admin@CB2024` — role: Maintenance Manager

---

## What I built

All four v1 requirements plus the full "go further" set:

- **PM program → store rollout** — one program per asset type, one click fans out tasks to all active store assets. New store assets auto-generate tasks on insert.
- **PM task lifecycle** — Scheduled → Due → Overdue → Completed / Failed, refreshed by daily scheduler. Recurring tasks auto-created after completion.
- **PM failure → ticket** — marking a task Failed auto-creates a linked `CB Maintenance Ticket` with issue type, spare part, and assignee pre-filled.
- **Zonal routing** — outlet → city → zonal office → incharge. Runs on every ticket (reactive or failure-generated).
- **Spare parts suggestion** — selecting an issue type on a ticket prefills the spare part field client-side; PM failure path does the same server-side.
- **Overdue alerts** — two layers: Python scheduler emails zonal incharge on the first overdue day; `Notification` fixture fires for Maintenance Managers declaratively.
- **Two reports** — *PM Health by Outlet* (completion rate, overdue count, at-risk flag per outlet) and *Asset Failure Analysis* (failure rate + top issue + most-needed spare part per asset type). Both have summary rows and bar charts.
- **CB brand theme** — CSS variables override Frappe's primary colour; staggered fade-up animations on workspace cards; pulsing red badge on overdue items.
- **Print format** — `CB PM Task Checklist` renders a field-ready PDF with inspection checklist, observations box, pass/fail, and signature lines.

---

## Design decisions

**Asset normalisation** — the PM tracker has 15+ spellings for the same equipment (`"Fire Ext."`, `"Walk-IN Chiller"`, `"A/C Plant"`). I normalised these to ~18 canonical `CB Asset Type` records via an `ASSET_ALIASES` dict in the import script rather than creating duplicate asset types.

**Store assets inferred, not assumed** — only outlet + asset pairs that actually appear in the PM tracker get a `CB Store Asset` record. Assuming every outlet has every asset type would create thousands of phantom tasks.

**Blank frequency → one-time** — rows with no frequency in the legacy sheet are imported as `One-time` and excluded from auto-recurrence. Treating them as monthly (the most common frequency) would silently schedule unwanted work.

**Notification fixture + Python scheduler** — the `Notification` doctype fixture handles the declarative case (role-based, zero code). The Python scheduler adds precise zonal routing that the declarative model can't express. Both coexist.

**Scope cut** — no ERPNext Asset module integration, no mobile interface, no WhatsApp. The daily scheduler is the overdue escalation hook; the reporting layer covers visibility.

---

## Walkthrough

**New store opens?**
Create `CB Outlet` (code + city) → create `CB Store Asset` rows. The `after_insert` hook scans active PM programs for that asset type and creates all PM tasks automatically.

**AC coil cleaning → bi-monthly chain-wide?**
Edit the frequency on the `AC Plant PM Program` task row → **Roll Out to Stores**. Stores with an open task for that task name are skipped. Future recurrence follows the new frequency after completion.

**Records after 1 year / 5 years?**

| Table | 1 yr | 5 yr |
|---|---|---|
| CB PM Program | ~18 | ~18 |
| CB Store Asset | ~1,300 | ~1,400 |
| CB PM Task | ~25,000 | ~125,000 |
| CB Maintenance Ticket | ~2,000–5,000 | ~10,000–25,000 |

List views filter on indexed fields (`status`, `outlet`, `due_date`). The PM Health report aggregates everything in a single query.

**Route a ticket to the right technician?**
`outlet.city` → city-to-office map → `CB Maintenance Team Member` where `zonal_office = X AND is_incharge = 1` → fall back to first active member. Runs in `validate()` so every ticket arrives pre-assigned.

---

## Run locally

```bash
colima start && export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock
docker-compose up --build
# then in a second terminal:
docker compose exec frappe bench --site site1.local execute cb_maintenance.maintenance_ops.setup.import_case_data.run
```

Site at `http://localhost:8000` — `Administrator` / `admin`.

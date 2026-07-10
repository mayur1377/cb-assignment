# Maintenance Ops (cb_maintenance)

Frappe custom app for California Burrito's store maintenance operations — preventive maintenance (PM) scheduling and reactive tickets.

## What this ships

- **Define PM once, roll out everywhere** — `CB PM Program` ties tasks + frequencies to an asset type; one click rolls tasks to all active `CB Store Asset` records.
- **Due / overdue tracking** — daily scheduler refreshes PM task status.
- **Reactive tickets** — raise `CB Maintenance Ticket` against an outlet/asset with taxonomy from the case data.
- **PM failure → ticket** — mark a PM task as Failed and the system opens a linked ticket, routes to the zonal incharge, and suggests spare parts when possible.
- **Zonal routing** — outlet city → zonal office → default technician assignment.

## DocTypes

| DocType | Purpose |
|---|---|
| CB Zonal Office | City zonal offices |
| CB Outlet | 133 stores with city code |
| CB Asset Type | Normalized equipment taxonomy |
| CB PM Program | Recurring PM tasks per asset type |
| CB Store Asset | Asset instance at a store |
| CB PM Task | Scheduled / due / overdue / completed work |
| CB Issue Type | Ticket taxonomy (Maintenance + Spare Parts) |
| CB Spare Part | Coded spare parts catalog |
| CB Maintenance Team Member | Technicians + reporting chain |
| CB Maintenance Ticket | Reactive + PM-failure tickets |

## Deploy to Frappe Cloud (recommended)

1. Create a free [Frappe Cloud](https://frappecloud.com) site (ERPNext optional — this app works on plain Frappe).
2. Upload or connect this app:
   ```bash
   # on your bench
   bench get-app https://github.com/<you>/cb_maintenance
   bench --site <site> install-app cb_maintenance
   bench --site <site> migrate
   ```
3. Import seed data from the case package:
   ```bash
   bench --site <site> execute cb_maintenance.maintenance_ops.setup.import_case_data.run
   ```
4. Roll out PM programs (or open each `CB PM Program` and click **Roll Out to Stores**).
5. Create a **Maintenance Manager** user and share the **Maintenance Ops** workspace.

## Local bench setup

```bash
# Requires Python 3.10+, Node 18+, Redis, MariaDB
pip install frappe-bench
bench init cb-bench --frappe-branch version-15
cd cb-bench
bench get-app /path/to/cb_maintenance
bench new-site cb.local
bench --site cb.local install-app cb_maintenance
bench start
```

Then import data as above.

## Docker setup (recommended)

This repository now includes a Docker-based local environment using `docker-compose`.

```bash
# Install Docker Desktop or Colima + Docker CLI on macOS
brew install docker colima
colima start

# If Colima is used, point Docker to the Colima socket
export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock

docker-compose up --build
```

After the first run, open `http://localhost:8000`.

Default local site:
- Site: `site1.local`
- Admin password: `admin`

Import the case seed data with:

```bash
docker compose exec frappe bench --site site1.local execute cb_maintenance.maintenance_ops.setup.import_case_data.run
```

## Design choices (assumptions)

- **Asset normalization** — messy spreadsheet names (e.g. "Fire Ext.", "Walk-IN Chiller") map to canonical `CB Asset Type` records; aliases are stored for traceability.
- **Frequency gaps** — rows with blank frequency in the legacy sheet are treated as one-time/ad-hoc tasks and excluded from auto-recurrence.
- **Store assets** — inferred from the PM tracker (outlet + asset pairs), not assumed every outlet has every asset type.
- **Scope cut** — no full ERPNext Asset module integration, no mobile app, no WhatsApp alerts (daily scheduler is the overdue notification hook).

## Walkthrough Q&A

### A new store opens — what do you create?
1. Create a `CB Outlet` (code + city). The city field auto-links it to the right `CB Zonal Office`.
2. Create a `CB Store Asset` for each piece of equipment at that outlet (outlet + asset type).
3. That's it. The `after_insert` hook on `CB Store Asset` scans all active `CB PM Program` records for that asset type and creates `CB PM Task` rows automatically. The new store is fully scheduled within seconds.

### We want AC coil cleaning bi-monthly chain-wide — what do you touch?
Open the `AC Plant PM Program`, find the coil-cleaning task row, change its frequency to `6 month` (the closest option to bi-monthly). Click **Roll Out to Stores**. The rollout creates new tasks only for store assets that don't already have an open task for that task name — so existing in-progress tasks aren't disturbed. Going forward, `generate_recurring_pm_tasks` (daily scheduler) uses the new frequency when creating the next task after each completion.

### How many records after 1 year / 5 years?
The volumes stay manageable because **templates stay small, only instances grow**:

| Table | After 1 year | After 5 years | Notes |
|---|---|---|---|
| `CB PM Program` | ~18 | ~18 | One per asset type — never grows |
| `CB Store Asset` | ~1,300 | ~1,400 | ~10 assets × 133 stores |
| `CB PM Task` | ~25,000 | ~125,000 | ~1,300 assets × avg 4 tasks × 5 recurrences/yr |
| `CB Maintenance Ticket` | ~2,000–5,000 | ~10,000–25,000 | Depends on failure rate |

Query pattern is always filtered by `status` or `outlet` — indexed fields — so list views stay fast even at 100k+ PM tasks. The **PM Health by Outlet** report aggregates this at query time.

### How would you route a ticket to the right technician?
`CB Outlet.city` → lookup `CB Zonal Office` (hardcoded 5-city map, set on save) → query `CB Maintenance Team Member` where `zonal_office = X AND is_incharge = 1` → fall back to first active member if no incharge flagged. This runs in `CBMaintenanceTicket.validate()` so every new ticket (reactive or PM-failure-generated) arrives pre-assigned.

## License

MIT

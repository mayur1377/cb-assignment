# Build Exercise: Maintenance Operations in Frappe

**Time:** 90 minutes, live/paired with us on a call.
**Setup:** We'll give you a running Frappe/ERPNext bench. Setup time doesn't count against you.
**AI tools:** Encouraged — use whatever you'd use on the job. We care how you *direct* and *edit* AI output, not whether you recall Frappe syntax.

---

## The situation

We run California Burrito — a fast-casual chain with 130+ stores across six Indian cities. Every store runs a fleet of equipment (ACs, walk-in chillers, fryers, DG sets, fire extinguishers, RO plants, grease traps, and ~40 other asset types). Two things happen to that equipment:

1. **Planned** — preventive maintenance on a recurring schedule (filters monthly, coils quarterly, fire-extinguisher service annually, grease traps weekly).
2. **Unplanned** — things break and someone raises a ticket ("AC not cooling", "chest freezer gasket broken").

A team of ~40 maintenance staff, organised by city zonal offices and a reporting chain, keeps it all running. Today this lives in a pile of spreadsheets. Your job is to build the Frappe system that replaces them.

## The data (in the package)

| File | What it is |
|---|---|
| `PM_Case_Before.xlsx` | How preventive maintenance is tracked today. A real, messy export. |
| `PM_Case_Outlets.xlsx` | Store master: 133 outlets, each with a 3-letter code and city. |
| `PM_Case_User_Master.csv` | The maintenance team: role, reporting line, and home zonal office. |
| `PM_Case_Ticket_Buckets.xlsx` | The ticket taxonomy (Dept → Category → Sub-category) and a coded spare-parts catalog. |

These came out of four different systems. Part of the exercise is seeing how they relate.

## Your task

Build, in Frappe, the core of this maintenance system. We are **not** asking you to migrate the files or reproduce their layout — model the problem properly and ship a working slice.

A reasonable v1 lets us:

1. Define the PM program once — which tasks each kind of asset needs, and how often — and roll it across many stores without re-entering per store.
2. See what's **due / overdue** and mark it done.
3. Raise a reactive ticket against an asset at a store.
4. Handle the awkward bits in the data gracefully rather than crashing or producing silent nonsense.

## Go further (this is where you distinguish yourself)

A v1 that just schedules PM is a pass. What we're really curious about is how *interesting* a system you can build from how these four files connect. We're not prescribing any of these — they're directions past candidates found worth pursuing. Pick what excites you and what you can ship:

- The planned and unplanned worlds share an equipment taxonomy. Is "PM task" and "ticket" really one thing wearing two hats?
- An outlet sits in a city; a city has a zonal office; a zonal office has technicians with a reporting chain. What can you do with that path?
- A ticket says "Gasket Broken" on a chest freezer. The spare-parts catalog has a part code for exactly that. Can the system help?
- A PM inspection says "check gasket, replace if required" — and it fails. Then what?
- An item goes overdue. Who hears about it, and when?

We'd rather see one of these built thoughtfully than all of them gestured at.

## Ground rules

- Use Frappe the way it wants to be used. Lean on its primitives.
- Ship something that runs. A small working slice beats a large broken one.
- Cutting scope is expected — just be ready to tell us **what you cut and why.**
- If the data is ambiguous, make a call, note the assumption, move on. Asking good questions is fair game too.

## What to hand over

Two things, both required:

1. **A live link we can use.** Build on a hosted Frappe site (a free Frappe Cloud trial is fine) and share the URL plus a login for us — the system back-office needs an account, so a link alone won't open. We want to click through the real thing, not screenshots.
2. **Your code.** Push your custom app to a **public GitHub repo** and share the link (from your bench: `cd apps/<your_app>`, then `git init && git add -A && git commit -m "case" `, create the repo on GitHub, `git remote add origin <url> && git push -u origin main`). If you'd rather not use GitHub, zip the `apps/<your_app>` folder and send the `.zip`. Either way, we only need *your* app — not the stock Frappe/ERPNext code around it.

## The walkthrough (~15 min after)

Expect questions like: *A new store opens — what do you create? We move AC coil-cleaning to bi-monthly chain-wide — what do you touch? How many records exist after a year, after five? How would you route a ticket to the right technician?* No trick answers; we want to see how you think about the shape of the problem.

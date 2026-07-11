"""PM Health by Outlet — Script Report.

Answers the walkthrough question: "How many records after 1 year / 5 years?"
Shows per-outlet PM task completion rate, overdue count, and open ticket count.
Color-coded: red = struggling outlet, green = healthy.
"""

import frappe


def execute(filters=None):
    filters = filters or {}

    columns = _get_columns()
    data = _get_data(filters)
    chart = _get_chart(data)
    summary = _get_summary(data)

    return columns, data, None, chart, summary


def _get_columns():
    return [
        {
            "label": "Outlet",
            "fieldname": "outlet",
            "fieldtype": "Link",
            "options": "CB Outlet",
            "width": 100,
        },
        {
            "label": "City",
            "fieldname": "city",
            "fieldtype": "Data",
            "width": 70,
        },
        {
            "label": "Zonal Office",
            "fieldname": "zonal_office",
            "fieldtype": "Link",
            "options": "CB Zonal Office",
            "width": 160,
        },
        {
            "label": "Total Tasks",
            "fieldname": "total",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Completed",
            "fieldname": "completed",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Due",
            "fieldname": "due",
            "fieldtype": "Int",
            "width": 80,
        },
        {
            "label": "Overdue",
            "fieldname": "overdue",
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "label": "Failed",
            "fieldname": "failed",
            "fieldtype": "Int",
            "width": 80,
        },
        {
            "label": "Open Tickets",
            "fieldname": "open_tickets",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": "Completion %",
            "fieldname": "completion_pct",
            "fieldtype": "Percent",
            "width": 120,
        },
        {
            "label": "Health",
            "fieldname": "health",
            "fieldtype": "Data",
            "width": 100,
        },
    ]


def _get_data(filters):
    conditions = ""
    if filters.get("city"):
        conditions += " AND o.city = %(city)s"
    if filters.get("zonal_office"):
        conditions += " AND o.zonal_office = %(zonal_office)s"

    # PM task counts per outlet
    task_rows = frappe.db.sql(
        f"""
        SELECT
            sa.outlet,
            o.city,
            o.zonal_office,
            COUNT(*)                                                    AS total,
            SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END)    AS completed,
            SUM(CASE WHEN t.status = 'Due'       THEN 1 ELSE 0 END)    AS due,
            SUM(CASE WHEN t.status = 'Overdue'   THEN 1 ELSE 0 END)    AS overdue,
            SUM(CASE WHEN t.status = 'Failed'    THEN 1 ELSE 0 END)    AS failed
        FROM `tabCB PM Task` t
        JOIN `tabCB Store Asset` sa ON sa.name = t.store_asset
        JOIN `tabCB Outlet`      o  ON o.name  = sa.outlet
        WHERE 1=1 {conditions}
        GROUP BY sa.outlet, o.city, o.zonal_office
        ORDER BY overdue DESC, o.city
        """,
        filters,
        as_dict=True,
    )

    # Open ticket count per outlet
    ticket_counts = {
        r.outlet: r.cnt
        for r in frappe.db.sql(
            """
            SELECT outlet, COUNT(*) AS cnt
            FROM `tabCB Maintenance Ticket`
            WHERE status IN ('Open','In Progress')
            GROUP BY outlet
            """,
            as_dict=True,
        )
    }

    data = []
    for row in task_rows:
        total = row.total or 0
        completed = row.completed or 0
        overdue = row.overdue or 0
        failed = row.failed or 0
        pct = round(completed / total * 100, 1) if total else 0.0
        open_tickets = ticket_counts.get(row.outlet, 0)

        if overdue > 3 or pct < 50:
            health = "🔴 At Risk"
        elif overdue > 0 or pct < 80:
            health = "🟡 Watch"
        else:
            health = "🟢 Healthy"

        data.append(
            {
                "outlet": row.outlet,
                "city": row.city,
                "zonal_office": row.zonal_office,
                "total": total,
                "completed": completed,
                "due": row.due or 0,
                "overdue": overdue,
                "failed": failed,
                "open_tickets": open_tickets,
                "completion_pct": pct,
                "health": health,
            }
        )

    return data


def _get_chart(data):
    if not data:
        return None

    # Top 15 outlets by overdue count for the bar chart
    top = sorted(data, key=lambda r: r["overdue"], reverse=True)[:15]
    return {
        "data": {
            "labels": [r["outlet"] for r in top],
            "datasets": [
                {"name": "Overdue",   "values": [r["overdue"]   for r in top]},
                {"name": "Completed", "values": [r["completed"] for r in top]},
            ],
        },
        "type": "bar",
        "colors": ["#C8102E", "#27AE60"],
        "title": "PM Tasks — Overdue vs Completed (top outlets)",
    }


def _get_summary(data):
    if not data:
        return []

    total_tasks   = sum(r["total"]        for r in data)
    total_overdue = sum(r["overdue"]      for r in data)
    total_done    = sum(r["completed"]    for r in data)
    total_tickets = sum(r["open_tickets"] for r in data)
    at_risk       = sum(1 for r in data if "At Risk" in r["health"])

    overall_pct = round(total_done / total_tasks * 100, 1) if total_tasks else 0.0

    return [
        {"value": total_tasks,   "label": "Total PM Tasks",     "datatype": "Int",     "color": "blue"},
        {"value": overall_pct,   "label": "Overall Completion", "datatype": "Percent", "color": "green"},
        {"value": total_overdue, "label": "Overdue Tasks",      "datatype": "Int",     "color": "red"},
        {"value": total_tickets, "label": "Open Tickets",       "datatype": "Int",     "color": "orange"},
        {"value": at_risk,       "label": "At-Risk Outlets",    "datatype": "Int",     "color": "red"},
    ]

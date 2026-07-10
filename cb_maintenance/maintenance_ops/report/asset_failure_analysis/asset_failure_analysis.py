"""Asset Failure Analysis — Script Report.

Connects the PM tracker with the ticket taxonomy and spare parts catalog —
the "how these four files connect" insight the brief asks for.

Shows: which asset types fail PM most often, which issue types recur,
which spare parts are needed most. Useful for procurement and prioritisation.
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
            "label": "Asset Type",
            "fieldname": "asset_type",
            "fieldtype": "Link",
            "options": "CB Asset Type",
            "width": 160,
        },
        {
            "label": "Total PM Tasks",
            "fieldname": "total_tasks",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": "PM Failures",
            "fieldname": "failures",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": "Failure Rate %",
            "fieldname": "failure_rate",
            "fieldtype": "Percent",
            "width": 120,
        },
        {
            "label": "Reactive Tickets",
            "fieldname": "reactive_tickets",
            "fieldtype": "Int",
            "width": 130,
        },
        {
            "label": "Total Issues",
            "fieldname": "total_issues",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": "Top Issue Category",
            "fieldname": "top_issue",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Most Needed Spare Part",
            "fieldname": "top_spare",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Stores Affected",
            "fieldname": "stores_affected",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": "Risk",
            "fieldname": "risk",
            "fieldtype": "Data",
            "width": 90,
        },
    ]


def _get_data(filters):
    # PM failure counts per asset type
    pm_rows = frappe.db.sql(
        """
        SELECT
            sa.asset_type,
            COUNT(*)                   AS total_tasks,
            SUM(t.status = 'Failed')   AS failures,
            COUNT(DISTINCT sa.outlet)  AS stores_affected
        FROM `tabCB PM Task`    t
        JOIN `tabCB Store Asset` sa ON sa.name = t.store_asset
        GROUP BY sa.asset_type
        ORDER BY failures DESC
        """,
        as_dict=True,
    )

    # Reactive ticket counts per asset type
    ticket_rows = {
        r.asset_type: r.cnt
        for r in frappe.db.sql(
            """
            SELECT sa.asset_type, COUNT(*) AS cnt
            FROM `tabCB Maintenance Ticket` tk
            JOIN `tabCB Store Asset` sa ON sa.name = tk.store_asset
            WHERE tk.source = 'Reactive'
            GROUP BY sa.asset_type
            """,
            as_dict=True,
        )
    }

    # Most common issue category per asset type (via tickets)
    top_issue_rows = frappe.db.sql(
        """
        SELECT
            sa.asset_type,
            it.category,
            COUNT(*) AS cnt
        FROM `tabCB Maintenance Ticket` tk
        JOIN `tabCB Store Asset` sa ON sa.name = tk.store_asset
        JOIN `tabCB Issue Type`  it ON it.name = tk.issue_type
        GROUP BY sa.asset_type, it.category
        ORDER BY cnt DESC
        """,
        as_dict=True,
    )
    top_issue_map = {}
    for r in top_issue_rows:
        if r.asset_type not in top_issue_map:
            top_issue_map[r.asset_type] = r.category

    # Most needed spare part per asset type (via tickets)
    spare_rows = frappe.db.sql(
        """
        SELECT
            sa.asset_type,
            sp.part_name,
            COUNT(*) AS cnt
        FROM `tabCB Maintenance Ticket` tk
        JOIN `tabCB Store Asset` sa ON sa.name = tk.store_asset
        JOIN `tabCB Spare Part`  sp ON sp.name = tk.spare_part
        GROUP BY sa.asset_type, sp.part_name
        ORDER BY cnt DESC
        """,
        as_dict=True,
    )
    spare_map = {}
    for r in spare_rows:
        if r.asset_type not in spare_map:
            spare_map[r.asset_type] = r.part_name

    data = []
    for row in pm_rows:
        total = row.total_tasks or 0
        failures = row.failures or 0
        reactive = ticket_rows.get(row.asset_type, 0)
        total_issues = failures + reactive
        failure_rate = round(failures / total * 100, 1) if total else 0.0

        if failure_rate > 20 or total_issues > 10:
            risk = "🔴 High"
        elif failure_rate > 10 or total_issues > 4:
            risk = "🟡 Medium"
        else:
            risk = "🟢 Low"

        data.append(
            {
                "asset_type": row.asset_type,
                "total_tasks": total,
                "failures": failures,
                "failure_rate": failure_rate,
                "reactive_tickets": reactive,
                "total_issues": total_issues,
                "top_issue": top_issue_map.get(row.asset_type, "—"),
                "top_spare": spare_map.get(row.asset_type, "—"),
                "stores_affected": row.stores_affected or 0,
                "risk": risk,
            }
        )

    return data


def _get_chart(data):
    if not data:
        return None

    top = sorted(data, key=lambda r: r["total_issues"], reverse=True)[:12]
    return {
        "data": {
            "labels": [r["asset_type"] for r in top],
            "datasets": [
                {"name": "PM Failures",       "values": [r["failures"]        for r in top]},
                {"name": "Reactive Tickets",  "values": [r["reactive_tickets"] for r in top]},
            ],
        },
        "type": "bar",
        "colors": ["#C8102E", "#F4821F"],
        "title": "Issues by Asset Type (PM Failures + Reactive Tickets)",
    }


def _get_summary(data):
    if not data:
        return []

    high_risk = sum(1 for r in data if "High" in r["risk"])
    total_failures = sum(r["failures"] for r in data)
    total_reactive = sum(r["reactive_tickets"] for r in data)
    worst = max(data, key=lambda r: r["failure_rate"]) if data else {}

    return [
        {"value": len(data),       "label": "Asset Types Tracked",  "datatype": "Int", "color": "blue"},
        {"value": total_failures,  "label": "PM Failures",           "datatype": "Int", "color": "red"},
        {"value": total_reactive,  "label": "Reactive Tickets",      "datatype": "Int", "color": "orange"},
        {"value": high_risk,       "label": "High-Risk Asset Types", "datatype": "Int", "color": "red"},
        {
            "value": worst.get("asset_type", "—"),
            "label": "Highest Failure Rate",
            "datatype": "Data",
            "color": "red",
        },
    ]

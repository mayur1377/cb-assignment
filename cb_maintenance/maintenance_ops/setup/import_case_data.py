"""Import case-study seed data into a Frappe site.

Run from bench:
    bench --site <site> execute cb_maintenance.maintenance_ops.setup.import_case_data.run
"""

from __future__ import annotations

import re
from pathlib import Path

import frappe

DATA_DIR = Path(__file__).resolve().parents[3] / "case_data"

ASSET_ALIASES = {
	"A/C Plant": "AC Plant",
	"AC": "AC",
	"Air Conditioner / AC Plant / FCU / AHU": "AC Plant",
	"Aircon Unit": "AC",
	"Chest Freezer": "Chest Freezer",
	"DG Set & AMF Panel": "DG Set",
	"Drain Lines / Grease Trap": "Grease Trap",
	"Fire Ext.": "Fire Extinguisher",
	"Fire Extinguisher": "Fire Extinguisher",
	"Fire Extingushers": "Fire Extinguisher",
	"Fryers": "Fryer",
	"Hot Line/Warmer": "Hot Line Warmer",
	"Ice Cube Machine": "Ice Cube Machine",
	"Kitchen Exhaust Fan": "Kitchen Exhaust Fan",
	"RO Plant": "RO Plant",
	"Tortila Press": "Tortilla Press",
	"WIC": "Walk-in Chiller",
	"Walk in Chiller": "Walk-in Chiller",
	"Walk-IN Chiller": "Walk-in Chiller",
}

FREQ_MAP = {
	"Weekly": "Weekly",
	"Monthly": "Monthly",
	"Qtrly": "Qtrly",
	"Yearly": "Yearly",
	"6 month": "6 month",
}


@frappe.whitelist()
def run(data_dir: str | None = None):
	"""Entry point for bench execute and whitelisted API call."""
	import pandas as pd

	base = Path(data_dir) if data_dir else _find_data_dir()
	if not base.exists():
		frappe.throw(f"Case data folder not found: {base}")

	frappe.flags.in_import = True
	try:
		_import_outlets(pd.read_excel(base / "PM_Case_Outlets.xlsx"))
		_import_team(pd.read_csv(base / "PM_Case_User_Master.csv"))
		_import_issue_types_and_parts(pd.read_excel(base / "PM_Case_Ticket_Buckets.xlsx"))
		_import_pm_program(pd.read_excel(base / "PM_Case_Before.xlsx"))
		_rollout_programs()
		frappe.db.commit()
	finally:
		frappe.flags.in_import = False

	frappe.msgprint("Case data import completed.")


def _find_data_dir() -> Path:
	candidates = [
		Path(__file__).resolve().parents[3] / "case_data",
		Path(frappe.get_site_path("private/files/case_data")),
	]
	for path in candidates:
		if (path / "PM_Case_Outlets.xlsx").exists():
			return path
	return candidates[0]


def _import_outlets(df):
	for _, row in df.iterrows():
		code = str(row["Outlet Code"]).strip()
		city = str(row["City"]).strip().upper()
		if frappe.db.exists("CB Outlet", code):
			continue
		frappe.get_doc(
			{"doctype": "CB Outlet", "outlet_code": code, "city": city, "is_active": 1}
		).insert(ignore_permissions=True)


def _import_team(df):
	maint = df[df["Department"].astype(str).str.lower() == "maintenance"].copy()
	name_to_emp = {}
	for _, row in maint.iterrows():
		emp_no = str(row["Employee No"]).strip()
		zonal = str(row["Home"]).strip()
		if zonal == "COR":
			continue
		if not frappe.db.exists("CB Zonal Office", zonal):
			frappe.get_doc(
				{"doctype": "CB Zonal Office", "zonal_office_name": zonal, "city_codes": ""}
			).insert(ignore_permissions=True)
		title = str(row.get("Job title", "")).strip().lower()
		doc = frappe.get_doc(
			{
				"doctype": "CB Maintenance Team Member",
				"employee_no": emp_no,
				"full_name": str(row["Name"]).strip(),
				"job_title": str(row.get("Job title", "")).strip(),
				"email": str(row.get("Email", "")).strip(),
				"mobile": str(row.get("Mobile", "")).strip(),
				"zonal_office": zonal,
				"is_incharge": 1 if "incharge" in title or "leader" in title else 0,
				"is_active": 1,
			}
		)
		if frappe.db.exists("CB Maintenance Team Member", emp_no):
			continue
		doc.insert(ignore_permissions=True)
		name_to_emp[str(row["Name"]).strip().lower()] = emp_no

	for _, row in maint.iterrows():
		manager_name = str(row.get("Reports to", "")).strip().lower()
		emp_no = str(row["Employee No"]).strip()
		manager_emp = name_to_emp.get(manager_name)
		if manager_emp and frappe.db.exists("CB Maintenance Team Member", emp_no):
			frappe.db.set_value("CB Maintenance Team Member", emp_no, "reports_to", manager_emp)


def _import_issue_types_and_parts(df):
	for _, row in df.iterrows():
		dept = str(row["Department"]).strip()
		category = str(row["Category"]).strip()
		sub1 = "" if str(row.get("Sub Category 1", "")).strip() in ("nan", "") else str(row["Sub Category 1"]).strip()
		sub2 = "" if str(row.get("Sub Category 2", "")).strip() in ("nan", "") else str(row["Sub Category 2"]).strip()
		if dept not in ("Maintenance", "Spare Parts"):
			continue
		key = (dept, category, sub1, sub2)
		existing = frappe.db.exists(
			"CB Issue Type",
			{
				"department": dept,
				"category": category,
				"sub_category_1": sub1 or "",
				"sub_category_2": sub2 or "",
			},
		)
		if not existing:
			issue = frappe.get_doc(
				{
					"doctype": "CB Issue Type",
					"department": dept,
					"category": category,
					"sub_category_1": sub1,
					"sub_category_2": sub2,
				}
			).insert(ignore_permissions=True)
			issue_name = issue.name
		else:
			issue_name = existing

		if dept == "Spare Parts" and sub1:
			match = re.match(r"^([A-Z0-9]+)\s+(.*)$", sub1)
			if not match:
				continue
			part_code, part_name = match.group(1), match.group(2).strip()
			if frappe.db.exists("CB Spare Part", part_code):
				continue
			frappe.get_doc(
				{
					"doctype": "CB Spare Part",
					"part_code": part_code,
					"equipment_category": category,
					"part_name": part_name,
					"issue_type": issue_name,
				}
			).insert(ignore_permissions=True)


def _import_pm_program(df):
	asset_types = set()
	for raw_asset in df["Asset"].dropna().unique():
		normalized = ASSET_ALIASES.get(str(raw_asset).strip(), str(raw_asset).strip())
		if not normalized or normalized.lower() == "nan":
			continue
		asset_types.add(normalized)
		if not frappe.db.exists("CB Asset Type", normalized):
			aliases = [a for a, n in ASSET_ALIASES.items() if n == normalized]
			frappe.get_doc(
				{
					"doctype": "CB Asset Type",
					"asset_type_name": normalized,
					"aliases": ", ".join(sorted(set(aliases + [normalized]))),
				}
			).insert(ignore_permissions=True)

	for normalized in asset_types:
		program_name = f"{normalized} PM Program"
		if frappe.db.exists("CB PM Program", program_name):
			continue
		rows = df[df["Asset"].map(lambda a: ASSET_ALIASES.get(str(a).strip(), str(a).strip()) == normalized)]
		tasks = []
		for _, row in rows[["Task", "Freq"]].drop_duplicates().iterrows():
			task = str(row["Task"]).strip()
			if not task or task.lower() == "nan":
				continue
			freq_raw = row["Freq"]
			freq = FREQ_MAP.get(str(freq_raw).strip(), "One-time") if str(freq_raw).strip() not in ("nan", "") else "One-time"
			tasks.append({"task": task, "frequency": freq})
		if not tasks:
			continue
		frappe.get_doc(
			{
				"doctype": "CB PM Program",
				"program_name": program_name,
				"asset_type": normalized,
				"is_active": 1,
				"tasks": tasks,
			}
		).insert(ignore_permissions=True)

	for _, row in df.drop_duplicates(subset=["Outlet", "Asset"]).iterrows():
		outlet = str(row["Outlet"]).strip()
		raw_asset = str(row["Asset"]).strip()
		if not outlet or outlet.lower() == "nan" or not raw_asset or raw_asset.lower() == "nan":
			continue
		asset_type = ASSET_ALIASES.get(raw_asset, raw_asset)
		if not frappe.db.exists("CB Outlet", outlet):
			continue
		name = f"{outlet}-{asset_type}"
		if frappe.db.exists("CB Store Asset", name):
			continue
		frappe.get_doc(
			{
				"doctype": "CB Store Asset",
				"outlet": outlet,
				"asset_type": asset_type,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)


def _rollout_programs():
	from cb_maintenance.maintenance_ops.utils.pm_scheduler import rollout_pm_program

	for program in frappe.get_all("CB PM Program", pluck="name"):
		rollout_pm_program(program)

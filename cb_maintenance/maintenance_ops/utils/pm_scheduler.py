import frappe
from frappe.utils import getdate, today

from cb_maintenance.maintenance_ops.utils import add_days_from_frequency


def refresh_pm_task_statuses():
	for name in frappe.get_all(
		"CB PM Task",
		filters={"status": ["in", ["Scheduled", "Due", "Overdue"]], "docstatus": ["<", 2]},
		pluck="name",
	):
		doc = frappe.get_doc("CB PM Task", name)
		was_overdue = doc.status == "Overdue"
		doc.set_status_from_due_date()
		doc.db_set("status", doc.status, update_modified=False)
		if doc.status == "Overdue" and not was_overdue:
			_notify_overdue(doc)


def _notify_overdue(doc):
	"""Email the zonal incharge (or any team member) when a PM task becomes overdue."""
	zonal_office = frappe.db.get_value("CB Store Asset", doc.store_asset, "zonal_office")
	if not zonal_office:
		return
	recipients = frappe.get_all(
		"CB Maintenance Team Member",
		filters={"zonal_office": zonal_office, "is_incharge": 1, "is_active": 1},
		fields=["full_name", "email"],
	)
	if not recipients:
		recipients = frappe.get_all(
			"CB Maintenance Team Member",
			filters={"zonal_office": zonal_office, "is_active": 1},
			fields=["full_name", "email"],
			limit=1,
		)
	to_emails = [r.email for r in recipients if r.get("email")]
	if not to_emails:
		return
	outlet_code = doc.outlet or frappe.db.get_value("CB Store Asset", doc.store_asset, "outlet")
	asset_type = doc.asset_type or frappe.db.get_value("CB Store Asset", doc.store_asset, "asset_type")
	frappe.sendmail(
		recipients=to_emails,
		subject=f"[Overdue] PM Task: {doc.task} at {outlet_code}",
		message=f"""
			<p>The following preventive maintenance task is now <b>overdue</b>:</p>
			<ul>
				<li><b>Task:</b> {doc.task}</li>
				<li><b>Asset:</b> {asset_type}</li>
				<li><b>Outlet:</b> {outlet_code}</li>
				<li><b>Due Date:</b> {doc.due_date}</li>
				<li><b>PM Task ID:</b> {doc.name}</li>
			</ul>
			<p>Please complete or raise a ticket at the earliest.</p>
		""",
		now=True,
	)


def generate_recurring_pm_tasks():
	"""Create the next PM task after a completed one when frequency is defined."""
	completed = frappe.get_all(
		"CB PM Task",
		filters={"status": "Completed", "result": "Passed", "frequency": ["is", "set"]},
		fields=["name", "store_asset", "task", "frequency", "completed_on", "pm_program_task"],
	)
	for row in completed:
		if not row.frequency or row.frequency == "One-time":
			continue
		if _has_open_task(row.store_asset, row.task):
			continue
		next_due = add_days_from_frequency(row.frequency, row.completed_on or today())
		if not next_due:
			continue
		_create_pm_task(
			store_asset=row.store_asset,
			task=row.task,
			frequency=row.frequency,
			due_date=next_due,
			pm_program_task=row.pm_program_task,
		)


def rollout_pm_program(pm_program: str):
	program = frappe.get_doc("CB PM Program", pm_program)
	assets = frappe.get_all(
		"CB Store Asset",
		filters={"asset_type": program.asset_type, "is_active": 1},
		pluck="name",
	)
	created = 0
	for store_asset in assets:
		for line in program.tasks:
			if not line.frequency or line.frequency == "One-time":
				continue
			if _has_open_task(store_asset, line.task):
				continue
			_create_pm_task(
				store_asset=store_asset,
				task=line.task,
				frequency=line.frequency,
				due_date=today(),
				pm_program_task=line.name,
			)
			created += 1
	return created


def create_tasks_for_store_asset(store_asset: str):
	asset = frappe.get_doc("CB Store Asset", store_asset)
	programs = frappe.get_all(
		"CB PM Program",
		filters={"asset_type": asset.asset_type, "is_active": 1},
		pluck="name",
	)
	created = 0
	for program_name in programs:
		program = frappe.get_doc("CB PM Program", program_name)
		for line in program.tasks:
			if not line.frequency or line.frequency == "One-time":
				continue
			if _has_open_task(store_asset, line.task):
				continue
			_create_pm_task(
				store_asset=store_asset,
				task=line.task,
				frequency=line.frequency,
				due_date=today(),
				pm_program_task=line.name,
			)
			created += 1
	return created


def _has_open_task(store_asset: str, task: str) -> bool:
	return bool(
		frappe.db.exists(
			"CB PM Task",
			{
				"store_asset": store_asset,
				"task": task,
				"status": ["in", ["Scheduled", "Due", "Overdue"]],
			},
		)
	)


def _create_pm_task(store_asset, task, frequency, due_date, pm_program_task=None):
	doc = frappe.get_doc(
		{
			"doctype": "CB PM Task",
			"store_asset": store_asset,
			"task": task,
			"frequency": frequency,
			"due_date": getdate(due_date),
			"pm_program_task": pm_program_task,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name

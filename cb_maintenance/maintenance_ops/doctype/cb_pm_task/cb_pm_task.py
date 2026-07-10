import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class CBPMTask(Document):
	def validate(self):
		if self.result == "Failed":
			self.status = "Failed"
		elif self.result == "Passed":
			self.status = "Completed"
			if not self.completed_on:
				self.completed_on = today()
		else:
			self.set_status_from_due_date()

	def on_update(self):
		if self.result == "Failed" and not self.linked_ticket:
			self.create_ticket_from_failure()

	def set_status_from_due_date(self):
		if self.status in ("Completed", "Failed"):
			return
		due = getdate(self.due_date)
		current = getdate(today())
		if current > due:
			self.status = "Overdue"
		elif current == due:
			self.status = "Due"
		else:
			self.status = "Scheduled"

	def create_ticket_from_failure(self):
		issue_type = self.get_default_issue_type()
		assigned_to = self.get_default_assignee()
		outlet = self.outlet or frappe.db.get_value("CB Store Asset", self.store_asset, "outlet")
		spare_part = self.get_suggested_spare_part(issue_type)
		ticket = frappe.get_doc(
			{
				"doctype": "CB Maintenance Ticket",
				"outlet": outlet,
				"store_asset": self.store_asset,
				"issue_type": issue_type,
				"spare_part": spare_part,
				"subject": f"PM failed: {self.task}",
				"description": self.notes or f"Preventive maintenance task failed for {self.task}.",
				"source": "PM Failure",
				"pm_task": self.name,
				"assigned_to": assigned_to,
			}
		)
		ticket.insert(ignore_permissions=True)
		frappe.db.set_value("CB PM Task", self.name, "linked_ticket", ticket.name)
		self.linked_ticket = ticket.name

	def get_suggested_spare_part(self, issue_type):
		if not issue_type:
			return None
		parts = frappe.get_all(
			"CB Spare Part",
			filters={"issue_type": issue_type},
			pluck="name",
			limit=1,
		)
		return parts[0] if parts else None

	def get_default_issue_type(self):
		if not self.pm_program_task:
			return self.guess_issue_type_from_task()
		issue_type = frappe.db.get_value(
			"CB PM Program Task",
			self.pm_program_task,
			"default_issue_type",
		)
		return issue_type or self.guess_issue_type_from_task()

	def guess_issue_type_from_task(self):
		task_lower = (self.task or "").lower()
		if "gasket" in task_lower or "gaskit" in task_lower:
			candidates = frappe.get_all(
				"CB Issue Type",
				filters={"sub_category_1": ["like", "%Gasket%"]},
				pluck="name",
				limit=1,
			)
			return candidates[0] if candidates else None
		return None

	def get_default_assignee(self):
		zonal_office = frappe.db.get_value("CB Store Asset", self.store_asset, "zonal_office")
		if not zonal_office:
			return None
		incharge = frappe.get_all(
			"CB Maintenance Team Member",
			filters={"zonal_office": zonal_office, "is_incharge": 1},
			pluck="name",
			limit=1,
		)
		if incharge:
			return incharge[0]
		members = frappe.get_all(
			"CB Maintenance Team Member",
			filters={"zonal_office": zonal_office},
			pluck="name",
			limit=1,
		)
		return members[0] if members else None


def before_save(doc, method=None):
	if doc.result == "Failed":
		doc.status = "Failed"
	elif doc.result == "Passed":
		doc.status = "Completed"
	else:
		doc.set_status_from_due_date()

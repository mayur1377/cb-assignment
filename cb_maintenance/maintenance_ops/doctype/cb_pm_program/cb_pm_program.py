import frappe
from frappe.model.document import Document

from cb_maintenance.maintenance_ops.utils.pm_scheduler import rollout_pm_program


class CBPMProgram(Document):
	@frappe.whitelist()
	def rollout(self):
		created = rollout_pm_program(self.name)
		frappe.msgprint(f"Created {created} PM task(s) across active store assets.")
		return created

import frappe
from frappe.model.document import Document


class CBMaintenanceTicket(Document):
	def validate(self):
		if self.store_asset and not self.outlet:
			self.outlet = frappe.db.get_value("CB Store Asset", self.store_asset, "outlet")
		if not self.assigned_to and self.outlet:
			self.assigned_to = self.get_default_assignee()

	def get_default_assignee(self):
		zonal_office = frappe.db.get_value("CB Outlet", self.outlet, "zonal_office")
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

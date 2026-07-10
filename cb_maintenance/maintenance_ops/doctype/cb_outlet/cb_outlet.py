import frappe
from frappe.model.document import Document

from cb_maintenance.maintenance_ops.utils import get_zonal_office_for_city


class CBOutlet(Document):
	def before_save(self):
		zonal_name = get_zonal_office_for_city(self.city)
		if zonal_name and frappe.db.exists("CB Zonal Office", zonal_name):
			self.zonal_office = zonal_name

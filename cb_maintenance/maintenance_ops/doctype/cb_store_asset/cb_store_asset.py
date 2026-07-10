import frappe
from frappe.model.document import Document

from cb_maintenance.maintenance_ops.utils.pm_scheduler import create_tasks_for_store_asset


class CBStoreAsset(Document):
	pass


def after_insert(doc, method=None):
	if getattr(frappe.flags, "in_import", False):
		return
	create_tasks_for_store_asset(doc.name)

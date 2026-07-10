import frappe

from cb_maintenance.maintenance_ops.utils import CITY_ZONAL_OFFICE


def after_install():
	create_roles()
	create_zonal_offices()


def create_roles():
	for role in ("Maintenance Manager", "Maintenance User"):
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def create_zonal_offices():
	for city_code, office_name in CITY_ZONAL_OFFICE.items():
		if frappe.db.exists("CB Zonal Office", office_name):
			continue
		frappe.get_doc(
			{
				"doctype": "CB Zonal Office",
				"zonal_office_name": office_name,
				"city_codes": city_code,
			}
		).insert(ignore_permissions=True)

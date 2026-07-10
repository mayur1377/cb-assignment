app_name = "cb_maintenance"
app_title = "Maintenance Ops"
app_publisher = "California Burrito"
app_description = "Preventive and reactive maintenance for store equipment"
app_email = "sanju.vp@californiaburrito.in"
app_license = "MIT"

required_apps = []


after_install = "cb_maintenance.install.after_install"

add_to_apps_screen = [
	{
		"name": "cb_maintenance",
		"logo": "/assets/cb_maintenance/images/cb_logo.svg",
		"title": "Maintenance Ops",
		"route": "/app/maintenance-ops",
		"has_permission": "cb_maintenance.api.permission.has_app_permission",
	}
]

doc_events = {
	"CB PM Task": {
		"before_save": "cb_maintenance.maintenance_ops.doctype.cb_pm_task.cb_pm_task.before_save",
	},
	"CB Store Asset": {
		"after_insert": "cb_maintenance.maintenance_ops.doctype.cb_store_asset.cb_store_asset.after_insert",
	},
}

scheduler_events = {
	"daily": [
		"cb_maintenance.maintenance_ops.utils.pm_scheduler.refresh_pm_task_statuses",
		"cb_maintenance.maintenance_ops.utils.pm_scheduler.generate_recurring_pm_tasks",
	],
}

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["module", "=", "Maintenance Ops"]],
	},
	{
		"dt": "Notification",
		"filters": [["name", "in", ["CB PM Task Overdue Alert"]]],
	},
	{
		"dt": "Print Format",
		"filters": [["name", "in", ["CB PM Task Checklist"]]],
	},
]

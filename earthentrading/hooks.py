app_name = "earthentrading"
app_title = "Earth Ent Trading"
app_publisher = "Earth Trading"
app_description = "Trading CRM for Earth"
app_email = "admin@earthentrading.local"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "earthentrading",
		"logo": "/assets/earthentrading/images/earth-hub.svg",
		"title": "Earth Trading Hub",
		"route": "/earthentrading",
		"has_permission": "earthentrading.api.permission.has_app_permission",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/earthentrading/css/earthentrading.css"
app_include_js = [
	"/assets/earthentrading/js/trade_report_widget.js?v=3",
	"/assets/earthentrading/js/selling_workspace_widget.js?v=1",
]

# include js, css files in header of web template
# web_include_css = "/assets/earthentrading/css/earthentrading.css"
# web_include_js = "/assets/earthentrading/js/earthentrading.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "earthentrading/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_list_js = {"Project": "public/js/project_list.js"}
doctype_js = {"Sales Order": "public/js/sales_order_assign_prompt.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "earthentrading/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "earthentrading.utils.jinja_methods",
# 	"filters": "earthentrading.utils.jinja_filters"
# }

# Installation
# ------------

before_install = "earthentrading.install.before_install"
after_install = "earthentrading.install.after_install"
after_migrate = "earthentrading.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "earthentrading.uninstall.before_uninstall"
# after_uninstall = "earthentrading.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "earthentrading.utils.before_app_install"
# after_app_install = "earthentrading.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "earthentrading.utils.before_app_uninstall"
# after_app_uninstall = "earthentrading.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "earthentrading.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Lead": "earthentrading.permissions.lead_query_conditions",
	"Opportunity": "earthentrading.permissions.opportunity_query_conditions",
	"Quotation": "earthentrading.permissions.quotation_query_conditions",
	"Sales Order": "earthentrading.permissions.sales_order_query_conditions",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Lead": {
		"validate": "earthentrading.events.lead.validate",
		"before_save": "earthentrading.events.lead.before_save",
	},
	"Opportunity": {
		"validate": "earthentrading.events.opportunity.validate",
		"before_insert": "earthentrading.events.opportunity.before_insert",
	},
	"Quotation": {
		"validate": "earthentrading.events.quotation.validate",
		"before_insert": "earthentrading.events.quotation.before_insert",
		"before_submit": "earthentrading.events.quotation.before_submit",
	},
	"Sales Order": {
		"validate": "earthentrading.events.sales_order.validate",
		"before_submit": "earthentrading.events.sales_order.before_submit",
	},
	"Project": {
		"after_insert": "earthentrading.events.project.after_insert",
		"on_update": "earthentrading.events.project.on_update",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"earthentrading.tasks.all"
# 	],
# 	"daily": [
# 		"earthentrading.tasks.daily"
# 	],
# 	"hourly": [
# 		"earthentrading.tasks.hourly"
# 	],
# 	"weekly": [
# 		"earthentrading.tasks.weekly"
# 	],
# 	"monthly": [
# 		"earthentrading.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "earthentrading.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.crm.doctype.lead.lead.make_opportunity": "earthentrading.overrides.lead.make_opportunity",
}

# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "earthentrading.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["earthentrading.utils.before_request"]
# after_request = ["earthentrading.utils.after_request"]

# Job Events
# ----------
# before_job = ["earthentrading.utils.before_job"]
# after_job = ["earthentrading.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"earthentrading.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Website Route Rules — SPA (same pattern as Dinematters / Mint catch-all → www page)
website_route_rules = [
	{"from_route": "/earthentrading/<path:app_path>", "to_route": "earthentrading"}
]


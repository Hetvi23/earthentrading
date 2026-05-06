import frappe


def has_app_permission():
	"""Allow any logged-in user (not Guest) to open the Earth Trading Hub app tile."""
	return bool(frappe.session.user) and frappe.session.user != "Guest"

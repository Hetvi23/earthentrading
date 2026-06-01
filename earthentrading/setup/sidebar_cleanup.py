# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Hide every public workspace except the two we want users to see (CRM,
Selling). Also drop the stale Earth Trading Hub / Earth Trading CRM
workspaces so they don't reappear in the sidebar."""

import frappe


KEEP_VISIBLE = {"CRM", "Selling"}
DROP_NAMES = {"Earth Trading Hub", "Earth Trading CRM"}


def trim_public_sidebar():
	# Delete the old Earth Trading workspaces we're replacing.
	for name in DROP_NAMES:
		if frappe.db.exists("Workspace", name):
			try:
				frappe.delete_doc(
					"Workspace", name, force=True, ignore_permissions=True
				)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"earthentrading.drop_workspace.{name}")

	# Hide every other public workspace from the sidebar.
	for name in frappe.get_all(
		"Workspace",
		filters={"public": 1, "name": ["not in", list(KEEP_VISIBLE)]},
		pluck="name",
	):
		try:
			frappe.db.set_value("Workspace", name, "is_hidden", 1, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"earthentrading.hide_workspace.{name}")

	# Ensure the two we want stay visible.
	for name in KEEP_VISIBLE:
		if frappe.db.exists("Workspace", name):
			frappe.db.set_value("Workspace", name, "is_hidden", 0, update_modified=False)

	frappe.db.commit()
	frappe.clear_cache()

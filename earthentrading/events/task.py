# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""When the last open task on a project-linked Sales Order is completed,
auto-transition the SO workflow from In Progress → Raise Invoice."""

import frappe

DONE_STATUSES = {"Completed", "Cancelled"}


def on_update(doc, method):
	# Only trigger when the task just moved into a terminal status.
	if doc.status not in DONE_STATUSES:
		return
	if not doc.project:
		return

	# Skip if we just inserted the task as part of a checklist spawn run —
	# during that bulk insert all tasks start as Open, which can't trigger.
	if getattr(doc.flags, "from_project", False):
		return

	# Find the linked Sales Order (standard ERPNext Project.sales_order link).
	project = frappe.db.get_value(
		"Project",
		doc.project,
		["name", "sales_order", "status"],
		as_dict=True,
	)
	if not project or not project.get("sales_order"):
		return

	so_name = project["sales_order"]
	ws = frappe.db.get_value("Sales Order", so_name, "workflow_state")
	if ws != "In Progress":
		# Only transition from In Progress. Defensive — if SO is already in
		# Raise Invoice / Completed / Claim / etc., don't bounce it backwards.
		return

	# Check remaining open tasks on the project.
	remaining = frappe.db.count(
		"Task",
		filters={"project": doc.project, "status": ["not in", list(DONE_STATUSES)]},
	)
	if remaining > 0:
		return

	# All tasks done — flip SO to Raise Invoice.
	try:
		frappe.db.set_value(
			"Sales Order",
			so_name,
			"workflow_state",
			"Raise Invoice",
			update_modified=False,
		)
		# Also close the project so it's clearly finished.
		frappe.db.set_value(
			"Project", doc.project, "status", "Completed", update_modified=False
		)
		frappe.db.commit()
	except Exception:
		frappe.log_error(
			frappe.get_traceback(), "earthentrading.task.transition_to_raise_invoice"
		)

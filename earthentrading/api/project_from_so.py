# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Create a Project from a submitted Sales Order with everything pre-filled
from the SO; the only inputs the user provides are the ET Task Template and
(optionally) an assignee for the spawned tasks."""

import frappe
from frappe import _

from earthentrading.events.project import spawn_et_checklist_from_project


@frappe.whitelist()
def create_from_sales_order(sales_order: str, template: str, assignee: str | None = None):
	if not sales_order:
		frappe.throw(_("Sales Order is required."))
	if not template:
		frappe.throw(_("ET Task Template is required."))

	so = frappe.get_doc("Sales Order", sales_order)

	if so.docstatus != 1:
		frappe.throw(_("Sales Order must be submitted before creating a Project."))

	if not frappe.db.exists("ET Task Template", template):
		frappe.throw(_("ET Task Template {0} not found.").format(template))

	# Avoid duplicate Projects for the same SO.
	existing = frappe.db.get_value(
		"Project", {"sales_order": so.name}, "name"
	) or frappe.db.get_value(
		"Project", {"project_name": _project_name_for(so)}, "name"
	)
	if existing:
		frappe.msgprint(
			_("Project {0} already exists for this Sales Order.").format(existing),
			indicator="orange",
		)
		return {"name": existing, "created": False}

	project = frappe.new_doc("Project")
	project.project_name = _project_name_for(so)
	project.customer = so.customer
	project.company = so.company
	if so.delivery_date:
		project.expected_end_date = so.delivery_date
	project.status = "Open"
	project.custom_et_task_template = template
	# Standard ERPNext Project doctype has a `sales_order` link field; use
	# it when present so the linkage is bidirectional.
	if "sales_order" in {df.fieldname for df in frappe.get_meta("Project").fields}:
		project.sales_order = so.name

	if assignee and frappe.db.exists("User", assignee):
		project.append("users", {"user": assignee})

	project.flags.ignore_permissions = True
	project.insert()

	# Spawn checklist tasks now — events/project.after_insert already does this
	# on a Project save, but calling explicitly makes the flow deterministic.
	try:
		spawn_et_checklist_from_project(project)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.create_from_sales_order")

	frappe.db.commit()
	return {"name": project.name, "created": True}


def _project_name_for(so) -> str:
	return f"Project — {so.name}"

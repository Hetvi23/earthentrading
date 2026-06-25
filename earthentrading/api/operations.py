# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Operations actions on submitted Sales Orders:
- assign_team_member: Operations picks a user, optionally a task template,
  grants the user view + write access to the SO via Frappe Share, creates
  the linked Project, spawns the checklist tasks, and transitions the SO
  workflow from "Pending Assignment" to "Person Assigned".
- raise_claim: Completed → Claim (flags a post-completion issue).
- resolve_claim: Claim → Completed (closes the order again; no re-run of operations).
"""

import json

import frappe
from frappe import _
from frappe.desk.form import assign_to
from frappe.share import add as share_add

from earthentrading.events.project import spawn_et_checklist_from_project


@frappe.whitelist()
def assign_team_member(sales_order: str, user: str, template: str | None = None):
	if not sales_order:
		frappe.throw(_("Sales Order is required."))
	if not user or not frappe.db.exists("User", user):
		frappe.throw(_("Pick a valid user."))

	so = frappe.get_doc("Sales Order", sales_order)
	if so.docstatus != 1:
		frappe.throw(_("Sales Order must be submitted first."))
	if so.workflow_state != "Pending Assignment":
		frappe.throw(
			_("Sales Order is in state {0}; assignment is only available in Pending Assignment.").format(
				so.workflow_state or _("unset")
			)
		)

	# 1. Grant the user read + write on this SO via Frappe Share.
	try:
		share_add(
			"Sales Order",
			sales_order,
			user,
			read=1,
			write=1,
			share=0,
			notify=1,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.assign.share")

	# 2. Add a ToDo so the user sees this SO in their inbox.
	try:
		assign_to.add(
			{
				"assign_to": [user],
				"doctype": "Sales Order",
				"name": sales_order,
				"description": _("Operations handler for Sales Order {0}").format(sales_order),
			},
			ignore_permissions=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.assign.todo")

	# 3. Create the Project (or reuse if it already exists for this SO).
	project_name = None
	if template:
		project_name = _ensure_project_for_so(so, template, user)

	# 4. Transition the SO to Person Assigned.
	frappe.db.set_value(
		"Sales Order",
		sales_order,
		"workflow_state",
		"Person Assigned",
		update_modified=False,
	)
	frappe.db.commit()

	return {"project": project_name, "assignee": user}


@frappe.whitelist()
def raise_claim(sales_order: str, note: str | None = None):
	so = frappe.db.get_value(
		"Sales Order", sales_order, ["name", "workflow_state"], as_dict=True
	)
	if not so:
		frappe.throw(_("Sales Order {0} not found.").format(sales_order))
	if so.workflow_state != "Completed":
		frappe.throw(
			_("Claim can only be raised on Completed Sales Orders (current: {0}).").format(
				so.workflow_state or _("unset")
			)
		)

	frappe.db.set_value(
		"Sales Order",
		sales_order,
		"workflow_state",
		"Claim",
		update_modified=False,
	)

	# A claim only flags an issue; it does NOT reopen the project or respawn
	# tasks. Record the reason as a comment on the SO for the audit trail.
	if note:
		try:
			comment = frappe.new_doc("Comment")
			comment.comment_type = "Comment"
			comment.reference_doctype = "Sales Order"
			comment.reference_name = sales_order
			comment.content = f"Claim raised: {note}"
			comment.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "earthentrading.claim.comment")

	frappe.db.commit()
	return {"ok": True}


@frappe.whitelist()
def resolve_claim(sales_order: str):
	so = frappe.db.get_value(
		"Sales Order", sales_order, ["name", "workflow_state"], as_dict=True
	)
	if not so:
		frappe.throw(_("Sales Order {0} not found.").format(sales_order))
	if so.workflow_state != "Claim":
		frappe.throw(
			_("Only Sales Orders in Claim can be resolved (current: {0}).").format(
				so.workflow_state or _("unset")
			)
		)
	frappe.db.set_value(
		"Sales Order",
		sales_order,
		"workflow_state",
		"Completed",
		update_modified=False,
	)
	frappe.db.commit()
	return {"ok": True}


def _ensure_project_for_so(so, template: str, user: str) -> str:
	"""Find or create a Project linked to the SO. Spawns the checklist tasks
	from the picked template and adds the user to the project team."""
	project_name = frappe.db.get_value("Project", {"sales_order": so.name}, "name")
	if project_name:
		project = frappe.get_doc("Project", project_name)
		project.custom_et_task_template = template
		# Add the user to the team if not already present.
		existing_users = {u.user for u in (project.users or [])}
		if user not in existing_users:
			project.append("users", {"user": user})
		project.flags.ignore_permissions = True
		project.save()
	else:
		project = frappe.new_doc("Project")
		project.project_name = f"Project — {so.name}"
		project.customer = so.customer
		project.company = so.company
		if so.delivery_date:
			project.expected_end_date = so.delivery_date
		project.status = "Open"
		project.custom_et_task_template = template
		if "sales_order" in {df.fieldname for df in frappe.get_meta("Project").fields}:
			project.sales_order = so.name
		project.append("users", {"user": user})
		project.flags.ignore_permissions = True
		project.insert()
		project_name = project.name

	# Spawn the tasks for the (re)assigned template.
	try:
		spawn_et_checklist_from_project(frappe.get_doc("Project", project_name))
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"earthentrading.assign.spawn.{project_name}",
		)

	return project_name

# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Create Tasks from ET Task Template when linked on a Project, with ToDos for the team."""

import json

import frappe
from frappe import _
from frappe.desk.form import assign_to
from frappe.utils import escape_html

LOG_NAME = "earthentrading.project_spawn_checklist"


def after_insert(doc, method):
	try:
		spawn_et_checklist_from_project(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), LOG_NAME)


def on_update(doc, method):
	try:
		spawn_et_checklist_from_project(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), LOG_NAME)


def spawn_et_checklist_from_project(doc) -> None:
	"""Insert one ERPNext Task per template line; allocate ToDos to team or row assignee."""
	if not doc.get("custom_et_task_template"):
		return
	if doc.status == "Cancelled":
		return
	# Idempotency guard. This runs from Project.after_insert AND Project.on_update
	# (both fire within a single insert), plus the explicit callers in
	# api/operations.py and api/project_from_so.py — up to 3 calls per request.
	# The in-memory flag goes stale after db.set_value(update_modified=False),
	# so re-read the persisted value before spawning, or we'd duplicate every
	# task (and its ToDo assignment).
	if doc.get("custom_et_checklist_spawned"):
		return
	if doc.name and frappe.db.get_value("Project", doc.name, "custom_et_checklist_spawned"):
		return

	tpl_key = frappe.db.exists("ET Task Template", doc.custom_et_task_template)
	if not tpl_key:
		frappe.msgprint(_("ET Task Template {0} does not exist; checklist skipped.").format(doc.custom_et_task_template), indicator="orange")
		return

	tpl = frappe.get_doc("ET Task Template", tpl_key)
	project_users = sorted({row.user for row in (doc.users or []) if row.user})
	fallback_assignees = []
	if getattr(doc, "owner", None) and frappe.db.exists("User", doc.owner):
		fallback_assignees = [doc.owner]

	cc = frappe.get_all("Company", pluck="name", limit_page_length=1)
	company = doc.company or frappe.db.get_single_value("Global Defaults", "default_company") or (cc[0] if cc else None)
	if not company:
		frappe.msgprint(_("Set Company on Project before spawning checklist tasks."), indicator="orange")
		return

	task_count = 0
	for row in tpl.tasks:
		assignees_for_row = []
		row_assignee = getattr(row, "assigned_to", None)
		if row_assignee:
			assignees_for_row = [row_assignee]
		else:
			assignees_for_row = project_users if project_users else fallback_assignees

		task_doc = frappe.get_doc(
			{
				"doctype": "Task",
				"subject": row.task_title,
				"project": doc.name,
				"status": "Open",
				"description": _instructions_to_html(row.instructions),
				"company": company,
			}
		)
		task_doc.flags.ignore_permissions = True
		task_doc.flags.from_project = True
		task_doc.insert()

		if assignees_for_row:
			assign_to.add(
				{
					"assign_to": json.dumps(assignees_for_row),
					"doctype": "Task",
					"name": task_doc.name,
					"description": _("Step: {0}").format(row.task_title),
				},
				ignore_permissions=True,
			)
		task_count += 1

	if task_count > 0:
		frappe.db.set_value(
			"Project",
			doc.name,
			"custom_et_checklist_spawned",
			1,
			update_modified=False,
		)
		# Keep the in-memory doc in sync so same-request callers also short-circuit.
		doc.custom_et_checklist_spawned = 1
		try:
			frappe.get_doc("Project", doc.name).update_project()
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"{LOG_NAME}_update_project")
		frappe.msgprint(
			_("Added {0} tasks from checklist template {1}").format(task_count, tpl.title),
			alert=False,
			indicator="green",
		)


def _instructions_to_html(text):
	t = (text or "").strip()
	if not t:
		return ""
	# Preserve simple pasted HTML; escape plain instructions.
	if "<" in t and ">" in t:
		return t
	return "<p>" + escape_html(t).replace("\n", "<br>") + "</p>"

# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Bulk-apply an ET Task Template to many Projects from the Desk list view."""

import frappe
from frappe import _

from earthentrading.events.project import spawn_et_checklist_from_project


@frappe.whitelist()
def bulk_assign_template(projects, template, overwrite=False):
	if isinstance(projects, str):
		projects = frappe.parse_json(projects)
	if not projects:
		frappe.throw(_("No projects selected."))
	if not template or not frappe.db.exists("ET Task Template", template):
		frappe.throw(_("ET Task Template {0} not found.").format(template))

	overwrite = frappe.parse_json(overwrite) if isinstance(overwrite, str) else bool(overwrite)

	results = {"spawned": [], "skipped": [], "errors": []}
	for name in projects:
		if not frappe.has_permission("Project", "write", doc=name):
			results["errors"].append({"project": name, "error": _("No write permission")})
			continue
		try:
			doc = frappe.get_doc("Project", name)
			already = bool(doc.get("custom_et_checklist_spawned"))
			if already and not overwrite:
				results["skipped"].append(name)
				continue
			if already and overwrite:
				doc.custom_et_checklist_spawned = 0
			doc.custom_et_task_template = template
			doc.save(ignore_permissions=False)
			spawn_et_checklist_from_project(doc)
			results["spawned"].append(name)
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "earthentrading.bulk_assign_template")
			results["errors"].append({"project": name, "error": str(e)})

	frappe.db.commit()
	return results

# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe
from frappe.permissions import add_permission

ET_ROLES = ("ET Director", "ET Trader", "ET Operations")


def ensure_roles():
	for role_name in ET_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}
		).insert(ignore_permissions=True)


def _upsert_custom_docperm(doctype: str, role: str, perm: dict):
	name = frappe.db.get_value(
		"Custom DocPerm",
		{"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0},
		"name",
	)
	if name:
		doc = frappe.get_doc("Custom DocPerm", name)
		for key, val in perm.items():
			doc.set(key, val)
		doc.save(ignore_permissions=True)
	else:
		row = {
			"doctype": "Custom DocPerm",
			"parent": doctype,
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": role,
			"permlevel": 0,
			"if_owner": 0,
			"select": 0,
			"read": 0,
			"write": 0,
			"create": 0,
			"delete": 0,
			"submit": 0,
			"cancel": 0,
			"amend": 0,
			"report": 0,
			"export": 0,
			"import": 0,
			"share": 0,
			"print": 0,
			"email": 0,
		}
		row.update(perm)
		frappe.get_doc(row).insert(ignore_permissions=True)


def ensure_role_permissions():
	"""Doc-level permissions; ET Trader row scope uses permission_query_conditions in hooks."""
	full = {
		"read": 1,
		"write": 1,
		"create": 1,
		"submit": 1,
		"cancel": 1,
		"amend": 1,
		"delete": 1,
		"print": 1,
		"email": 1,
		"export": 1,
		"report": 1,
		"share": 1,
	}
	trader = {
		**full,
		"delete": 0,
	}
	read_only = {"read": 1, "export": 1, "report": 1}

	crm = ("Lead", "Opportunity", "Quotation", "Sales Order", "Project")
	for dt in crm:
		_upsert_custom_docperm(dt, "ET Director", full)
		_upsert_custom_docperm(dt, "ET Trader", trader)

	party = ("Customer", "Supplier", "Contact")
	for dt in ("Task",):
		_upsert_custom_docperm(dt, "ET Director", full)
		_upsert_custom_docperm(dt, "ET Trader", trader)
		_upsert_custom_docperm(dt, "ET Operations", read_only)

	for dt in ("Lead", "Opportunity", "Project"):
		_upsert_custom_docperm(dt, "ET Operations", read_only)

	for dt in party:
		_upsert_custom_docperm(dt, "ET Director", full)
		_upsert_custom_docperm(dt, "ET Trader", trader)
		_upsert_custom_docperm(dt, "ET Operations", read_only)

	for dt in ("Quotation", "Sales Order"):
		_upsert_custom_docperm(dt, "ET Operations", read_only)

	# Task templates (checklists) — DocType may not exist on very first hook pass
	if frappe.db.exists("DocType", "ET Task Template"):
		_upsert_custom_docperm("ET Task Template", "ET Director", full)
		_upsert_custom_docperm("ET Task Template", "ET Trader", trader)
		_upsert_custom_docperm("ET Task Template", "ET Operations", read_only)

	for role in ET_ROLES:
		try:
			add_permission("User", role, 0, "read")
		except Exception:
			pass

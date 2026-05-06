# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe


def _earth_trading_lead_web_form_rows():
	"""Field layout for /earth-trading-lead (desk + website)."""
	return [
		{
			"fieldname": "company_name",
			"label": "Company / Organization",
			"fieldtype": "Data",
			"reqd": 1,
		},
		{
			"fieldname": "first_name",
			"label": "First Name",
			"fieldtype": "Data",
			"reqd": 1,
		},
		{
			"fieldname": "last_name",
			"label": "Last Name",
			"fieldtype": "Data",
		},
		{
			"fieldname": "email_id",
			"label": "Email",
			"fieldtype": "Data",
			"reqd": 1,
		},
		{
			"fieldname": "phone",
			"label": "Phone",
			"fieldtype": "Data",
		},
		{
			"fieldname": "country",
			"label": "Country",
			"fieldtype": "Link",
			"options": "Country",
		},
		{
			"fieldname": "custom_et_region",
			"label": "Region",
			"fieldtype": "Data",
		},
		{
			"fieldname": "custom_et_lines",
			"label": "Products (Item from catalogue — or specification if not listed)",
			"fieldtype": "Table",
			"options": "ET Lead Line",
		},
		{
			"fieldname": "custom_et_deal_type",
			"label": "Deal Type",
			"fieldtype": "Select",
			"options": "\nBrokerage\nPrincipal",
		},
		{
			"fieldname": "custom_et_incoterm",
			"label": "Incoterm",
			"fieldtype": "Link",
			"options": "Incoterm",
		},
	]


def ensure_lead_web_form():
	if frappe.db.exists("Web Form", {"route": "earth-trading-lead"}):
		return

	rows = _earth_trading_lead_web_form_rows()
	doc = frappe.get_doc(
		{
			"doctype": "Web Form",
			"title": "Earth Trading Lead",
			"route": "earth-trading-lead",
			"doc_type": "Lead",
			"module": "CRM",
			"is_standard": 0,
			"published": 1,
			"allow_multiple": 0,
			"allow_edit": 0,
			"allow_delete": 0,
			"login_required": 0,
			"anonymous": 1,
			"introduction_text": "<p>Submit your inquiry. Our team will contact you.</p>",
			"meta_title": "Earth Trading Lead",
			"show_in_grid": 0,
			"web_form_fields": [],
		}
	)
	for i, row in enumerate(rows, start=1):
		doc.append("web_form_fields", row)
		doc.web_form_fields[-1].idx = i
	doc.insert(ignore_permissions=True)
	frappe.db.commit()


def sync_earth_trading_lead_web_form():
	"""Rewrites Web Form fields (e.g. after adding ET Lead Line table)."""
	route = {"route": "earth-trading-lead"}
	if not frappe.db.exists("Web Form", route):
		ensure_lead_web_form()
		if not frappe.db.exists("Web Form", route):
			return
	wf_name = frappe.db.get_value("Web Form", route, "name")
	doc = frappe.get_doc("Web Form", wf_name)
	doc.web_form_fields = []
	for i, row in enumerate(_earth_trading_lead_web_form_rows(), start=1):
		doc.append("web_form_fields", row)
		doc.web_form_fields[-1].idx = i
	doc.save(ignore_permissions=True)

# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Seed a few Payment Terms Templates so the Sales Order 'Trade Payment' link
field has sensible options out of the box. Idempotent; safe to re-run."""

import frappe

DEFAULT_TEMPLATES = [
	"100% against scanned documents",
	"100% advance TT",
	"20% Advance, 80% against scanned documents",
	"100% LC at sight",
]


def ensure_payment_terms_templates():
	for name in DEFAULT_TEMPLATES:
		if frappe.db.exists("Payment Terms Template", name):
			continue
		try:
			tmpl = frappe.new_doc("Payment Terms Template")
			tmpl.template_name = name
			tmpl.append(
				"terms",
				{
					"description": name,
					"invoice_portion": 100,
					"due_date_based_on": "Day(s) after invoice date",
					"credit_days": 0,
				},
			)
			tmpl.flags.ignore_permissions = True
			tmpl.insert()
		except Exception:
			frappe.log_error(
				frappe.get_traceback(), "earthentrading.ensure_payment_terms_templates"
			)

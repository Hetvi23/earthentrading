# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Seed a few ET Payment Term records so the Sales Order 'Trade Payment' link
field has sensible options out of the box. Users can add more inline from the
Sales Order page. Idempotent; safe to re-run."""

import frappe

DEFAULT_TERMS = [
	"100% against scanned documents",
	"100% advance TT",
	"20% Advance, 80% against scanned documents",
	"100% LC at sight",
]


def ensure_payment_terms():
	for name in DEFAULT_TERMS:
		if frappe.db.exists("ET Payment Term", name):
			continue
		try:
			doc = frappe.new_doc("ET Payment Term")
			doc.term_name = name
			doc.flags.ignore_permissions = True
			doc.insert()
		except Exception:
			frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_payment_terms")

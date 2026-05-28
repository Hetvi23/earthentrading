# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Seed default ET Lead Function rows (Buyer / Seller / Buyer-Seller / Broker)."""

import frappe

DEFAULT_FUNCTIONS = ["Buyer", "Seller", "Buyer-Seller", "Broker"]


def ensure_lead_functions():
	if not frappe.db.exists("DocType", "ET Lead Function"):
		return
	for name in DEFAULT_FUNCTIONS:
		if frappe.db.exists("ET Lead Function", name):
			continue
		frappe.get_doc(
			{
				"doctype": "ET Lead Function",
				"function_name": name,
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()

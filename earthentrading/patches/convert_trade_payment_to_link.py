# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Convert Sales Order ``custom_et_trade_payment`` from Small Text to a
Link → Payment Terms Template.

Frappe refuses an in-place fieldtype change (Small Text → Link), so the old
Custom Field is deleted here (post_model_sync). The ``after_migrate`` hook then
re-creates it as a Link via create_custom_fields. The DB column is left in place
so any existing values are preserved and simply re-typed when the Link field is
re-added.
"""

import frappe


def execute():
	name = "Sales Order-custom_et_trade_payment"
	fieldtype = frappe.db.get_value("Custom Field", name, "fieldtype")
	if fieldtype and fieldtype != "Link":
		frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)

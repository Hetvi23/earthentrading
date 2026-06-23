# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Normalize the Sales Order operations/email Custom Field ordering.

Frappe sorts custom fields into the form by their stored ``idx`` (it processes
fields in idx order and places each after its ``insert_after`` target). Over
several migrations these idx values drifted out of sync with the intended
``insert_after`` chain — e.g. ``custom_et_port_of_loading`` had a lower idx than
``custom_et_origin``, so it was deferred to the very end of the form (below the
Email Recipients table). Re-stamp a clean, increasing idx in chain order so the
sort resolves correctly every time.
"""

import frappe

# Intended top-to-bottom order of the operations + email custom fields.
SALES_ORDER_FIELD_ORDER = [
	"custom_et_operations_section",
	"custom_et_brokerage_commission_value",
	"custom_et_co_brokerage_commission_value",
	"custom_et_insurance_value",
	"custom_et_trade_payment",
	"custom_et_origin",
	"custom_et_port_of_loading",
	"custom_et_operations_cb",
	"custom_et_packaging_design",
	"custom_et_crop",
	"custom_et_destination",
	"custom_et_port_of_destination",
	"custom_et_email_section",
	"custom_et_email_recipients",
]

# Base idx — kept above the Trading-details custom fields (idx ~54-57) so the
# operations block always sorts after them.
_BASE_IDX = 59


def ensure_sales_order_field_order():
	changed = False
	for offset, fieldname in enumerate(SALES_ORDER_FIELD_ORDER):
		name = f"Sales Order-{fieldname}"
		if not frappe.db.exists("Custom Field", name):
			continue
		new_idx = _BASE_IDX + offset
		if frappe.db.get_value("Custom Field", name, "idx") != new_idx:
			frappe.db.set_value("Custom Field", name, "idx", new_idx, update_modified=False)
			changed = True
	if changed:
		frappe.clear_cache(doctype="Sales Order")

# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Drop the legacy Sales Order ``custom_et_buyer`` Custom Field.

The trading model was reworked so the standard ``customer`` field is the buyer
and a new ``custom_et_supplier`` Link is the seller; the old ``custom_et_buyer``
(a second Customer link) is no longer used. ``create_custom_fields(update=True)``
does not remove dropped keys, so the Custom Field is deleted here. There is no
safe automatic remap of old buyer/seller data (the old seller was stored as a
Customer, not a Supplier), so existing values are dropped.
"""

import frappe


def execute():
	name = "Sales Order-custom_et_buyer"
	if frappe.db.exists("Custom Field", name):
		frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)

	# Custom Field on_trash does not run ALTER TABLE DROP COLUMN; remove the
	# orphaned column so it doesn't linger as dead data.
	try:
		if "custom_et_buyer" in frappe.db.get_table_columns("Sales Order"):
			frappe.db.sql_ddl("ALTER TABLE `tabSales Order` DROP COLUMN `custom_et_buyer`")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.remove_legacy_buyer_field")

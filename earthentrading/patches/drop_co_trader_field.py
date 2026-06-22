# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Drop the Sales Order ``custom_et_co_trader`` field.

The trader model was simplified to a single explicit trader: the order's creator
is the first trader and ``custom_et_assigned_trader`` is the other trader; both
share the commission via their User 'Commission %'. The separate Co-Trader field
is no longer used. create_custom_fields(update=True) does not remove dropped
keys, so the Custom Field is deleted here.
"""

import frappe


def execute():
	name = "Sales Order-custom_et_co_trader"
	if frappe.db.exists("Custom Field", name):
		frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)
	try:
		if "custom_et_co_trader" in frappe.db.get_table_columns("Sales Order"):
			frappe.db.sql_ddl("ALTER TABLE `tabSales Order` DROP COLUMN `custom_et_co_trader`")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.drop_co_trader_field")

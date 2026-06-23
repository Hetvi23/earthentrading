# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Drop the Sales Order ``custom_et_brokerage_commission_unit`` field.

Trade quantities (and therefore the brokerage commission) are always per Metric
Ton, so the unit selector is redundant — the commission line is now hardcoded to
"per Metric Ton". create_custom_fields(update=True) does not remove dropped keys,
so the Custom Field is deleted here.
"""

import frappe


def execute():
	name = "Sales Order-custom_et_brokerage_commission_unit"
	if frappe.db.exists("Custom Field", name):
		frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)
	try:
		if "custom_et_brokerage_commission_unit" in frappe.db.get_table_columns("Sales Order"):
			frappe.db.sql_ddl(
				"ALTER TABLE `tabSales Order` DROP COLUMN `custom_et_brokerage_commission_unit`"
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.drop_brokerage_commission_unit")

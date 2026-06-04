# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Drop the legacy Lead Commodities & quantities section + its child table.

Earlier iterations of the app added a "Commodities & quantities" section
(custom_et_commodities_section + custom_et_lines, linked to ET Lead Line) on
Lead. The section is no longer wanted — Trade Report (ET Lead Trade Report)
already captures the trading data per Lead.

Idempotent: silently skips fields/rows that don't exist.
"""

import frappe


FIELDS_TO_DROP = [
	"Lead-custom_et_commodities_section",
	"Lead-custom_et_lines",
]


def execute():
	for cf in FIELDS_TO_DROP:
		if not frappe.db.exists("Custom Field", cf):
			continue
		try:
			frappe.delete_doc(
				"Custom Field", cf, force=True, ignore_permissions=True
			)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"earthentrading.remove_lead_commodities_section.{cf}",
			)
	frappe.db.commit()
	frappe.clear_cache()

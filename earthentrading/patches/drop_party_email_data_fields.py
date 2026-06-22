# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Drop the short-lived Customer/Supplier ``custom_et_primary_email`` and
``custom_et_secondary_email`` Data fields.

They were replaced by the ``custom_et_emails`` table (ET Party Email), which
supports multiple addresses per party. These two fields were only just
introduced and hold no production data, so they are removed without a data
copy. ``create_custom_fields(update=True)`` does not delete dropped keys, so the
Custom Fields are deleted here.
"""

import frappe


def execute():
	for dt in ("Customer", "Supplier"):
		for fieldname in ("custom_et_primary_email", "custom_et_secondary_email"):
			name = f"{dt}-{fieldname}"
			if frappe.db.exists("Custom Field", name):
				frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)
			try:
				if fieldname in frappe.db.get_table_columns(dt):
					frappe.db.sql_ddl(f"ALTER TABLE `tab{dt}` DROP COLUMN `{fieldname}`")
			except Exception:
				frappe.log_error(
					frappe.get_traceback(), "earthentrading.drop_party_email_data_fields"
				)

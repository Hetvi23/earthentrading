# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""One-shot patch: switch Sales Order port custom fields Data → Link → ET Port.

Frappe blocks fieldtype changes on Custom Field via the standard
`create_custom_fields` path. We force-update the Custom Field rows directly
(the DB column stays VARCHAR, which works for a Link), then make sure every
already-stored port value has a matching ET Port record so the Link doesn't
appear invalid.
"""

import frappe


CF_NAMES = [
	"Sales Order-custom_et_port_of_loading",
	"Sales Order-custom_et_port_of_destination",
]


def execute():
	if not frappe.db.exists("DocType", "ET Port"):
		return

	# Fresh install: no Custom Fields yet, no data to migrate. create_custom_fields()
	# in after_migrate will set the port fields up directly as Link → ET Port.
	if not (
		frappe.db.exists("Custom Field", "Sales Order-custom_et_port_of_loading")
		or frappe.db.exists("Custom Field", "Sales Order-custom_et_port_of_destination")
	):
		return

	# 1. Make sure every port string already saved on Sales Orders exists as
	#    an ET Port record (so the new Link doesn't dangle).
	rows = frappe.db.sql(
		"""
		SELECT DISTINCT custom_et_port_of_loading AS port FROM `tabSales Order`
		WHERE custom_et_port_of_loading IS NOT NULL AND custom_et_port_of_loading <> ''
		UNION
		SELECT DISTINCT custom_et_port_of_destination AS port FROM `tabSales Order`
		WHERE custom_et_port_of_destination IS NOT NULL AND custom_et_port_of_destination <> ''
		""",
		as_dict=True,
	)
	for r in rows:
		name = r["port"]
		if name and not frappe.db.exists("ET Port", name):
			frappe.get_doc({"doctype": "ET Port", "port_name": name}).insert(ignore_permissions=True)

	# 2. Flip the fieldtype on the existing Custom Field rows in-place.
	for cf in CF_NAMES:
		if not frappe.db.exists("Custom Field", cf):
			continue
		frappe.db.set_value(
			"Custom Field",
			cf,
			{
				"fieldtype": "Link",
				"options": "ET Port",
			},
			update_modified=False,
		)

	frappe.db.commit()
	frappe.clear_cache()

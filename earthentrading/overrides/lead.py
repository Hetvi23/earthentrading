# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Override ERPNext Lead → Opportunity mapper so Lines appear before first save."""

import frappe

from earthentrading.events.opportunity import _items_nonempty, _opp_item_from_lead_line


@frappe.whitelist()
def make_opportunity(source_name, target_doc=None):
	from erpnext.crm.doctype.lead.lead import make_opportunity as erpnext_make_opportunity

	doc = erpnext_make_opportunity(source_name, target_doc)
	if frappe.db.exists("Lead", source_name):
		lead = frappe.get_doc("Lead", source_name)
	else:
		lead = None

	if lead and getattr(doc, "doctype", None) == "Opportunity" and doc.get("opportunity_from") == "Lead":
		if not _items_nonempty(doc):
			for row in getattr(lead, "custom_et_lines", None) or []:
				doc.append("items", _opp_item_from_lead_line(row))
		try:
			doc.calculate_totals()
		except Exception:
			pass

	return doc

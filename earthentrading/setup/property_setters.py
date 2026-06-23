# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Property Setters for Lead and Sales Order — hides legacy fields and
reorders the list view to match the Earth Trading operations layout."""

import frappe
from frappe.custom.doctype.property_setter.property_setter import (
	make_property_setter,
)


# (doctype, fieldname, property, value, property_type)
PROPERTY_SETTERS = [
	# --- Lead status: trim to the three statuses we actually use ---
	("Lead", "status", "options", "Open\nLead\nConverted", "Text"),
	# --- Lead: hide standard fields that aren't useful for B2B trading ---
	("Lead", "salutation", "hidden", "1", "Check"),
	("Lead", "middle_name", "hidden", "1", "Check"),
	("Lead", "gender", "hidden", "1", "Check"),
	("Lead", "no_of_employees", "hidden", "1", "Check"),
	("Lead", "annual_revenue", "hidden", "1", "Check"),
	("Lead", "market_segment", "hidden", "1", "Check"),
	# Keep qualification visible — user wants a Qualification section in the form.
	("Lead", "qualification", "hidden", "0", "Check"),
	("Lead", "blog_subscriber", "hidden", "1", "Check"),
	("Lead", "fax", "hidden", "1", "Check"),
	("Lead", "type", "hidden", "1", "Check"),
	("Lead", "request_type", "hidden", "1", "Check"),
	("Lead", "campaign_name", "hidden", "1", "Check"),
	# Push organization to the front: list view shows Organization Name, Status,
	# Lead Function, Commodity Group, Country, External Broker.
	("Lead", "company_name", "in_list_view", "1", "Check"),
	("Lead", "company_name", "in_standard_filter", "1", "Check"),
	("Lead", "status", "in_list_view", "1", "Check"),
	("Lead", "industry", "in_standard_filter", "1", "Check"),
	("Lead", "website", "in_standard_filter", "1", "Check"),
	("Lead", "country", "in_list_view", "1", "Check"),
	("Lead", "country", "in_standard_filter", "1", "Check"),
	("Lead", "territory", "in_standard_filter", "1", "Check"),
	# Title -> Organization Name (used on the list & breadcrumb)
	("Lead", None, "title_field", "company_name", "Data"),
	("Lead", None, "search_fields", "company_name,lead_name,status,custom_et_lead_function,custom_et_commodity_group", "Small Text"),
	# --- Sales Order: surface operations-relevant fields in list view ---
	("Sales Order", "customer_name", "in_list_view", "1", "Check"),
	("Sales Order", "status", "in_list_view", "1", "Check"),
	("Sales Order", "transaction_date", "in_list_view", "1", "Check"),
	("Sales Order", "delivery_date", "in_list_view", "1", "Check"),
	("Sales Order", "order_type", "in_standard_filter", "1", "Check"),
	("Sales Order", "company", "in_standard_filter", "1", "Check"),
	("Sales Order", "total_qty", "in_list_view", "1", "Check"),
	# Order Type is restricted to Sales Contract / Trade Contract.
	("Sales Order", "order_type", "options", "Sales Contract\nTrade Contract", "Text"),
	# The standard field default is "Sales", which is no longer a valid option;
	# point it at a valid one so meta validation (e.g. country-fixture install)
	# doesn't choke on an out-of-list default.
	("Sales Order", "order_type", "default", "Sales Contract", "Text"),
	# Delivery Date is no longer mandatory (trade contracts often have no
	# defined delivery date until shipping is confirmed).
	("Sales Order", "delivery_date", "reqd", "0", "Check"),
	# Same for the items table's per-row delivery_date.
	("Sales Order Item", "delivery_date", "reqd", "0", "Check"),
	# Trade quantities are in Metric Ton — default the item UOM accordingly.
	("Sales Order Item", "uom", "default", "Metric Ton", "Data"),
	("Sales Order Item", "stock_uom", "default", "Metric Ton", "Data"),
	# Keep the Items grid to: Item Code, Shipping Start/End, Qty, Rate, Amount —
	# hide delivery_date and warehouse columns (still editable in the row).
	("Sales Order Item", "delivery_date", "in_list_view", "0", "Check"),
	("Sales Order Item", "warehouse", "in_list_view", "0", "Check"),
	# po_no becomes a Link picker into existing Trade Contract Sales Orders.
	# Only shown on Sales Contract orders (a Trade Contract IS the source,
	# so it doesn't need to pick another SO). The dropdown filter is set
	# client-side in sales_order_assign_prompt.js via frm.set_query.
	("Sales Order", "po_no", "fieldtype", "Link", "Data"),
	("Sales Order", "po_no", "options", "Sales Order", "Small Text"),
	("Sales Order", "po_no", "depends_on", "eval:doc.order_type=='Sales Contract'", "Data"),
	("Sales Order", "po_date", "depends_on", "eval:doc.order_type=='Sales Contract'", "Data"),
	# --- Lead: hide standard tab breaks so all sections render under Details ---
	# Six sections in order: (1) Person / Status, (2) Contact Info,
	# (3) Address & Contact, (4) Organization, (5) Trading details + Trade
	# Report, (6) Qualification. We flip the tab breaks to plain section
	# breaks so the content flows as one continuous Details tab.
	("Lead", "contact_info", "fieldtype", "Section Break", "Data"),
	("Lead", "more_info", "fieldtype", "Section Break", "Data"),
	("Lead", "connections_tab", "hidden", "1", "Check"),
	# Friendly section labels matching the requested ordering.
	("Lead", "contact_info", "label", "Contact info", "Data"),
	("Lead", "more_info", "label", "Qualification", "Data"),
]


def ensure_property_setters():
	# The default UOM property setters point at "Metric Ton"; make sure it exists.
	if not frappe.db.exists("UOM", "Metric Ton"):
		try:
			frappe.get_doc({"doctype": "UOM", "uom_name": "Metric Ton"}).insert(
				ignore_permissions=True
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_metric_ton_uom")

	for doctype, fieldname, prop, value, prop_type in PROPERTY_SETTERS:
		try:
			make_property_setter(
				doctype,
				fieldname,
				prop,
				value,
				prop_type,
				for_doctype=(fieldname is None),
				validate_fields_for_doctype=False,
			)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"earthentrading.property_setters: {doctype}.{fieldname}.{prop}",
			)

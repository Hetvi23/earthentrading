# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Force the Lead form into the 6-section sequence:
  1. Person details (as-is)
  2. Contact info
  3. Address and Contact
  4. Organization
  5. Trading details + Trade Report (our custom sections)
  6. Qualification

Uses a Property Setter on Lead.field_order — overrides the standard
ERPNext order so contact info / address / organization render in the
sequence we want, then drops our Trading sections in before
Qualification.
"""

import json

import frappe
from frappe.custom.doctype.property_setter.property_setter import (
	make_property_setter,
)


LEAD_FIELD_ORDER = [
	# --- 1. Person details (as it currently is) -----------------------
	"naming_series",
	"salutation",
	"first_name",
	"middle_name",
	"last_name",
	"column_break_1",
	"lead_name",
	"job_title",
	"gender",
	"source",
	"col_break123",
	"lead_owner",
	"status",
	"customer",
	"type",
	"request_type",
	# --- 2. Contact info ---------------------------------------------
	"contact_info_tab",
	"email_id",
	"website",
	"column_break_20",
	"mobile_no",
	"whatsapp_no",
	"column_break_16",
	"phone",
	"phone_ext",
	# --- 3. Address and Contact --------------------------------------
	"address_section",
	"address_html",
	"column_break_38",
	"city",
	"state",
	"country",
	"column_break2",
	"contact_html",
	# --- 4. Organization ---------------------------------------------
	"organization_section",
	"company_name",
	"no_of_employees",
	"column_break_28",
	"annual_revenue",
	"industry",
	"market_segment",
	"column_break_31",
	"territory",
	"fax",
	# --- 5. Trading details + Trade Report (custom) ------------------
	"custom_et_trading_section",
	"custom_et_sales_stage",
	"custom_et_lead_function",
	"custom_et_commodity_group",
	"custom_et_assigned_trader",
	"custom_et_brokers_cb",
	"custom_et_internal_broker",
	"custom_et_external_broker",
	"custom_et_region",
	"custom_et_deal_type",
	"custom_et_incoterm",
	"custom_et_trade_report_section",
	"custom_et_trade_report",
	# --- 6. Qualification --------------------------------------------
	"qualification_tab",
	"qualification_status",
	"column_break_64",
	"qualified_by",
	"qualified_on",
	# --- Trailing sections kept for parity with standard Lead --------
	# These remain in the doc but won't render visually for the user
	# because their tab breaks are hidden / converted by property setters.
	"other_info_tab",
	"campaign_name",
	"company",
	"column_break_22",
	"language",
	"image",
	"title",
	"column_break_50",
	"disabled",
	"unsubscribed",
	"blog_subscriber",
	"activities_tab",
	"open_activities_html",
	"all_activities_section",
	"all_activities_html",
	"notes_tab",
	"notes_html",
	"notes",
	"dashboard_tab",
]


def apply_lead_layout():
	"""Compute the final ordered field list (intersected with what actually
	exists on this site's Lead meta) and write it as a Property Setter.

	Defensively wipe any pre-existing field_order Property Setter first —
	an earlier release of this module stored the value newline-separated
	instead of JSON, which makes frappe.get_meta("Lead") throw
	JSONDecodeError. Self-heal by clearing it before we try to load meta.
	"""
	frappe.db.sql(
		"DELETE FROM `tabProperty Setter` WHERE doc_type='Lead' AND property='field_order'"
	)
	frappe.db.commit()
	frappe.clear_cache(doctype="Lead")

	meta = frappe.get_meta("Lead")
	existing = {df.fieldname for df in meta.fields}

	ordered = [f for f in LEAD_FIELD_ORDER if f in existing]
	# Tack on anything we don't explicitly know about (other apps' custom fields).
	for f in [df.fieldname for df in meta.fields]:
		if f not in ordered:
			ordered.append(f)

	# Frappe's Meta.sort_fields does json.loads(field_order) — so the value
	# must be a JSON-encoded list, not newline-separated. The previous
	# release stored newlines and broke every Lead form load with
	# JSONDecodeError.
	make_property_setter(
		"Lead",
		"",
		"field_order",
		json.dumps(ordered),
		"Small Text",
		for_doctype=True,
		validate_fields_for_doctype=False,
	)
	frappe.clear_cache(doctype="Lead")

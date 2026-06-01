# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Leads filtered by their Trade Report (child table) rows.

Joins Lead ↔ ET Lead Trade Report and shows only leads with matching trade
report rows. One row in the report = one matching Trade Report entry, so a
single lead may show twice if it has two trade rows that both match.
"""

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = _columns()
	rows = _rows(filters)
	return columns, rows


def _columns():
	return [
		{
			"label": "Lead",
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Lead",
			"width": 160,
		},
		{
			"label": "Organization",
			"fieldname": "company_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": "Status",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"label": "Function",
			"fieldname": "lead_function",
			"fieldtype": "Link",
			"options": "ET Lead Function",
			"width": 110,
		},
		{
			"label": "Commodity Group",
			"fieldname": "commodity_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 130,
		},
		{
			"label": "Lead Country",
			"fieldname": "country",
			"fieldtype": "Link",
			"options": "Country",
			"width": 120,
		},
		{
			"label": "External Broker",
			"fieldname": "external_broker",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 160,
		},
		{
			"label": "Trade Commodity",
			"fieldname": "tr_commodity",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": "Origin",
			"fieldname": "tr_origin",
			"fieldtype": "Link",
			"options": "Country",
			"width": 110,
		},
		{
			"label": "Destination",
			"fieldname": "tr_destination",
			"fieldtype": "Link",
			"options": "Country",
			"width": 110,
		},
		{
			"label": "Role",
			"fieldname": "tr_role",
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"label": "Transaction",
			"fieldname": "tr_transaction_id",
			"fieldtype": "Data",
			"width": 110,
		},
	]


def _rows(filters):
	conditions = ["tr.parenttype = 'Lead'"]
	values = {}

	commodity = (filters.get("commodity") or "").strip()
	if commodity:
		conditions.append("tr.commodity LIKE %(commodity)s")
		values["commodity"] = f"%{commodity}%"

	if filters.get("origin"):
		conditions.append("tr.origin = %(origin)s")
		values["origin"] = filters["origin"]

	if filters.get("destination"):
		conditions.append("tr.destination = %(destination)s")
		values["destination"] = filters["destination"]

	if filters.get("role"):
		conditions.append("tr.role = %(role)s")
		values["role"] = filters["role"]

	if filters.get("status"):
		conditions.append("l.status = %(status)s")
		values["status"] = filters["status"]

	if filters.get("lead_function"):
		conditions.append("l.custom_et_lead_function = %(lead_function)s")
		values["lead_function"] = filters["lead_function"]

	if filters.get("commodity_group"):
		conditions.append("l.custom_et_commodity_group = %(commodity_group)s")
		values["commodity_group"] = filters["commodity_group"]

	where = " AND ".join(conditions)

	return frappe.db.sql(
		f"""
		SELECT
			l.name AS name,
			l.company_name AS company_name,
			l.status AS status,
			l.custom_et_lead_function AS lead_function,
			l.custom_et_commodity_group AS commodity_group,
			l.country AS country,
			l.custom_et_external_broker AS external_broker,
			tr.commodity AS tr_commodity,
			tr.origin AS tr_origin,
			tr.destination AS tr_destination,
			tr.role AS tr_role,
			tr.transaction_id AS tr_transaction_id
		FROM `tabET Lead Trade Report` tr
		INNER JOIN `tabLead` l ON l.name = tr.parent
		WHERE {where}
		ORDER BY l.company_name, tr.idx
		""",
		values,
		as_dict=True,
	)

# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Whitelisted endpoint used by the inline workspace filter widget."""

import frappe


@frappe.whitelist()
def search(
	commodity: str | None = None,
	origin: str | None = None,
	destination: str | None = None,
	role: str | None = None,
	lead_function: str | None = None,
	commodity_group: str | None = None,
	status: str | None = None,
):
	"""Return Trade Report rows (joined with Lead) matching the filter set.

	All filters AND together. Results are capped to 500 rows so a stray empty
	filter set doesn't ship the entire table to the browser.
	"""
	conditions = ["tr.parenttype = 'Lead'"]
	values: dict = {}

	commodity = (commodity or "").strip()
	if commodity:
		conditions.append("tr.commodity LIKE %(commodity)s")
		values["commodity"] = f"%{commodity}%"

	if origin:
		conditions.append("tr.origin = %(origin)s")
		values["origin"] = origin

	if destination:
		conditions.append("tr.destination = %(destination)s")
		values["destination"] = destination

	if role:
		conditions.append("tr.role = %(role)s")
		values["role"] = role

	if lead_function:
		conditions.append("l.custom_et_lead_function = %(lead_function)s")
		values["lead_function"] = lead_function

	if commodity_group:
		conditions.append("l.custom_et_commodity_group = %(commodity_group)s")
		values["commodity_group"] = commodity_group

	if status:
		conditions.append("l.status = %(status)s")
		values["status"] = status

	where = " AND ".join(conditions)

	rows = frappe.db.sql(
		f"""
		SELECT
			l.name,
			l.company_name,
			l.status,
			l.custom_et_lead_function AS lead_function,
			l.custom_et_commodity_group AS commodity_group,
			tr.commodity,
			tr.origin,
			tr.destination,
			tr.role,
			tr.transaction_id
		FROM `tabET Lead Trade Report` tr
		INNER JOIN `tabLead` l ON l.name = tr.parent
		WHERE {where}
		ORDER BY l.company_name, tr.idx
		LIMIT 500
		""",
		values,
		as_dict=True,
	)
	return rows

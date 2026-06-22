# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Endpoint backing the Selling workspace inline list widget. Returns Sales
Orders scoped to the current user by default, or unfiltered when `mine=0`.
"""

import frappe


@frappe.whitelist()
def search(mine: int = 1, status: str | None = None, limit: int = 200):
	"""Return Sales Orders for the inline widget.

	Args:
		mine: 1 (default) restricts to SOs owned by frappe.session.user.
		      0 returns all SOs the user has read permission for.
		status: optional Sales Order `status` filter (Draft/Submitted/Cancelled
		        or any of the workflow_state values).
		limit: max rows (capped at 500).
	"""
	mine = int(mine or 0)
	limit = min(int(limit or 200), 500)

	conditions = []
	values: dict = {}

	if mine:
		conditions.append("so.owner = %(me)s")
		values["me"] = frappe.session.user

	if status:
		conditions.append("so.status = %(status)s")
		values["status"] = status

	where = " AND ".join(conditions) if conditions else "1=1"

	rows = frappe.db.sql(
		f"""
		SELECT
			so.name,
			so.customer,
			so.customer_name,
			so.custom_et_supplier AS supplier,
			so.custom_et_contract_type AS contract_type,
			so.custom_et_assigned_trader AS assigned_trader,
			so.workflow_state,
			so.status,
			so.transaction_date,
			so.delivery_date,
			so.total,
			so.currency,
			so.docstatus,
			so.owner
		FROM `tabSales Order` so
		WHERE {where}
		ORDER BY so.transaction_date DESC, so.creation DESC
		LIMIT {limit}
		""",
		values,
		as_dict=True,
	)
	return rows

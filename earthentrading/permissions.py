# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe


def _roles(user: str) -> set[str]:
	return set(frappe.get_roles(user))


def _is_et_trader(user: str) -> bool:
	return "ET Trader" in _roles(user) and "ET Director" not in _roles(user) and "System Manager" not in _roles(
		user
	)


def lead_query_conditions(user: str | None) -> str | None:
	if not user or user == "Administrator":
		return None
	if not _is_et_trader(user):
		return None
	u = frappe.db.escape(user)
	return f"(`tabLead`.`lead_owner` = {u})"


def opportunity_query_conditions(user: str | None) -> str | None:
	if not user or user == "Administrator":
		return None
	if not _is_et_trader(user):
		return None
	u = frappe.db.escape(user)
	return f"(`tabOpportunity`.`opportunity_owner` = {u})"


def quotation_query_conditions(user: str | None) -> str | None:
	if not user or user == "Administrator":
		return None
	if not _is_et_trader(user):
		return None
	u = frappe.db.escape(user)
	return (
		f"(`tabQuotation`.`custom_et_assigned_trader` = {u} OR `tabQuotation`.`owner` = {u})"
	)


def sales_order_query_conditions(user: str | None) -> str | None:
	if not user or user == "Administrator":
		return None
	if not _is_et_trader(user):
		return None
	u = frappe.db.escape(user)
	# A trader sees their own deals (assigned to them or created by them) plus
	# the shared "Trader Review" queue — any SO currently awaiting a trader's
	# approval, so it can be picked up regardless of who it's assigned to.
	return (
		f"(`tabSales Order`.`custom_et_assigned_trader` = {u} "
		f"OR `tabSales Order`.`owner` = {u} "
		f"OR `tabSales Order`.`workflow_state` = 'Trader Review')"
	)

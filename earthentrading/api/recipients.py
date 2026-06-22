# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Shared builder for the Sales Order email-recipients table.

Both the client (on Customer / Supplier change) and the server
(earthentrading.events.sales_order.validate) call build_recipient_candidates
so the two stay in agreement. Each party — Customer = buyer, Supplier = seller —
contributes its primary email (To), secondary email (CC), and every internal
"dealing user" (CC).
"""

import frappe


def _party_candidates(party_type: str, party: str | None, side: str) -> list[dict]:
	"""Candidate recipient rows for one Customer/Supplier."""
	rows: list[dict] = []
	if not party:
		return rows

	name_field = "customer_name" if party_type == "Customer" else "supplier_name"
	display_name = frappe.db.get_value(party_type, party, name_field) or party

	# Party emails (multiple): Primary-ticked -> To, the rest -> CC.
	emails = frappe.get_all(
		"ET Party Email",
		filters={"parent": party, "parenttype": party_type, "parentfield": "custom_et_emails"},
		fields=["email", "is_primary"],
		order_by="idx asc",
	)
	for em in emails:
		addr = (em.get("email") or "").strip()
		if not addr:
			continue
		if em.get("is_primary"):
			rows.append(
				{
					"party_side": side,
					"source": "Primary Email",
					"recipient_name": display_name,
					"email": addr,
					"is_primary": 1,
					"is_cc": 0,
				}
			)
		else:
			rows.append(
				{
					"party_side": side,
					"source": "Additional Email",
					"recipient_name": display_name,
					"email": addr,
					"is_primary": 0,
					"is_cc": 1,
				}
			)

	# Connected internal users → CC.
	users = frappe.get_all(
		"ET Party User",
		filters={"parent": party, "parenttype": party_type, "parentfield": "custom_et_dealing_users"},
		fields=["user", "full_name", "email"],
		order_by="idx asc",
	)
	for u in users:
		email = (u.get("email") or "").strip()
		if not email and u.get("user"):
			email = (frappe.db.get_value("User", u.get("user"), "email") or "").strip()
		if not email:
			continue
		rows.append(
			{
				"party_side": side,
				"source": "Connected User",
				"recipient_name": u.get("full_name") or u.get("user"),
				"email": email,
				"is_primary": 0,
				"is_cc": 1,
			}
		)

	return rows


def build_recipient_candidates(customer: str | None, supplier: str | None) -> list[dict]:
	"""Candidate rows for a Sales Order's Customer (buyer) + Supplier (seller)."""
	rows: list[dict] = []
	rows.extend(_party_candidates("Customer", customer, "Customer"))
	rows.extend(_party_candidates("Supplier", supplier, "Supplier"))
	return rows


@frappe.whitelist()
def get_recipient_candidates(customer: str | None = None, supplier: str | None = None) -> dict:
	"""Whitelisted wrapper for the Sales Order form.

	Returns the candidate rows plus per-side connected-user counts so the client
	can prompt the user to review the CC list when several people deal with a
	party.
	"""
	rows = build_recipient_candidates(customer, supplier)
	user_counts = {
		"Customer": sum(
			1 for r in rows if r["party_side"] == "Customer" and r["source"] == "Connected User"
		),
		"Supplier": sum(
			1 for r in rows if r["party_side"] == "Supplier" and r["source"] == "Connected User"
		),
	}
	return {"rows": rows, "user_counts": user_counts}

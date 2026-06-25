# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""One-time (idempotent) rename of legacy workflow_state values on existing
Sales Orders and Quotations after the "ET SO " / "ET Quote " prefixes were
dropped from the workflow state names.

Runs from install.after_migrate (right after ensure_workflows). The LIKE/exact
filters make it a no-op once every row already carries a new-style state, so it
is safe to run on every migrate.
"""

import frappe

# Old workflow_state value -> new value.
SALES_ORDER_STATE_MAP = {
	"ET SO Draft": "Draft",
	"ET SO Trader Review": "Trader Review",
	"ET SO Final Review": "Final Review",
	"ET SO Pending Assignment": "Pending Assignment",
	"ET SO In Progress": "Person Assigned",
	"ET SO Raise Invoice": "Tasks Completed",
	# Renamed states: "In Progress" -> "Person Assigned",
	# "Raise Invoice" -> "Tasks Completed".
	"In Progress": "Person Assigned",
	"Raise Invoice": "Tasks Completed",
	"ET SO Completed": "Completed",
	"ET SO Claim": "Claim",
	"ET SO Rejected": "Rejected",
	# Legacy sample-data label that was never an actual workflow state; land it
	# in the nearest real post-approval state.
	"ET SO Approved": "Pending Assignment",
}

QUOTATION_STATE_MAP = {
	"ET Quote Draft": "Quote Draft",
	"ET Quote Pending": "Quote Pending",
	"ET Quote Approved": "Quote Approved",
	"ET Quote Rejected": "Quote Rejected",
}


def _apply(doctype: str, mapping: dict) -> int:
	updated = 0
	for old, new in mapping.items():
		rows = frappe.db.sql(
			f"update `tab{doctype}` set workflow_state = %s where workflow_state = %s",
			(new, old),
		)
		# rowcount is exposed via frappe.db._cursor after execute.
		count = getattr(frappe.db._cursor, "rowcount", 0) or 0
		if count:
			updated += count
	return updated


def rename_legacy_workflow_states() -> None:
	total = 0
	total += _apply("Sales Order", SALES_ORDER_STATE_MAP)
	total += _apply("Quotation", QUOTATION_STATE_MAP)
	if total:
		frappe.db.commit()
		frappe.logger("earthentrading").info(
			f"Renamed legacy workflow_state on {total} documents."
		)

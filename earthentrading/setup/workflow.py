# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Approval workflows for Quotation and Sales Order (Earth Trading)."""

import frappe


def _ensure_workflow_state(name: str, style: str | None = None):
	if frappe.db.exists("Workflow State", name):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Workflow State",
			"workflow_state_name": name,
		}
	)
	if style:
		doc.style = style
	doc.insert(ignore_permissions=True)


def _ensure_workflow_action(name: str):
	if frappe.db.exists("Workflow Action Master", name):
		return
	frappe.get_doc(
		{"doctype": "Workflow Action Master", "workflow_action_name": name}
	).insert(ignore_permissions=True)


def _active_workflow_for(doctype: str) -> str | None:
	row = frappe.db.sql(
		"""
		select name from `tabWorkflow`
		where document_type = %s and is_active = 1
		limit 1
		""",
		doctype,
		as_dict=True,
	)
	return row[0].name if row else None


def _deactivate_other_workflows(document_type: str, keep_name: str):
	frappe.db.sql(
		"""
		update `tabWorkflow` set is_active = 0
		where document_type = %s and name != %s
		""",
		(document_type, keep_name),
	)


def ensure_workflow_prerequisites():
	for state, style in (
		("Quote Draft", "Warning"),
		("Quote Pending", "Primary"),
		("Quote Approved", "Success"),
		("Quote Rejected", "Danger"),
		# Sales Order — extended lifecycle.
		("Draft", "Warning"),
		("Trader Review", "Primary"),
		("Trader Manager Review", "Primary"),
		("Final Review", "Primary"),
		("Pending Assignment", "Inverse"),
		("Person Assigned", "Primary"),
		("Tasks Completed", "Warning"),
		("Completed", "Success"),
		("Claim", "Danger"),
		("Rejected", "Danger"),
	):
		_ensure_workflow_state(state, style)

	for action in (
		"Send for Approval",
		"Send to Trader",
		"Send to Final",
		"Approve",
		"Reject",
		"Assign Team Member",
		"All Tasks Done",
		"Mark Completed",
		"Raise Claim",
		"Resolve Claim",
		"Resubmit",
	):
		_ensure_workflow_action(action)


def ensure_quotation_workflow():
	"""Single active workflow for Quotation; skips if another workflow is already active."""
	document_type = "Quotation"
	existing = _active_workflow_for(document_type)
	if existing:
		existing_title = frappe.db.get_value("Workflow", existing, "workflow_name")
		if existing_title != "Earth Trading Quotation":
			frappe.log_error(
				title="Earth Trading",
				message=f"Quotation already has active workflow {existing} ({existing_title}); skipping Earth Trading Quotation workflow.",
			)
			return

	# Role used for document edits in each state (must exist on site)
	edit_role = "Sales User" if frappe.db.exists("Role", "Sales User") else "System Manager"
	approver_roles = [r for r in ("Sales Manager", "ET Director") if frappe.db.exists("Role", r)] or ["System Manager"]

	name = "Earth Trading Quotation"
	if frappe.db.exists("Workflow", name):
		wf = frappe.get_doc("Workflow", name)
	else:
		wf = frappe.new_doc("Workflow")
		wf.workflow_name = name

	wf.document_type = document_type
	wf.is_active = 1
	wf.workflow_state_field = "workflow_state"
	wf.send_email_alert = 0

	wf.states = []
	wf.append(
		"states",
		{
			"state": "Quote Draft",
			"doc_status": "0",
			"allow_edit": edit_role,
		},
	)
	wf.append(
		"states",
		{
			"state": "Quote Pending",
			"doc_status": "0",
			"allow_edit": edit_role,
		},
	)
	wf.append(
		"states",
		{
			"state": "Quote Approved",
			"doc_status": "0",
			"allow_edit": edit_role,
		},
	)
	wf.append(
		"states",
		{
			"state": "Quote Rejected",
			"doc_status": "0",
			"allow_edit": edit_role,
		},
	)

	wf.transitions = []
	wf.append(
		"transitions",
		{
			"state": "Quote Draft",
			"action": "Send for Approval",
			"next_state": "Quote Pending",
			"allowed": edit_role,
		},
	)
	for role in approver_roles:
		wf.append(
			"transitions",
			{
				"state": "Quote Pending",
				"action": "Approve",
				"next_state": "Quote Approved",
				"allowed": role,
			},
		)
		wf.append(
			"transitions",
			{
				"state": "Quote Pending",
				"action": "Reject",
				"next_state": "Quote Rejected",
				"allowed": role,
			},
		)
	wf.append(
		"transitions",
		{
			"state": "Quote Rejected",
			"action": "Send for Approval",
			"next_state": "Quote Pending",
			"allowed": edit_role,
		},
	)

	wf.save(ignore_permissions=True)
	_deactivate_other_workflows(document_type, wf.name)
	wf.db_set("is_active", 1)
	frappe.db.commit()


def ensure_sales_order_workflow():
	"""Full SO lifecycle:
	- Approval: Draft -> [Trader Review if assigned] -> Final Review -> Rejected (loop) | Pending Assignment (auto-submits, doc_status=1)
	- Operations: Pending Assignment -> Person Assigned (operations assigns team member + creates project)
	- Tasks: Person Assigned -> Tasks Completed (auto when all tasks complete)
	- Billing: Tasks Completed -> Completed (auto when all linked Sales Invoices are paid)
	- Post-completion: Completed -> Claim -> Completed (resolve simply closes it again)
	"""
	document_type = "Sales Order"
	existing = _active_workflow_for(document_type)
	if existing:
		existing_title = frappe.db.get_value("Workflow", existing, "workflow_name")
		if existing_title != "Earth Trading Sales Order":
			frappe.log_error(
				title="Earth Trading",
				message=f"Sales Order already has active workflow {existing} ({existing_title}); skipping Earth Trading Sales Order workflow.",
			)
			return

	edit_role = "Sales User" if frappe.db.exists("Role", "Sales User") else "System Manager"
	# Two-step trader approval: the deal's own traders (the order's creator and
	# the Assigned Trader) approve first (Trader Review), then the Trader Manager
	# (Trader Manager Review, where the buyer/seller email fires).
	trader_role = "ET Trader" if frappe.db.exists("Role", "ET Trader") else "Sales Manager"
	trader_mgr_role = "ET Trader Manager" if frappe.db.exists("Role", "ET Trader Manager") else "Sales Manager"
	final_role = "ET Operations" if frappe.db.exists("Role", "ET Operations") else "Sales Manager"
	accounts_role = "Accounts User" if frappe.db.exists("Role", "Accounts User") else "System Manager"
	# Restrict the first approval to the deal's traders (creator or Assigned Trader).
	trader_match = "frappe.session.user in (doc.custom_et_assigned_trader, doc.owner)"

	name = "Earth Trading Sales Order"
	if frappe.db.exists("Workflow", name):
		wf = frappe.get_doc("Workflow", name)
	else:
		wf = frappe.new_doc("Workflow")
		wf.workflow_name = name

	wf.document_type = document_type
	wf.is_active = 1
	wf.workflow_state_field = "workflow_state"
	wf.send_email_alert = 0

	# ---- States ---------------------------------------------------------
	wf.states = []
	# Approval flow — doc_status=0 (draft, editable).
	for st in ("Draft", "Trader Review", "Trader Manager Review", "Final Review", "Rejected"):
		wf.append("states", {"state": st, "doc_status": "0", "allow_edit": edit_role})
	# Pending Assignment — submitted (doc_status=1). Operations sees the SO here.
	wf.append(
		"states",
		{"state": "Pending Assignment", "doc_status": "1", "allow_edit": final_role},
	)
	# Person Assigned — operations has assigned a handler and project is running.
	wf.append(
		"states",
		{"state": "Person Assigned", "doc_status": "1", "allow_edit": final_role},
	)
	# Tasks Completed — all project tasks done; accounts can now invoice.
	wf.append(
		"states",
		{"state": "Tasks Completed", "doc_status": "1", "allow_edit": accounts_role},
	)
	# Completed — invoices paid. Read-only for most; ops can raise a claim.
	wf.append(
		"states",
		{"state": "Completed", "doc_status": "1", "allow_edit": final_role},
	)
	# Claim — issue raised after completion. Only action is Resolve (→ Completed).
	wf.append(
		"states",
		{"state": "Claim", "doc_status": "1", "allow_edit": final_role},
	)

	# ---- Transitions ----------------------------------------------------
	wf.transitions = []

	# --- Approval phase ---
	wf.append(
		"transitions",
		{
			"state": "Draft",
			"action": "Send to Trader",
			"next_state": "Trader Review",
			"allowed": edit_role,
			"condition": "doc.custom_et_assigned_trader",
		},
	)
	wf.append(
		"transitions",
		{
			"state": "Draft",
			"action": "Send for Approval",
			"next_state": "Trader Manager Review",
			"allowed": edit_role,
			"condition": "not doc.custom_et_assigned_trader",
		},
	)
	# Step 1: the deal's own trader (Assigned Trader / Co-Trader) approves.
	wf.append(
		"transitions",
		{
			"state": "Trader Review",
			"action": "Approve",
			"next_state": "Trader Manager Review",
			"allowed": trader_role,
			"condition": trader_match,
		},
	)
	wf.append(
		"transitions",
		{
			"state": "Trader Review",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": trader_role,
			"condition": trader_match,
		},
	)
	# Step 2: the Trader Manager approves (this is where the buyer/seller
	# trade-confirmation email fires, on entering Final Review).
	wf.append(
		"transitions",
		{
			"state": "Trader Manager Review",
			"action": "Approve",
			"next_state": "Final Review",
			"allowed": trader_mgr_role,
		},
	)
	wf.append(
		"transitions",
		{
			"state": "Trader Manager Review",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": trader_mgr_role,
		},
	)
	wf.append(
		"transitions",
		{
			"state": "Final Review",
			"action": "Approve",
			"next_state": "Pending Assignment",
			"allowed": final_role,
		},
	)
	wf.append(
		"transitions",
		{
			"state": "Final Review",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": final_role,
		},
	)
	wf.append(
		"transitions",
		{
			"state": "Rejected",
			"action": "Resubmit",
			"next_state": "Draft",
			"allowed": edit_role,
		},
	)

	# --- Operations phase ---
	# Pending Assignment -> Person Assigned is fired by api.operations.assign_team_member
	# (JS "Assign Team Member" button on the SO form). Still listed here so the
	# workflow board shows the transition path.
	wf.append(
		"transitions",
		{
			"state": "Pending Assignment",
			"action": "Assign Team Member",
			"next_state": "Person Assigned",
			"allowed": final_role,
		},
	)
	# Person Assigned -> Tasks Completed fires from events.task.on_update when every
	# task in the linked project is Completed. Listed here for the board.
	wf.append(
		"transitions",
		{
			"state": "Person Assigned",
			"action": "All Tasks Done",
			"next_state": "Tasks Completed",
			"allowed": final_role,
		},
	)

	# --- Billing phase ---
	# Tasks Completed -> Completed fires from events.sales_invoice when all SIs paid.
	wf.append(
		"transitions",
		{
			"state": "Tasks Completed",
			"action": "Mark Completed",
			"next_state": "Completed",
			"allowed": accounts_role,
		},
	)

	# --- Claim phase ---
	# A claim raised on a completed order is resolved by simply closing it
	# again — it returns straight to Completed. It does NOT reopen the
	# operations/invoice cycle (no reassign, no new task spawn).
	wf.append(
		"transitions",
		{
			"state": "Completed",
			"action": "Raise Claim",
			"next_state": "Claim",
			"allowed": final_role,
		},
	)
	wf.append(
		"transitions",
		{
			"state": "Claim",
			"action": "Resolve Claim",
			"next_state": "Completed",
			"allowed": final_role,
		},
	)

	wf.save(ignore_permissions=True)
	_deactivate_other_workflows(document_type, wf.name)
	wf.db_set("is_active", 1)
	frappe.db.commit()


def ensure_workflows():
	if not frappe.db.exists("DocType", "Quotation"):
		return
	ensure_workflow_prerequisites()
	ensure_quotation_workflow()
	ensure_sales_order_workflow()

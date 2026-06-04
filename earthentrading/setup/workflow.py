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
		("ET Quote Draft", "Warning"),
		("ET Quote Pending", "Primary"),
		("ET Quote Approved", "Success"),
		("ET Quote Rejected", "Danger"),
		("ET SO Draft", "Warning"),
		("ET SO Trader Review", "Primary"),
		("ET SO Final Review", "Primary"),
		("ET SO Approved", "Success"),
		("ET SO Rejected", "Danger"),
	):
		_ensure_workflow_state(state, style)

	for action in ("Send for Approval", "Send to Trader", "Send to Final", "Approve", "Reject"):
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
			"state": "ET Quote Draft",
			"doc_status": "0",
			"allow_edit": edit_role,
		},
	)
	wf.append(
		"states",
		{
			"state": "ET Quote Pending",
			"doc_status": "0",
			"allow_edit": edit_role,
		},
	)
	wf.append(
		"states",
		{
			"state": "ET Quote Approved",
			"doc_status": "0",
			"allow_edit": edit_role,
		},
	)
	wf.append(
		"states",
		{
			"state": "ET Quote Rejected",
			"doc_status": "0",
			"allow_edit": edit_role,
		},
	)

	wf.transitions = []
	wf.append(
		"transitions",
		{
			"state": "ET Quote Draft",
			"action": "Send for Approval",
			"next_state": "ET Quote Pending",
			"allowed": edit_role,
		},
	)
	for role in approver_roles:
		wf.append(
			"transitions",
			{
				"state": "ET Quote Pending",
				"action": "Approve",
				"next_state": "ET Quote Approved",
				"allowed": role,
			},
		)
		wf.append(
			"transitions",
			{
				"state": "ET Quote Pending",
				"action": "Reject",
				"next_state": "ET Quote Rejected",
				"allowed": role,
			},
		)
	wf.append(
		"transitions",
		{
			"state": "ET Quote Rejected",
			"action": "Send for Approval",
			"next_state": "ET Quote Pending",
			"allowed": edit_role,
		},
	)

	wf.save(ignore_permissions=True)
	_deactivate_other_workflows(document_type, wf.name)
	wf.db_set("is_active", 1)
	frappe.db.commit()


def ensure_sales_order_workflow():
	"""Conditional two-track SO approval:
	- If custom_et_assigned_trader is set: Draft → Trader Review → Final Review → Approved/Rejected
	- Otherwise: Draft → Final Review → Approved/Rejected
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
	trader_role = "ET Trader" if frappe.db.exists("Role", "ET Trader") else "Sales Manager"
	final_role = "ET Operations" if frappe.db.exists("Role", "ET Operations") else "Sales Manager"

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

	wf.states = []
	for st in ("ET SO Draft", "ET SO Trader Review", "ET SO Final Review", "ET SO Rejected"):
		wf.append("states", {"state": st, "doc_status": "0", "allow_edit": edit_role})
	# Approved state auto-submits the SO (doc_status=1) when reached.
	wf.append(
		"states",
		{"state": "ET SO Approved", "doc_status": "1", "allow_edit": edit_role},
	)

	wf.transitions = []

	# Draft → Trader Review (when assigned trader is set)
	wf.append(
		"transitions",
		{
			"state": "ET SO Draft",
			"action": "Send to Trader",
			"next_state": "ET SO Trader Review",
			"allowed": edit_role,
			"condition": "doc.custom_et_assigned_trader",
		},
	)
	# Draft → Final Review (when no assigned trader — skip trader step)
	wf.append(
		"transitions",
		{
			"state": "ET SO Draft",
			"action": "Send for Approval",
			"next_state": "ET SO Final Review",
			"allowed": edit_role,
			"condition": "not doc.custom_et_assigned_trader",
		},
	)

	# Trader Review → Final Review (trader approves)
	wf.append(
		"transitions",
		{
			"state": "ET SO Trader Review",
			"action": "Approve",
			"next_state": "ET SO Final Review",
			"allowed": trader_role,
		},
	)
	# Trader Review → Rejected (trader rejects outright)
	wf.append(
		"transitions",
		{
			"state": "ET SO Trader Review",
			"action": "Reject",
			"next_state": "ET SO Rejected",
			"allowed": trader_role,
		},
	)

	# Final Review → Approved (operations finalises)
	wf.append(
		"transitions",
		{
			"state": "ET SO Final Review",
			"action": "Approve",
			"next_state": "ET SO Approved",
			"allowed": final_role,
		},
	)
	# Final Review → Rejected
	wf.append(
		"transitions",
		{
			"state": "ET SO Final Review",
			"action": "Reject",
			"next_state": "ET SO Rejected",
			"allowed": final_role,
		},
	)

	# Rejected → back to Draft so user can revise and resubmit
	wf.append(
		"transitions",
		{
			"state": "ET SO Rejected",
			"action": "Send for Approval",
			"next_state": "ET SO Draft",
			"allowed": edit_role,
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

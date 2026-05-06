# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Rebuild Workspace `content` EditorJS blocks from shortcuts, quick lists, and link cards."""

import json
import secrets

import frappe


def _block_id() -> str:
	return secrets.token_hex(6)


def shortcut_sig(row) -> tuple:
	return (
		row.type or "",
		row.link_to or "",
		row.url or "",
		row.doc_view or "",
		row.kanban_board or "",
		row.stats_filter or "",
	)


def build_editorjs_json(
	header_html: str,
	shortcut_labels: list[str],
	card_labels: list[str],
	quick_list_labels: list[str],
) -> str:
	blocks: list[dict] = []

	def push(**b):
		blocks.append(b)

	if header_html:
		push(id=_block_id(), type="header", data={"text": header_html, "col": 12})
		push(id=_block_id(), type="spacer", data={"col": 12})

	if quick_list_labels:
		push(
			id=_block_id(),
			type="header",
			data={"text": '<span class="h5"><b>Live lists</b></span>', "col": 12},
		)
		for lab in quick_list_labels:
			push(
				id=_block_id(),
				type="quick_list",
				data={"quick_list_name": lab, "col": 6},
			)
		push(id=_block_id(), type="spacer", data={"col": 12})

	push(
		id=_block_id(),
		type="header",
		data={"text": '<span class="h5"><b>Shortcuts</b></span>', "col": 12},
	)
	for lab in shortcut_labels:
		push(
			id=_block_id(),
			type="shortcut",
			data={"shortcut_name": lab, "col": 3},
		)
	push(id=_block_id(), type="spacer", data={"col": 12})
	push(
		id=_block_id(),
		type="header",
		data={"text": '<span class="h5"><b>Link cards</b></span>', "col": 12},
	)
	for lab in card_labels:
		push(
			id=_block_id(),
			type="card",
			data={"card_name": lab, "col": 4},
		)

	return json.dumps(blocks)


def sync_workspace_editorjs(workspace_name: str, header_html: str) -> None:
	"""Rebuild `content` using Desk widgets the current user role would see."""
	prev = frappe.session.user
	try:
		frappe.set_user("Administrator")
		from frappe.desk.desktop import Workspace as DeskWorkspace

		ws = frappe.get_doc("Workspace", workspace_name)
		page = frappe._dict(name=workspace_name, title=ws.title, public=True)
		desk = DeskWorkspace(page)
		desk.build_workspace()

		visible_shortcut = {shortcut_sig(frappe._dict(s)) for s in desk.shortcuts["items"]}
		shortcut_labels = [
			r.label for r in ws.shortcuts if r.label and shortcut_sig(r) in visible_shortcut
		]

		visible_card = {c["label"] for c in desk.cards["items"]}
		card_labels: list[str] = []
		for r in ws.links:
			if r.type != "Card Break" or not r.label:
				continue
			if frappe._(r.label) in visible_card:
				card_labels.append(r.label)

		quick_list_labels: list[str] = []
		if getattr(ws, "quick_lists", None):
			visible_ql = {q["label"] for q in desk.quick_lists["items"]}
			for r in ws.quick_lists:
				if r.label and frappe._(r.label) in visible_ql:
					quick_list_labels.append(r.label)

		# If visibility filtering yielded nothing while the workspace has widgets, fall back to all
		# rows — otherwise Desk shows a blank page (shortcut_sig / i18n / desk cache mismatches).
		if not shortcut_labels and ws.shortcuts:
			shortcut_labels = [r.label for r in ws.shortcuts if getattr(r, "label", None)]
		if not card_labels:
			card_labels = [r.label for r in ws.links if r.type == "Card Break" and r.label]
		if not quick_list_labels and getattr(ws, "quick_lists", None):
			quick_list_labels = [r.label for r in ws.quick_lists if getattr(r, "label", None)]

		body = build_editorjs_json(header_html, shortcut_labels, card_labels, quick_list_labels)
		frappe.db.set_value(
			"Workspace",
			workspace_name,
			"content",
			body,
			update_modified=False,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"earthentrading.workspace_editor.{workspace_name}")
	finally:
		frappe.set_user(prev)
	frappe.clear_cache()


def reload_workspace_into_doc_for_export(workspace_name: str) -> None:
	"""When developer_mode saves standard Workspaces to disk, persist `content` on the doc."""
	if not getattr(frappe.conf, "developer_mode", 0):
		return
	c = frappe.db.get_value("Workspace", workspace_name, "content")
	if not c or c == "[]":
		return
	doc = frappe.get_doc("Workspace", workspace_name)
	doc.content = c
	doc.save(ignore_permissions=True)

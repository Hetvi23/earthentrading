// On Sales Order creation, prompt Administrator / ET Operations users
// asking whether they want to assign this SO to someone.

(function () {
	const DEBUG = true;
	function log(...args) {
		if (DEBUG) console.log("[et-so-assign]", ...args);
	}
	log("script loaded");

	const ALLOWED_ROLES = ["Administrator", "System Manager", "ET Operations"];

	frappe.ui.form.on("Sales Order", {
		refresh(frm) {
			log("refresh", frm.doc.name, "docstatus=", frm.doc.docstatus, "ws=", frm.doc.workflow_state);
			// Workflow approval submits server-side via apply_workflow and reloads
			// the form — no client on_submit event fires. Detect the docstatus
			// 0 → 1 transition between refreshes here.
			const prevKey = "__et_so_prev_status_" + frm.doc.name;
			const prev = window[prevKey];
			window[prevKey] = frm.doc.docstatus;
			if (prev === 0 && frm.doc.docstatus === 1) {
				log("detected submit via workflow (prev docstatus 0, now 1)");
				maybeOpenDialog(frm);
			}
		},
		on_submit(frm) {
			log("on_submit fired, doc.name=", frm.doc.name);
			maybeOpenDialog(frm);
		},
	});

	function maybeOpenDialog(frm) {
		const reason = shouldPrompt(frm);
		if (reason !== true) {
			log("not prompting:", reason);
			return;
		}
		log("opening assign dialog");
		markPrompted(frm);
		openAssignDialog(frm);
	}

	function shouldPrompt(frm) {
		if (!frm.doc || !frm.doc.name) return "no doc.name";

		// Only after the SO is fully submitted (docstatus = 1).
		if (frm.doc.docstatus !== 1) return "not submitted yet (docstatus=" + frm.doc.docstatus + ")";

		// Don't prompt twice for the same doc in one page session.
		if (window["__et_so_prompted_" + frm.doc.name]) return "already prompted";

		// Only for users with Administrator / System Manager / ET Operations.
		const hasRole = ALLOWED_ROLES.some((r) => {
			try {
				return frappe.user.has_role(r);
			} catch (e) {
				return (frappe.user_roles || []).indexOf(r) !== -1;
			}
		});
		if (!hasRole) return "user lacks role; roles=" + JSON.stringify(frappe.user_roles || []);

		// Skip if it already has an assignee.
		const docinfo = (frm.get_docinfo && frm.get_docinfo()) || {};
		const assignments = docinfo.assignments || [];
		if (assignments.length > 0) return "already has assignees";

		return true;
	}

	function markPrompted(frm) {
		window["__et_so_prompted_" + frm.doc.name] = true;
	}

	function openAssignDialog(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Assign this Sales Order?"),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "intro",
					options: `<p class="text-muted" style="margin-bottom:8px">
						<b>${frappe.utils.escape_html(frm.doc.name)}</b> has been created.
						Assign it to someone now, or skip and assign later from the form sidebar.
					</p>`,
				},
				{
					fieldtype: "Link",
					fieldname: "assignee",
					label: __("Assign to"),
					options: "User",
					get_query: () => ({ filters: { enabled: 1, user_type: "System User" } }),
				},
				{
					fieldtype: "Small Text",
					fieldname: "note",
					label: __("Note (optional)"),
					description: __("Shown to the assignee on the ToDo notification."),
				},
			],
			primary_action_label: __("Assign"),
			primary_action(values) {
				if (!values.assignee) {
					frappe.msgprint(__("Pick a user or click Skip."));
					return;
				}
				frappe
					.call({
						method: "frappe.desk.form.assign_to.add",
						args: {
							assign_to: [values.assignee],
							doctype: frm.doctype,
							name: frm.docname,
							description: values.note || __("Assigned on creation of {0}", [frm.docname]),
						},
					})
					.then(() => {
						d.hide();
						frappe.show_alert(
							{
								message: __("Assigned to {0}", [values.assignee]),
								indicator: "green",
							},
							5
						);
						frm.reload_doc();
					});
			},
			secondary_action_label: __("Skip"),
			secondary_action() {
				d.hide();
			},
		});
		d.show();
	}
})();

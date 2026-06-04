// Sales Order client script — three concerns:
//   1) On submit (final approval), prompt Admin / ET Ops to assign the SO.
//   2) Customer Purchase Order picker: when Order Type = Sales Contract,
//      the PO field is a Link → Sales Order filtered to Order Type =
//      Trade Contract.
//   3) On submitted SOs, add a "Create Project" button that runs
//      earthentrading.api.project_from_so.create_from_sales_order.

(function () {
	const DEBUG = true;
	function log(...args) {
		if (DEBUG) console.log("[et-so-client]", ...args);
	}
	log("script loaded");

	const ALLOWED_ROLES = ["Administrator", "System Manager", "ET Operations"];

	frappe.ui.form.on("Sales Order", {
		refresh(frm) {
			log("refresh", frm.doc.name, "docstatus=", frm.doc.docstatus, "ws=", frm.doc.workflow_state);

			// (2) Limit po_no to Trade Contract SOs when current SO is a
			// Sales Contract. (po_no is a Link → Sales Order via property
			// setter — see setup/property_setters.py.)
			frm.set_query("po_no", () => ({
				filters: { order_type: "Trade Contract", docstatus: 1 },
			}));

			// (3) Create Project button on submitted SOs.
			if (frm.doc.docstatus === 1) {
				frm.add_custom_button(__("Create Project"), () => {
					openCreateProjectDialog(frm);
				});
			}

			// (1) Workflow approval submits server-side via apply_workflow and
			// reloads — no client on_submit event fires. Detect the docstatus
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

	function openCreateProjectDialog(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Create Project from {0}", [frm.doc.name]),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "intro",
					options: `<p class="text-muted" style="margin-bottom:8px">
						Customer, Company, Delivery Date are taken from this Sales Order.
						Pick a checklist template and (optionally) an assignee.
					</p>`,
				},
				{
					fieldtype: "Link",
					fieldname: "template",
					label: __("ET Task Template"),
					options: "ET Task Template",
					reqd: 1,
				},
				{
					fieldtype: "Link",
					fieldname: "assignee",
					label: __("Assign tasks to"),
					options: "User",
					get_query: () => ({
						filters: { enabled: 1, user_type: "System User" },
					}),
				},
			],
			primary_action_label: __("Create"),
			primary_action(values) {
				frappe
					.call({
						method: "earthentrading.api.project_from_so.create_from_sales_order",
						args: {
							sales_order: frm.doc.name,
							template: values.template,
							assignee: values.assignee || null,
						},
					})
					.then((r) => {
						if (!r || !r.message) return;
						d.hide();
						const project = r.message.name;
						const verb = r.message.created ? __("Created") : __("Found existing");
						frappe.show_alert(
							{
								message: __("{0} project {1}", [verb, project]),
								indicator: "green",
							},
							5
						);
						setTimeout(() => frappe.set_route("Form", "Project", project), 600);
					});
			},
		});
		d.show();
	}

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

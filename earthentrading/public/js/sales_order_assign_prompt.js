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

			// Preview the buyer + seller trade emails (with their To / CC).
			frm.add_custom_button(__("Preview Trade Email"), () => openEmailPreview(frm));

			// (3) State-driven action buttons on submitted SOs.
			if (frm.doc.docstatus === 1) {
				addLifecycleButtons(frm);
				// Offer "Create > Project" on every submitted SO.
				frm.add_custom_button(
					__("Project"),
					() => openCreateProjectDialog(frm),
					__("Create")
				);
				// Strip the Create menu down to just Sales Invoice + Project.
				restrictCreateMenu(frm);
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

	// --- Email-recipient auto-fill & Draft clearing --------------------------
	frappe.ui.form.on("Sales Order", {
		customer(frm) {
			dropRecipientSide(frm, "Customer");
			fillRecipients(frm);
			frm.set_value("custom_et_buyer_email_draft", "");
			frm.set_value("custom_et_seller_email_draft", "");
		},
		custom_et_supplier(frm) {
			dropRecipientSide(frm, "Supplier");
			fillRecipients(frm);
			frm.set_value("custom_et_buyer_email_draft", "");
			frm.set_value("custom_et_seller_email_draft", "");
		},
		customer_address(frm) {
			frm.set_value("custom_et_buyer_email_draft", "");
			frm.set_value("custom_et_seller_email_draft", "");
		},
		contact_person(frm) {
			frm.set_value("custom_et_buyer_email_draft", "");
			frm.set_value("custom_et_seller_email_draft", "");
		},
	});

	// Pull the candidate recipient rows for the chosen Customer + Supplier and
	// merge in any that aren't already present (preserving existing rows + their
	// Primary/CC ticks). Server validate is the source of truth on save.
	function fillRecipients(frm) {
		const customer = frm.doc.customer;
		const supplier = frm.doc.custom_et_supplier;
		if (!customer && !supplier) return;
		frappe.call({
			method: "earthentrading.api.recipients.get_recipient_candidates",
			args: { customer: customer || null, supplier: supplier || null },
			callback(r) {
				if (!r || !r.message) return;
				mergeRecipients(frm, r.message.rows || []);
				const counts = r.message.user_counts || {};
				const multi = [];
				if ((counts.Customer || 0) > 1) multi.push(__("Customer"));
				if ((counts.Supplier || 0) > 1) multi.push(__("Supplier"));
				if (multi.length) {
					frappe.show_alert(
						{
							message: __("Multiple people work with the {0} — review the CC list.", [
								multi.join(__(" and ")),
							]),
							indicator: "orange",
						},
						7
					);
				}
			},
		});
	}

	function recipientKey(d) {
		return (d.party_side || "") + "|" + (d.email || "").trim().toLowerCase();
	}

	function mergeRecipients(frm, rows) {
		const existing = frm.doc.custom_et_email_recipients || [];
		const seen = new Set(existing.map(recipientKey));
		let added = 0;
		rows.forEach((row) => {
			const key = recipientKey(row);
			if (seen.has(key)) return;
			seen.add(key);
			const child = frm.add_child("custom_et_email_recipients");
			child.party_side = row.party_side;
			child.source = row.source;
			child.recipient_name = row.recipient_name;
			child.email = row.email;
			child.is_primary = row.is_primary;
			child.is_cc = row.is_cc;
			added += 1;
		});
		if (added) frm.refresh_field("custom_et_email_recipients");
	}

	// When a party link changes, drop that side's rows so stale recipients from
	// the previously selected Customer/Supplier don't linger in the grid (mirrors
	// the server-side reconcile).
	function dropRecipientSide(frm, side) {
		const rows = frm.doc.custom_et_email_recipients || [];
		const keep = rows.filter((d) => d.party_side !== side);
		if (keep.length === rows.length) return;
		keep.forEach((d, i) => {
			d.idx = i + 1;
		});
		frm.doc.custom_et_email_recipients = keep;
		frm.refresh_field("custom_et_email_recipients");
	}

	function openEmailPreview(frm) {
		frappe.call({
			method: "earthentrading.api.email_preview.preview",
			args: { doc: JSON.stringify(frm.doc) },
			freeze: true,
			freeze_message: __("Rendering email preview…"),
			callback(r) {
				if (!r || !r.message) return;
				const m = r.message;
				const esc = (s) => frappe.utils.escape_html(s || "");
				// Only the Trade Manager (or an admin) may edit + save the draft.
				const canEdit =
					frappe.session.user === "Administrator" ||
					["ET Trader Manager", "Sales Manager", "System Manager"].some((r) => {
						try {
							return frappe.user.has_role(r);
						} catch (e) {
							return (frappe.user_roles || []).indexOf(r) !== -1;
						}
					});
				const ro = canEdit ? 0 : 1;
				const heading = (label, party, edited) =>
					`<h5 style="margin:0;font-weight:600;">${esc(label)} <span style="color:var(--text-muted);font-weight:400;">→ ${esc(party || "")}</span>${
						edited ? ` <span style="color:var(--green-600);font-weight:400;font-size:11px;">(${__("edited")})</span>` : ""
					}</h5>`;

				// To / CC / Subject / Body are all editable. Whatever is saved here is
				// what the auto-send ships on approval.
				const sideFields = (side, label, d) => [
					{ fieldtype: "HTML", fieldname: side + "_hd", options: heading(label, d.party, d.edited) },
					{ fieldtype: "Data", fieldname: side + "_to", label: __("To"), default: (d.to || []).join(", "), read_only: ro },
					{ fieldtype: "Data", fieldname: side + "_cc", label: __("CC"), default: (d.cc || []).join(", "), read_only: ro },
					{ fieldtype: "Data", fieldname: side + "_subject", label: __("Subject"), default: d.subject || "", read_only: ro },
					{ fieldtype: "Text Editor", fieldname: side + "_body", label: __("Body"), default: d.html || "", read_only: ro },
				];

				const dlg = new frappe.ui.Dialog({
					title: __("Trade Email Preview"),
					size: "extra-large",
					fields: [
						...sideFields("buyer", __("Buyer"), m.buyer),
						{ fieldtype: "Section Break" },
						...sideFields("seller", __("Seller"), m.seller),
					],
				});

				if (canEdit) {
					dlg.set_primary_action(__("Save Draft"), () => {
						if (frm.is_new()) {
							frappe.msgprint(__("Save the Sales Order first, then edit the email."));
							return;
						}
						const v = dlg.get_values(true) || {};
						const draft = (side) =>
							JSON.stringify({
								to: v[side + "_to"] || "",
								cc: v[side + "_cc"] || "",
								subject: v[side + "_subject"] || "",
								body: v[side + "_body"] || "",
							});
						const buyer = draft("buyer");
						const seller = draft("seller");
						frappe.call({
							method: "earthentrading.api.email_preview.save_draft",
							args: { sales_order: frm.doc.name, buyer: buyer, seller: seller },
							freeze: true,
							freeze_message: __("Saving draft…"),
							callback(res) {
								if (!res || !res.message || !res.message.ok) return;
								// Mirror into the in-memory doc so it's not re-rendered as default.
								frm.doc.custom_et_buyer_email_draft = buyer;
								frm.doc.custom_et_seller_email_draft = seller;
								dlg.hide();
								frappe.show_alert(
									{
										message: __("Email draft saved — it will be sent automatically on approval."),
										indicator: "green",
									},
									6
								);
							},
						});
					});
				} else {
					dlg.set_message(__("Only the Trade Manager can edit. This is a preview."));
				}
				dlg.show();
			},
		});
	}

	function addLifecycleButtons(frm) {
		const ws = frm.doc.workflow_state;

		if (ws === "Pending Assignment") {
			frm.add_custom_button(
				__("Assign Team Member"),
				() => openAssignTeamMemberDialog(frm),
				__("Operations")
			);
		}

		if (ws === "Completed") {
			frm.add_custom_button(
				__("Raise Claim"),
				() => openRaiseClaimDialog(frm),
				__("Operations")
			);
		}

		// Once a claim is raised the only action is to close it again — resolving
		// returns the order straight to Completed (no reassign / re-run).
		if (ws === "Claim") {
			frm.add_custom_button(
				__("Resolve Claim"),
				() => {
					frappe.confirm(__("Mark claim resolved and close this order again?"), () => {
						frappe
							.call({
								method: "earthentrading.api.operations.resolve_claim",
								args: { sales_order: frm.docname },
							})
							.then(() => {
								frappe.show_alert({ message: __("Claim resolved"), indicator: "green" }, 5);
								frm.reload_doc();
							});
					});
				},
				__("Operations")
			);
		}
	}

	function restrictCreateMenu(frm) {
		// The standard ERPNext "Create" dropdown carries many actions
		// (Delivery Note, Payment, Material Request, Pick List, …). Keep only:
		//   • Project   — always (our action, added above)
		//   • Sales Invoice — only when the SO is in "Tasks Completed" state AND
		//     the current user has the Accounts Manager role.
		// Frappe v15 renders the group as `.inner-group-button[data-label="Create"]`
		// and each item as `a.dropdown-item[data-label="<English label>"]`; we match
		// on the language-independent data-label and hide everything else. Re-applied
		// a couple of times because ERPNext (re)adds its buttons during refresh.
		const isAccountsManager = (() => {
			try {
				return frappe.user.has_role("Accounts Manager");
			} catch (e) {
				return (frappe.user_roles || []).indexOf("Accounts Manager") !== -1;
			}
		})();
		const allowInvoice =
			frm.doc.workflow_state === "Tasks Completed" && isAccountsManager;
		const keep = new Set(["Project"]);
		if (allowInvoice) keep.add("Sales Invoice");

		const apply = () => {
			const $tb =
				frm.page && frm.page.inner_toolbar && frm.page.inner_toolbar.length
					? frm.page.inner_toolbar
					: $(".page-actions .custom-actions");
			if (!$tb || !$tb.length) return;

			// Find the "Create" group (data-label is encodeURIComponent of the
			// English group label); fall back to matching the button text.
			let $group = $tb.find(
				'.inner-group-button[data-label="' + encodeURIComponent("Create") + '"]'
			);
			if (!$group.length) {
				$tb.find(".inner-group-button").each(function () {
					const txt = ($(this).children("button").first().text() || "").trim();
					if (txt === __("Create")) $group = $(this);
				});
			}
			if (!$group || !$group.length) return;

			$group.find("a.dropdown-item").each(function () {
				const $item = $(this);
				let label = "";
				try {
					label = decodeURIComponent($item.attr("data-label") || "");
				} catch (e) {
					label = ($item.text() || "").trim();
				}
				$item.toggle(keep.has(label));
			});
		};
		apply();
		setTimeout(apply, 300);
		setTimeout(apply, 900);
	}

	function openAssignTeamMemberDialog(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Assign team member for {0}", [frm.doc.name]),
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "intro",
					options: `<p class="text-muted" style="margin-bottom:8px">
						Operations: pick the team member who will own this SO,
						and the task checklist template. The user gets read+write
						on the SO via ToDo + Share. The project gets created with
						the picked template and the user as an assignee.
					</p>`,
				},
				{
					fieldtype: "Link",
					fieldname: "assignee",
					label: __("Assign to"),
					options: "User",
					reqd: 1,
					get_query: () => ({
						filters: { enabled: 1, user_type: "System User" },
					}),
				},
				{
					fieldtype: "Link",
					fieldname: "template",
					label: __("ET Task Template"),
					options: "ET Task Template",
					reqd: 1,
				},
			],
			primary_action_label: __("Assign"),
			primary_action(values) {
				frappe
					.call({
						method: "earthentrading.api.operations.assign_team_member",
						args: {
							sales_order: frm.docname,
							user: values.assignee,
							template: values.template,
						},
					})
					.then((r) => {
						if (!r || !r.message) return;
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
		});
		d.show();
	}

	function openRaiseClaimDialog(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Raise claim on {0}", [frm.doc.name]),
			fields: [
				{
					fieldtype: "Small Text",
					fieldname: "note",
					label: __("Reason / details"),
				},
			],
			primary_action_label: __("Raise Claim"),
			primary_action(values) {
				frappe
					.call({
						method: "earthentrading.api.operations.raise_claim",
						args: { sales_order: frm.docname, note: values.note || null },
					})
					.then(() => {
						d.hide();
						frappe.show_alert({ message: __("Claim raised"), indicator: "orange" }, 5);
						frm.reload_doc();
					});
			},
		});
		d.show();
	}

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

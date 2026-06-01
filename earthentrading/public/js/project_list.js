// Bulk "Assign ET Task Template" action on the Project list view.
// Prompts for a template, optionally re-spawns checklists that already ran,
// then calls earthentrading.api.project_bulk.bulk_assign_template.

frappe.listview_settings = frappe.listview_settings || {};

frappe.listview_settings["Project"] = frappe.listview_settings["Project"] || {};

(function (settings) {
	const onload_chain = settings.onload;

	settings.onload = function (listview) {
		if (typeof onload_chain === "function") {
			onload_chain(listview);
		}

		listview.page.add_actions_menu_item(
			__("Assign ET Task Template"),
			() => open_dialog(listview),
			true /* standard */
		);
	};
})(frappe.listview_settings["Project"]);

function open_dialog(listview) {
	const selected = listview.get_checked_items().map((d) => d.name);
	if (!selected.length) {
		frappe.msgprint(__("Select one or more Projects first."));
		return;
	}

	const d = new frappe.ui.Dialog({
		title: __("Assign ET Task Template ({0} projects)", [selected.length]),
		fields: [
			{
				fieldname: "template",
				fieldtype: "Link",
				options: "ET Task Template",
				label: __("Template"),
				reqd: 1,
			},
			{
				fieldname: "overwrite",
				fieldtype: "Check",
				label: __("Re-spawn even if checklist tasks were already created"),
				default: 0,
				description: __(
					"By default, projects with the 'Checklist tasks created' flag are skipped. " +
						"Enable this to clear the flag and create tasks again (existing tasks are not deleted)."
				),
			},
		],
		primary_action_label: __("Assign"),
		primary_action: (values) => {
			d.hide();
			frappe.dom.freeze(__("Spawning tasks on {0} projects…", [selected.length]));
			frappe
				.call({
					method: "earthentrading.api.project_bulk.bulk_assign_template",
					args: {
						projects: selected,
						template: values.template,
						overwrite: values.overwrite ? 1 : 0,
					},
				})
				.then((r) => {
					frappe.dom.unfreeze();
					if (!r || !r.message) {
						return;
					}
					const res = r.message;
					const lines = [];
					lines.push(__("Spawned: {0}", [res.spawned.length]));
					if (res.skipped.length) {
						lines.push(__("Skipped (already done): {0}", [res.skipped.length]));
					}
					if (res.errors.length) {
						lines.push(__("Errors: {0}", [res.errors.length]));
						res.errors.slice(0, 5).forEach((err) => {
							lines.push(`• ${err.project}: ${err.error}`);
						});
					}
					frappe.msgprint({
						title: __("Bulk template assignment"),
						message: lines.join("<br>"),
						indicator: res.errors.length ? "orange" : "green",
					});
					listview.refresh();
				})
				.catch(() => {
					frappe.dom.unfreeze();
				});
		},
	});

	d.show();
}

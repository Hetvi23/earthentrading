// Customer / Supplier: turn the "Add Emails (one per line)" quick box into rows
// in the Emails table live — as the user enters them — so they don't have to
// retype into the (mandatory-email) table. Mirrors the server-side
// earthentrading.events.party.sync_party_emails fallback that runs on save.

(function () {
	const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

	function syncEmails(frm) {
		const raw = (frm.doc.custom_et_emails_quick || "").trim();
		if (!raw) return;

		const rows = frm.doc.custom_et_emails || [];
		const existing = new Set(rows.map((r) => (r.email || "").trim().toLowerCase()));
		let hasPrimary = rows.some((r) => r.is_primary);
		let added = false;
		const skipped = [];

		raw
			.replace(/[;,]/g, "\n")
			.split("\n")
			.forEach((line) => {
				const addr = line.trim();
				if (!addr) return;
				if (!EMAIL_RE.test(addr)) {
					skipped.push(addr);
					return;
				}
				if (existing.has(addr.toLowerCase())) return;
				existing.add(addr.toLowerCase());
				const row = frm.add_child("custom_et_emails");
				row.email = addr;
				row.is_primary = hasPrimary ? 0 : 1;
				hasPrimary = true;
				added = true;
			});

		// Clear the quick box (this re-fires the handler, but raw is now empty).
		frm.set_value("custom_et_emails_quick", "");
		if (added) frm.refresh_field("custom_et_emails");
		if (skipped.length) {
			frappe.show_alert(
				{ message: __("Skipped invalid email(s): {0}", [skipped.join(", ")]), indicator: "orange" },
				6
			);
		}
	}

	const handlers = {
		custom_et_emails_quick(frm) {
			syncEmails(frm);
		},
	};

	frappe.ui.form.on("Customer", handlers);
	frappe.ui.form.on("Supplier", handlers);
})();

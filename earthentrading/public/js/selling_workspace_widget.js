// Inline "My Sales Orders" widget injected directly into the Selling
// workspace page. Sits below the dashboard charts with a toggle to switch
// between "Only mine" and "All".

(function () {
	const TARGET_WORKSPACE = "Selling";
	const WIDGET_ID = "et-selling-so-widget";
	const DEBUG = true;

	function log(...args) {
		if (DEBUG) console.log("[et-selling-widget]", ...args);
	}
	log("script loaded");

	function isOnSelling() {
		const path = (window.location.pathname || "").toLowerCase();
		if (path === "/app/selling" || path.startsWith("/app/selling/")) return true;
		const route = (frappe.get_route && frappe.get_route()) || [];
		if (route[0] !== "Workspaces") return false;
		const slug = String(route[1] || "").toLowerCase();
		return slug === "selling" || slug === slugify(TARGET_WORKSPACE);
	}

	function slugify(s) {
		return String(s)
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");
	}

	function getWorkspaceContainer() {
		const candidates = [
			'[data-page-name="Selling"]:visible',
			".layout-main-section[data-page-name=\"Selling\"]",
			".page-container.show .layout-main-section",
			".layout-main-section:visible",
			".main-section:visible",
		];
		for (const sel of candidates) {
			const $el = $(sel);
			if ($el.length) return $el.last();
		}
		return $();
	}

	function mountWidget() {
		if (!isOnSelling()) return;
		const $container = getWorkspaceContainer();
		if (!$container || !$container.length) return;
		if ($("#" + WIDGET_ID).length) return;

		const $widget = $(`
			<div id="${WIDGET_ID}" class="et-selling-widget"
				style="margin:16px 0 24px; padding:16px; border:1px solid var(--border-color); border-radius:8px;">
				<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; gap:12px; flex-wrap:wrap;">
					<h5 style="margin:0; font-weight:600;">My Sales Orders</h5>
					<div style="display:flex; align-items:center; gap:12px;">
						<label style="display:flex; align-items:center; gap:6px; margin:0; font-size:13px;">
							<input type="checkbox" id="et-so-only-mine" checked />
							Only mine
						</label>
						<select class="form-control input-sm" id="et-so-status" style="max-width:180px">
							<option value="">Any status</option>
							<option>Draft</option>
							<option>To Deliver and Bill</option>
							<option>To Bill</option>
							<option>To Deliver</option>
							<option>Completed</option>
							<option>Cancelled</option>
							<option>Closed</option>
						</select>
						<small class="text-muted" id="et-so-count">—</small>
					</div>
				</div>
				<div id="et-so-results" class="table-responsive" style="max-height:520px; overflow:auto;">
					<table class="table table-bordered table-sm" style="font-size:13px; margin-bottom:0;">
						<thead style="position:sticky; top:0; background:var(--bg-color);">
							<tr>
								<th>Sales Order</th>
								<th>Customer</th>
								<th>Buyer</th>
								<th>Contract</th>
								<th>Assigned Trader</th>
								<th>Workflow State</th>
								<th>Status</th>
								<th>Date</th>
								<th>Total</th>
							</tr>
						</thead>
						<tbody>
							<tr><td colspan="9" class="text-center text-muted" style="padding:24px;">Loading…</td></tr>
						</tbody>
					</table>
				</div>
			</div>
		`);

		// Append below the existing EditorJS blocks (charts).
		const candidates = [
			$container.find(".codex-editor").last().parent(),
			$container.find(".standard-form-section").last(),
			$container.find(".ce-block-wrapper").last().parent(),
			$container.find(".page-content").last(),
			$container,
		];
		let inserted = false;
		for (const $target of candidates) {
			if ($target && $target.length) {
				$target.append($widget);
				inserted = true;
				log("widget inserted into:", $target[0]);
				break;
			}
		}
		if (!inserted) {
			$("body").append($widget);
			log("widget inserted into body (fallback)");
		}

		bind($widget);
		refresh($widget);
	}

	function bind($w) {
		$("#et-so-only-mine", $w).on("change", () => refresh($w));
		$("#et-so-status", $w).on("change", () => refresh($w));
	}

	function refresh($w) {
		const mine = $("#et-so-only-mine", $w).is(":checked") ? 1 : 0;
		const status = $("#et-so-status", $w).val() || null;
		$("#et-so-count", $w).text("Loading…");
		frappe
			.call({
				method: "earthentrading.api.sales_order_list.search",
				args: { mine, status },
			})
			.then((r) => {
				const rows = (r && r.message) || [];
				render($w, rows);
			})
			.catch(() => {
				$("#et-so-count", $w).text("Error");
			});
	}

	function render($w, rows) {
		const $tb = $("#et-so-results tbody", $w).empty();
		if (!rows.length) {
			$tb.append('<tr><td colspan="9" class="text-center text-muted" style="padding:24px;">No matching sales orders.</td></tr>');
			$("#et-so-count", $w).text("0 orders");
			return;
		}
		const stateColor = {
			"Draft": "gray",
			"Trader Review": "orange",
			"Trader Manager Review": "orange",
			"Final Review": "blue",
			"Pending Assignment": "purple",
			"In Progress": "blue",
			"Raise Invoice": "orange",
			"Completed": "green",
			"Claim": "red",
			"Rejected": "red",
		};
		rows.forEach((r) => {
			const wsLabel = r.workflow_state || "—";
			const wsBg = stateColor[wsLabel] || "gray";
			const total =
				r.total != null
					? `${formatNumber(r.total)} ${r.currency || ""}`
					: "—";
			const date = r.transaction_date || "";
			$tb.append(`
				<tr>
					<td><a href="/app/sales-order/${encodeURIComponent(r.name)}">${escapeHtml(r.name)}</a></td>
					<td>${escapeHtml(r.customer_name || r.customer || "")}</td>
					<td>${escapeHtml(r.buyer || "")}</td>
					<td>${escapeHtml(r.contract_type || "")}</td>
					<td>${escapeHtml(r.assigned_trader || "")}</td>
					<td><span class="indicator-pill ${wsBg}" style="padding:2px 8px; border-radius:9999px; font-size:11px; background-color:var(--${wsBg}-bg, #eee); color:var(--${wsBg}-text, #333);">${escapeHtml(wsLabel)}</span></td>
					<td>${escapeHtml(r.status || "")}</td>
					<td>${escapeHtml(date)}</td>
					<td style="text-align:right;">${escapeHtml(total)}</td>
				</tr>
			`);
		});
		$("#et-so-count", $w).text(rows.length + " orders");
	}

	function escapeHtml(s) {
		return (frappe.utils && frappe.utils.escape_html ? frappe.utils.escape_html(s) : String(s))
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;");
	}

	function formatNumber(n) {
		try {
			return Number(n).toLocaleString();
		} catch (e) {
			return String(n);
		}
	}

	function unmountIfElsewhere() {
		if (isOnSelling()) return;
		$("#" + WIDGET_ID).remove();
	}

	$(document).on("app_ready page-change", () => {
		setTimeout(() => {
			unmountIfElsewhere();
			mountWidget();
		}, 300);
	});
	if (frappe && frappe.router && frappe.router.on) {
		frappe.router.on("change", () => {
			setTimeout(() => {
				unmountIfElsewhere();
				mountWidget();
			}, 300);
		});
	}
	$(document).ready(() => {
		setTimeout(mountWidget, 500);
		try {
			const obs = new MutationObserver(() => {
				if (isOnSelling()) mountWidget();
				else unmountIfElsewhere();
			});
			obs.observe(document.body, { childList: true, subtree: true });
		} catch (e) {
			// MutationObserver missing — app_ready hook is enough.
		}
	});
})();

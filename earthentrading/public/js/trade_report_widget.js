// Inline "Filter leads by trade report" widget injected directly into the
// Earth Trading CRM workspace page. No redirect — filter strip + results
// table render right below the existing shortcut tiles.

(function () {
	const TARGET_WORKSPACE = "CRM";
	const WIDGET_ID = "et-trade-report-widget";
	const DEBUG = true;

	function log(...args) {
		if (DEBUG) console.log("[et-trade-widget]", ...args);
	}
	log("script loaded");

	let countriesCache = null;

	function isOnEarthCRM() {
		// Match by URL path first — most reliable across Frappe / Frappe-CRM
		// workspace variants.
		const path = (window.location.pathname || "").toLowerCase();
		if (path === "/app/crm" || path.startsWith("/app/crm/")) {
			return true;
		}
		// Fallback: check the in-app router.
		const route = (frappe.get_route && frappe.get_route()) || [];
		if (route[0] !== "Workspaces") return false;
		const slug = String(route[1] || "").toLowerCase();
		return slug === "crm" || slug === slugify(TARGET_WORKSPACE);
	}

	function slugify(s) {
		return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
	}

	function getWorkspaceContainer() {
		// Try the most specific selectors first.
		const candidates = [
			'[data-page-name="CRM"]:visible',
			'.layout-main-section[data-page-name="CRM"]',
			'.page-container.show .layout-main-section',
			'.layout-main-section:visible',
			'.main-section:visible',
		];
		for (const sel of candidates) {
			const $el = $(sel);
			if ($el.length) return $el.last();
		}
		return $();
	}

	function mountWidget() {
		const onCRM = isOnEarthCRM();
		log("mountWidget called, onCRM=", onCRM, "path=", window.location.pathname, "route=", frappe.get_route && frappe.get_route());
		if (!onCRM) return;
		const $container = getWorkspaceContainer();
		log("container found:", $container.length, $container.length ? $container[0] : null);
		if (!$container || !$container.length) return;
		if ($("#" + WIDGET_ID).length) {
			log("already mounted, skipping");
			return;
		}

		const $widget = $(`
			<div id="${WIDGET_ID}" class="et-trade-widget" style="margin:8px 0 16px; padding:16px; border:1px solid var(--border-color); border-radius:8px;">
				<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
					<h5 style="margin:0; font-weight:600;">Filter leads by trade report</h5>
					<small class="text-muted" id="et-tr-status">—</small>
				</div>
				<div class="et-trade-filters" style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px;">
					<input type="text" class="form-control input-sm" id="et-tr-commodity"
						placeholder="Commodity (contains)" style="max-width:200px"/>
					<select class="form-control input-sm" id="et-tr-origin" style="max-width:180px">
						<option value="">Any origin</option>
					</select>
					<select class="form-control input-sm" id="et-tr-destination" style="max-width:180px">
						<option value="">Any destination</option>
					</select>
					<select class="form-control input-sm" id="et-tr-role" style="max-width:140px">
						<option value="">Any role</option>
						<option>Buyer</option>
						<option>Seller</option>
						<option>Broker</option>
					</select>
					<button class="btn btn-primary btn-sm" id="et-tr-apply">Apply</button>
					<button class="btn btn-secondary btn-sm" id="et-tr-clear">Clear</button>
				</div>
				<div id="et-tr-results" class="table-responsive" style="max-height:520px; overflow:auto;">
					<table class="table table-bordered table-sm" style="font-size:13px; margin-bottom:0;">
						<thead style="position:sticky; top:0; background:var(--bg-color);">
							<tr>
								<th>Lead</th>
								<th>Organization</th>
								<th>Status</th>
								<th>Function</th>
								<th>Commodity</th>
								<th>Origin</th>
								<th>Destination</th>
								<th>Role</th>
							</tr>
						</thead>
						<tbody>
							<tr><td colspan="8" class="text-center text-muted" style="padding:24px;">Loading…</td></tr>
						</tbody>
					</table>
				</div>
			</div>
		`);

		// Append to the workspace body. Prefer the .codex-editor (EditorJS) parent
		// so it sits right below the existing blocks. Fall back to the workspace
		// body / wrapper / container in order of specificity.
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
				log("widget inserted into:", $target[0]);
				inserted = true;
				break;
			}
		}
		if (!inserted) {
			$("body").append($widget);
			log("widget inserted into body (fallback)");
		}

		populateCountries($widget);
		bind($widget);
		apply($widget); // initial load
	}

	function populateCountries($w) {
		const fill = (countries) => {
			const opts = countries
				.map((c) => `<option value="${escape_attr(c)}">${escape_html(c)}</option>`)
				.join("");
			$("#et-tr-origin", $w).append(opts);
			$("#et-tr-destination", $w).append(opts);
		};
		if (countriesCache) {
			fill(countriesCache);
			return;
		}
		frappe.db
			.get_list("Country", { fields: ["name"], limit: 500, order_by: "name" })
			.then((rows) => {
				countriesCache = (rows || []).map((r) => r.name);
				fill(countriesCache);
			})
			.catch(() => {
				// Country list isn't critical — user can still type-search via Commodity / Role.
			});
	}

	function bind($w) {
		$("#et-tr-apply", $w).on("click", () => apply($w));
		$("#et-tr-clear", $w).on("click", () => clear($w));
		$w.find("select, input").on("keydown", (e) => {
			if (e.key === "Enter") apply($w);
		});
		$w.find("select").on("change", () => apply($w));
	}

	function apply($w) {
		const args = {
			commodity: $("#et-tr-commodity", $w).val() || null,
			origin: $("#et-tr-origin", $w).val() || null,
			destination: $("#et-tr-destination", $w).val() || null,
			role: $("#et-tr-role", $w).val() || null,
		};
		$("#et-tr-status", $w).text("Searching…");
		frappe
			.call({
				method: "earthentrading.api.trade_report_search.search",
				args,
			})
			.then((r) => {
				const rows = (r && r.message) || [];
				renderRows($w, rows);
			})
			.catch(() => {
				$("#et-tr-status", $w).text("Error");
			});
	}

	function clear($w) {
		$("#et-tr-commodity", $w).val("");
		$("#et-tr-origin", $w).val("");
		$("#et-tr-destination", $w).val("");
		$("#et-tr-role", $w).val("");
		apply($w);
	}

	function renderRows($w, rows) {
		const $tb = $("#et-tr-results tbody", $w).empty();
		if (!rows.length) {
			$tb.append(
				'<tr><td colspan="8" class="text-center text-muted" style="padding:24px;">No matching trades.</td></tr>'
			);
			$("#et-tr-status", $w).text("0 trades");
			return;
		}
		const leadHref = (n) => "/app/lead/" + encodeURIComponent(n);
		rows.forEach((r) => {
			$tb.append(`
				<tr>
					<td><a href="${leadHref(r.name)}">${escape_html(r.name)}</a></td>
					<td>${escape_html(r.company_name || "")}</td>
					<td>${escape_html(r.status || "")}</td>
					<td>${escape_html(r.lead_function || "")}</td>
					<td>${escape_html(r.commodity || "")}</td>
					<td>${escape_html(r.origin || "")}</td>
					<td>${escape_html(r.destination || "")}</td>
					<td>${escape_html(r.role || "")}</td>
				</tr>
			`);
		});
		$("#et-tr-status", $w).text(rows.length + " trades");
	}

	function escape_html(s) {
		return (frappe.utils && frappe.utils.escape_html ? frappe.utils.escape_html(s) : String(s))
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;");
	}
	function escape_attr(s) {
		return String(s).replace(/"/g, "&quot;");
	}

	function unmountIfElsewhere() {
		if (isOnEarthCRM()) return;
		$("#" + WIDGET_ID).remove();
	}

	// ----------------------- mount lifecycle -----------------------------
	// Mount on initial app-ready and on every route / page change. Also use a
	// MutationObserver so the widget reappears if the workspace re-renders.
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
				if (isOnEarthCRM()) {
					mountWidget();
				} else {
					unmountIfElsewhere();
				}
			});
			obs.observe(document.body, { childList: true, subtree: true });
		} catch (e) {
			// MutationObserver not available — fine, app_ready handler is enough.
		}
	});
})();

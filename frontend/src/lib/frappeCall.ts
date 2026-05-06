/** Typed JSON calls to `/api/method/...` (session cookie auth). */

function csrf(): string {
	return (typeof window !== 'undefined' && (window as { csrf_token?: string }).csrf_token) || '';
}

export async function frappeMethod<T = unknown>(
	methodPath: string,
	args?: Record<string, unknown>,
): Promise<T> {
	const res = await fetch(`/api/method/${encodeURI(methodPath)}`, {
		method: 'POST',
		credentials: 'include',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			'X-Frappe-CSRF-Token': csrf(),
		},
		body: JSON.stringify(args ?? {}),
	});

	const raw = await res.json().catch(() => ({}));
	if (!res.ok) {
		const msg =
			(typeof raw.exc === 'string' && raw.exc) ||
			(Array.isArray(raw._server_messages) && raw._server_messages[0]) ||
			raw.message ||
			raw.exception ||
			`Request failed (${res.status})`;
		throw new Error(String(msg));
	}
	if (raw.exc) throw new Error(String(raw.exc));

	return raw.message as T;
}

export async function searchLink(doctype: string, txt: string, filters?: Record<string, unknown>) {
	type Row = { value?: string; label?: string; description?: string };
	const rows = await frappeMethod<Row[]>('frappe.desk.search.search_link', {
		doctype,
		txt: txt || '',
		page_length: 20,
		filters: filters || {},
	});
	return rows ?? [];
}

export function bootUserName(): string {
	const u = (window as { frappe?: { boot?: { user?: string | { name?: string } } } }).frappe?.boot?.user;
	if (typeof u === 'string') return u;
	return u?.name ?? '';
}

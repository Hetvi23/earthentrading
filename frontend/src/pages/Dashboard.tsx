import { Link } from 'react-router-dom';

const tiles = [
	{ to: '/leads', title: 'Leads', desc: 'New leads, commodity lines & convert to deals.' },
	{ to: '/opportunities', title: 'Opportunities', desc: 'Deals owners and item lines copied from leads.' },
	{ to: '/quotations', title: 'Quotations', desc: 'Rows open in Desk for rates & taxes.' },
	{ to: '/sales-orders', title: 'Sales orders', desc: 'Fulfillment linkage from Desk.' },
	{ to: '/projects', title: 'Projects', desc: 'Create delivery jobs; attach ET task templates.' },
	{ to: '/tasks', title: 'Tasks', desc: 'Checklists generated from templates on projects.' },
	{ to: '/todos', title: 'My to-dos', desc: 'Assign_to entries from spawned tasks.' },
	{ to: '/task-templates', title: 'ET task templates', desc: 'Reference codes to paste on projects.' },
] as const;

export default function Dashboard() {
	const boot = (window as unknown as { frappe?: { boot?: Record<string, unknown> } }).frappe?.boot;
	const rawUser = boot?.user as string | { full_name?: string; name?: string } | undefined;
	const user =
		rawUser && typeof rawUser !== 'string'
			? rawUser.full_name || rawUser.name
			: (boot?.user_name as string | undefined) || (typeof rawUser === 'string' ? rawUser : undefined);

	return (
		<div>
			<h1 className="text-2xl font-semibold text-zinc-900">Earth Trading operations</h1>
			<p className="mt-2 text-zinc-600">
				Signed in as <span className="font-medium">{user ?? 'User'}</span>. Use the sidebar or tiles below — everything routes through this hub.
			</p>
			<div className="mt-8 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
				{tiles.map((x) => (
					<Link
						key={x.to}
						to={x.to}
						className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-emerald-800/40 hover:shadow-md">
						<h2 className="font-semibold text-zinc-900">{x.title}</h2>
						<p className="mt-2 text-sm text-zinc-500">{x.desc}</p>
					</Link>
				))}
			</div>
			<div className="mt-8 grid gap-3 sm:grid-cols-2">
				<a
					href="/app/earth-trading-hub"
					className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-emerald-800/40">
					<h2 className="font-semibold text-zinc-900">Desk · Earth Trading Hub</h2>
					<p className="mt-2 text-sm text-zinc-500">Workspace shortcuts & quick lists.</p>
				</a>
				<a
					href="/app"
					className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-emerald-800/40">
					<h2 className="font-semibold text-zinc-900">Full ERPNext desk</h2>
					<p className="mt-2 text-sm text-zinc-500">Stock, accounting, and deep forms.</p>
				</a>
			</div>
			<p className="mt-8 text-center text-xs text-zinc-500">
				Public intake ·{' '}
				<a href="/earth-trading-lead" className="text-emerald-900 underline">
					Web lead form
				</a>
			</p>
		</div>
	);
}

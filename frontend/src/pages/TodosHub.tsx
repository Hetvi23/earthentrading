import { bootUserName } from '@/lib/boot';
import { useFrappeGetDocList } from 'frappe-react-sdk';

type Row = { name?: string; description?: string; status?: string; date?: string; reference_type?: string; reference_name?: string };

export default function TodosHub() {
	const me = bootUserName();
	const { data, error, isLoading } = useFrappeGetDocList<Row>('ToDo', {
		fields: ['name', 'description', 'status', 'date', 'reference_type', 'reference_name'],
		filters: me
			? [
					['allocated_to', '=', me],
					['status', '!=', 'Closed'],
				]
			: [['name', '=', '__et_hub_no_user__']],
		orderBy: { field: 'date', order: 'asc' },
		limit: 200,
	});

	if (!me) {
		return <p className="text-red-700">Missing session user — reload after login.</p>;
	}

	if (isLoading) return <p className="text-zinc-500">Loading to-dos…</p>;
	if (error) {
		return <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm">Could not load ToDos.</div>;
	}

	return (
		<div>
			<h1 className="text-2xl font-semibold text-zinc-900">My to-dos</h1>
			<p className="mt-1 text-sm text-zinc-500">Assigned to {me}. Linked to tasks spawned from checklist templates.</p>
			<div className="mt-6 overflow-x-auto rounded-lg border border-zinc-200 bg-white shadow-sm">
				<table className="w-full text-left text-sm">
					<thead className="border-b bg-zinc-50">
						<tr>
							<th className="px-4 py-3 font-medium">Description</th>
							<th className="px-4 py-3 font-medium">Status</th>
							<th className="whitespace-nowrap px-4 py-3 font-medium">Due</th>
							<th className="px-4 py-3 font-medium">Reference</th>
						</tr>
					</thead>
					<tbody>
						{(data ?? []).length === 0 ? (
							<tr>
								<td colSpan={4} className="px-4 py-10 text-center text-zinc-500">
									No open to-dos. When checklist tasks spawn, assign_to creates entries here automatically.
								</td>
							</tr>
						) : (
							(data ?? []).map((row, i) => (
								<tr key={row.name ?? i} className="border-t hover:bg-zinc-50">
									<td className="px-4 py-3">
										<a
											href={row.name ? `/app/todo/${encodeURIComponent(row.name)}` : '#'}
											className="text-emerald-900 hover:underline">
											{row.description ?? row.name ?? '—'}
										</a>
									</td>
									<td className="text-zinc-600">{row.status ?? '—'}</td>
									<td className="text-zinc-600">{row.date ?? '—'}</td>
									<td className="text-xs text-zinc-500">
										{row.reference_type ? `${row.reference_type}: ${row.reference_name ?? ''}` : '—'}
									</td>
								</tr>
							))
						)}
					</tbody>
				</table>
			</div>
		</div>
	);
}

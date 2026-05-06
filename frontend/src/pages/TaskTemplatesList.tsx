import { useFrappeGetDocList } from 'frappe-react-sdk';

type Row = { name?: string; title?: string; modified?: string };

export default function TaskTemplatesList() {
	const { data, error, isLoading } = useFrappeGetDocList<Row>('ET Task Template', {
		fields: ['name', 'title', 'modified'],
		orderBy: { field: 'modified', order: 'desc' },
		limit: 100,
	});

	if (isLoading) return <p className="text-zinc-500">Loading templates…</p>;
	if (error) {
		return (
			<div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm">
				Cannot read ET Task Template — edit templates on Desk or grant read permission on this DocType.
			</div>
		);
	}

	return (
		<div>
			<h1 className="text-2xl font-semibold text-zinc-900">ET task templates</h1>
			<p className="mt-1 text-sm text-zinc-500">
				Use these names on Project → <b>ET Task Template</b>. Maintain template lines & assignees as usual on Desk.
			</p>
			<ul className="mt-6 divide-y rounded-lg border border-zinc-200 bg-white shadow-sm">
				{(data ?? []).length === 0 ? (
					<li className="px-4 py-8 text-center text-zinc-500">No templates — create under Earth Ent Trading module on Desk.</li>
				) : (
					(data ?? []).map((row) => (
						<li key={row.name} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 hover:bg-zinc-50">
							<span className="font-medium text-zinc-900">{row.title || row.name}</span>
							<div className="flex gap-3 text-xs text-zinc-500">
								<code className="rounded bg-zinc-100 px-1.5">{row.name}</code>
								{row.modified ? new Date(row.modified).toLocaleDateString() : null}
								<a
									href={`/app/et-task-template/${encodeURIComponent(row.name ?? '')}`}
									className="text-emerald-900 underline">
									Desk
								</a>
							</div>
						</li>
					))
				)}
			</ul>
		</div>
	);
}

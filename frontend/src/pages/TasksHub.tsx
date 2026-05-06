import { Link } from 'react-router-dom';
import { useFrappeGetDocList } from 'frappe-react-sdk';

type Row = {
	name?: string;
	subject?: string;
	project?: string;
	status?: string;
	priority?: string;
	_owner?: string;
	modified?: string;
};

export default function TasksHub() {
	const { data, error, isLoading } = useFrappeGetDocList<Row>('Task', {
		fields: ['name', 'subject', 'project', 'status', 'priority', 'modified'],
		orderBy: { field: 'modified', order: 'desc' },
		limit: 250,
	});

	if (isLoading) return <p className="text-zinc-500">Loading tasks…</p>;
	if (error) {
		return (
			<div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm">
				Could not load tasks — ensure your role can read Task.
			</div>
		);
	}

	return (
		<div>
			<h1 className="text-2xl font-semibold text-zinc-900">Tasks</h1>
			<p className="mt-1 text-sm text-zinc-500">
				Checklist tasks from ET templates appear once the project checklist has run on the backend.
			</p>
			<div className="mt-6 overflow-x-auto rounded-lg border border-zinc-200 bg-white shadow-sm">
				<table className="w-full text-left text-sm">
					<thead className="border-b bg-zinc-50">
						<tr>
							<th className="px-4 py-3 font-medium">Subject</th>
							<th className="px-4 py-3 font-medium">Project</th>
							<th className="px-4 py-3 font-medium">Status</th>
							<th className="px-4 py-3 font-medium">Priority</th>
							<th className="whitespace-nowrap px-4 py-3 font-medium">Modified</th>
						</tr>
					</thead>
					<tbody>
						{(data ?? []).length === 0 ? (
							<tr>
								<td colSpan={5} className="px-4 py-10 text-center text-zinc-500">
									No tasks — open{' '}
									<Link className="font-medium text-emerald-900 underline" to="/projects">
										Projects
									</Link>
									, create one, set template & company, save; hooks create tasks once per project.
								</td>
							</tr>
						) : (
							(data ?? []).map((row, i) => (
								<tr key={row.name ?? i} className="border-t hover:bg-zinc-50">
									<td className="px-4 py-3">
										<a
											href={`/app/task/${encodeURIComponent(row.name ?? '')}`}
											className="font-medium text-emerald-900 hover:underline">
											{row.subject || row.name}
										</a>
									</td>
									<td className="text-zinc-600">
										{row.project ? (
											<Link to={`/projects/${encodeURIComponent(row.project)}`} className="hover:underline text-emerald-900">
												{row.project}
											</Link>
										) : (
											'—'
										)}
									</td>
									<td className="text-zinc-600">{row.status ?? '—'}</td>
									<td className="text-zinc-600">{row.priority ?? '—'}</td>
									<td className="text-zinc-500">
										{row.modified ? new Date(row.modified).toLocaleString() : '—'}
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

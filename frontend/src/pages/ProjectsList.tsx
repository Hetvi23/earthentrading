import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useFrappeGetDocList } from 'frappe-react-sdk';
import { Plus } from 'lucide-react';
import { frappeMethod } from '@/lib/frappeCall';
import { bootUserName } from '@/lib/boot';

type Row = { name: string; project_name?: string; status?: string; expected_end_date?: string };
type Co = { name: string };

export default function ProjectsList() {
	const navigate = useNavigate();
	const [open, setOpen] = useState(false);
	const [creating, setCreating] = useState(false);
	const [err, setErr] = useState<string | null>(null);
	const [form, setForm] = useState({
		project_name: '',
		company: '',
		customer: '',
		expected_start_date: '',
		expected_end_date: '',
		template: '',
	});

	const { data: companies } = useFrappeGetDocList<Co>('Company', {
		fields: ['name'],
		limit: 200,
		orderBy: { field: 'name', order: 'asc' },
	});

	const { data, error, isLoading, mutate } = useFrappeGetDocList<Row>('Project', {
		fields: ['name', 'project_name', 'status', 'expected_end_date'],
		orderBy: { field: 'modified', order: 'desc' },
		limit: 250,
	});

	const openModal = () => {
		setErr(null);
		const first = companies?.[0]?.name ?? '';
		setForm((f) => ({ ...f, company: f.company || first }));
		setOpen(true);
	};

	const createProject = async () => {
		if (!form.project_name.trim()) {
			setErr('Project name is required.');
			return;
		}
		if (!form.company) {
			setErr('Select a company.');
			return;
		}
		setCreating(true);
		setErr(null);
		try {
			const doc: Record<string, unknown> = {
				doctype: 'Project',
				naming_series: 'PROJ-.####',
				project_name: form.project_name.trim(),
				company: form.company,
				status: 'Open',
			};
			if (form.customer.trim()) doc.customer = form.customer.trim();
			if (form.expected_start_date) doc.expected_start_date = form.expected_start_date;
			if (form.expected_end_date) doc.expected_end_date = form.expected_end_date;
			if (form.template.trim()) doc.custom_et_task_template = form.template.trim();

			const created = await frappeMethod<{ name?: string }>('frappe.client.insert', { doc });
			const id = created?.name;
			if (!id) throw new Error('Insert failed — no document name returned.');
			setOpen(false);
			setForm({
				project_name: '',
				company: companies?.[0]?.name ?? '',
				customer: '',
				expected_start_date: '',
				expected_end_date: '',
				template: '',
			});
			await mutate?.();
			void navigate(`/projects/${encodeURIComponent(id)}`);
		} catch (e: unknown) {
			setErr(e instanceof Error ? e.message : String(e));
		} finally {
			setCreating(false);
		}
	};

	if (isLoading) return <p className="text-zinc-500">Loading projects…</p>;
	if (error) {
		return (
			<div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm">
				Could not load projects — verify your profile can read “Project”.
			</div>
		);
	}

	return (
		<div>
			<div className="flex flex-wrap items-start justify-between gap-4">
				<div>
					<h1 className="text-2xl font-semibold text-zinc-900">Projects</h1>
					<p className="mt-1 max-w-xl text-sm text-zinc-500">
						Start delivery jobs here: pick company, optionally link an ET task template. Saving the template on the project
						triggers checklist tasks server-side ({bootUserName() || 'logged-in user'} must have Desk access to ERPNext Projects).
					</p>
				</div>
				<button
					type="button"
					onClick={openModal}
					className="inline-flex shrink-0 items-center gap-1.5 rounded-md bg-emerald-900 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-800">
					<Plus className="h-4 w-4" />
					New project
				</button>
			</div>

			{open ? (
				<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
					<div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
						<h2 className="text-lg font-semibold text-zinc-900">New project</h2>
						<p className="mt-1 text-xs text-zinc-500">Required: name + company (ERPNext rules).</p>
						<div className="mt-4 space-y-3">
							<label className="block">
								<span className="text-xs font-medium text-zinc-600">Project name</span>
								<input
									className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
									value={form.project_name}
									onChange={(e) => setForm((f) => ({ ...f, project_name: e.target.value }))}
								/>
							</label>
							<label className="block">
								<span className="text-xs font-medium text-zinc-600">Company</span>
								<select
									className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
									value={form.company}
									onChange={(e) => setForm((f) => ({ ...f, company: e.target.value }))}>
									<option value="">Select…</option>
									{(companies ?? []).map((c) => (
										<option key={c.name} value={c.name}>
											{c.name}
										</option>
									))}
								</select>
							</label>
							<label className="block">
								<span className="text-xs font-medium text-zinc-600">Customer (optional link)</span>
								<input
									className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
									placeholder="Customer name as in ERPNext"
									value={form.customer}
									onChange={(e) => setForm((f) => ({ ...f, customer: e.target.value }))}
								/>
							</label>
							<label className="block">
								<span className="text-xs font-medium text-zinc-600">ET task template (optional)</span>
								<input
									className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
									placeholder="Template code / name"
									value={form.template}
									onChange={(e) => setForm((f) => ({ ...f, template: e.target.value }))}
								/>
							</label>
							<div className="grid grid-cols-2 gap-2">
								<label className="block">
									<span className="text-xs font-medium text-zinc-600">Start</span>
									<input
										type="date"
										className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
										value={form.expected_start_date}
										onChange={(e) => setForm((f) => ({ ...f, expected_start_date: e.target.value }))}
									/>
								</label>
								<label className="block">
									<span className="text-xs font-medium text-zinc-600">Expected end</span>
									<input
										type="date"
										className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
										value={form.expected_end_date}
										onChange={(e) => setForm((f) => ({ ...f, expected_end_date: e.target.value }))}
									/>
								</label>
							</div>
						</div>
						{err ? <p className="mt-3 text-sm text-red-600">{err}</p> : null}
						<div className="mt-6 flex justify-end gap-2">
							<button type="button" className="rounded-md px-3 py-1.5 text-sm text-zinc-600" onClick={() => setOpen(false)}>
								Cancel
							</button>
							<button
								type="button"
								disabled={creating}
								onClick={() => void createProject()}
								className="rounded-md bg-emerald-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50">
								{creating ? 'Creating…' : 'Create'}
							</button>
						</div>
					</div>
				</div>
			) : null}

			<div className="mt-6 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
				<table className="w-full text-left text-sm">
					<thead className="border-b bg-zinc-50">
						<tr>
							<th className="px-4 py-3 font-medium">Project</th>
							<th className="px-4 py-3 font-medium">Status</th>
							<th className="px-4 py-3 font-medium">Expected end</th>
						</tr>
					</thead>
					<tbody>
						{(data ?? []).length === 0 ? (
							<tr>
								<td colSpan={3} className="px-4 py-10 text-center text-zinc-500">
									No projects yet — use <b>New project</b> above. If you expect data, confirm your user has read access to
									Project and that records exist in ERPNext.
								</td>
							</tr>
						) : (
							(data ?? []).map((row) => (
								<tr key={row.name} className="border-t hover:bg-zinc-50">
									<td className="px-4 py-3">
										<Link className="font-medium text-emerald-900 hover:underline" to={`/projects/${encodeURIComponent(row.name)}`}>
											{row.project_name || row.name}
										</Link>
									</td>
									<td className="text-zinc-600">{row.status ?? '—'}</td>
									<td className="text-zinc-600">{row.expected_end_date ?? '—'}</td>
								</tr>
							))
						)}
					</tbody>
				</table>
			</div>
		</div>
	);
}

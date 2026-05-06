import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useFrappeGetDoc, useFrappeGetDocList } from 'frappe-react-sdk';
import { frappeMethod } from '@/lib/frappeCall';

type TaskRow = { name?: string; subject?: string; status?: string; progress?: number; priority?: string };

type Proj = Record<string, unknown>;

const STATUSES = ['Open', 'Completed', 'Cancelled'] as const;

export default function ProjectDetail() {
	const { name } = useParams<{ name: string }>();
	const { data: project, error, isLoading, mutate } = useFrappeGetDoc<Proj>('Project', name);
	const [draft, setDraft] = useState<Proj | null>(null);
	const draftRef = useRef<Proj | null>(null);
	const [saving, setSaving] = useState(false);
	const [banner, setBanner] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

	useEffect(() => {
		if (project) {
			setDraft(structuredClone(project));
		}
	}, [project]);

	useEffect(() => {
		draftRef.current = draft;
	}, [draft]);

	const tasks = useFrappeGetDocList<TaskRow>('Task', {
		fields: ['name', 'subject', 'status', 'progress', 'priority'],
		filters: name ? [['project', '=', name]] : [['name', '=', '__no_project__']],
		limit: 200,
		orderBy: { field: 'creation', order: 'desc' },
	});

	const save = async () => {
		const snap = draftRef.current;
		if (!snap?.name) return;
		setSaving(true);
		setBanner(null);
		try {
			const payload = structuredClone(snap) as Proj;
			payload.doctype = 'Project';
			await frappeMethod('frappe.client.save', { doc: payload });
			await mutate?.();
			setBanner({ type: 'ok', text: 'Project saved. If checklist not spawned yet and template changed, ERPNext hooks will run.' });
		} catch (e: unknown) {
			setBanner({ type: 'err', text: e instanceof Error ? e.message : String(e) });
		} finally {
			setSaving(false);
		}
	};

	if (!name) return <p className="text-red-600">Missing project.</p>;
	if (isLoading) return <p className="text-zinc-500">Loading…</p>;
	if (error || !draft) {
		return (
			<div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm">
				Not found.{' '}
				<Link to="/projects" className="underline">
					Back
				</Link>
			</div>
		);
	}

	const tpl = String(draft.custom_et_task_template || '');
	const spawned = Boolean(draft.custom_et_checklist_spawned);

	return (
		<div className="mx-auto max-w-4xl">
			<Link to="/projects" className="text-sm text-zinc-600 hover:text-zinc-900">
				← Projects
			</Link>
			<h1 className="mt-2 text-2xl font-semibold text-zinc-900">{String(draft.project_name || draft.name)}</h1>

			{banner ? (
				<div
					className={`mt-4 rounded-md border px-3 py-2 text-sm ${
						banner.type === 'ok'
							? 'border-emerald-200 bg-emerald-50 text-emerald-900'
							: 'border-red-200 bg-red-50 text-red-800'
					}`}>
					{banner.text}
				</div>
			) : null}

			<div className="mt-6 flex flex-wrap gap-2 text-sm">
				<span className="rounded-full bg-emerald-50 px-3 py-1 text-emerald-900">Template: {tpl || '(none)'}</span>
				<span className="rounded-full bg-zinc-100 px-3 py-1">Checklist spawned: {spawned ? 'Yes' : 'No'}</span>
				<span className="rounded-full bg-zinc-100 px-3 py-1">Company: {String(draft.company ?? '—')}</span>
			</div>

			<div className="mt-6 space-y-4 rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
				<div className="grid gap-4 sm:grid-cols-2">
					<label className="block sm:col-span-2">
						<span className="text-xs font-medium text-zinc-600">ERP ID</span>
						<input className="mt-1 w-full rounded border border-zinc-200 bg-zinc-50 px-2 py-1.5 text-sm" readOnly value={String(draft.name)} />
					</label>
					<label className="block">
						<span className="text-xs font-medium text-zinc-600">Project name</span>
						<input
							className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={String(draft.project_name ?? '')}
							onChange={(e) => setDraft({ ...draft, project_name: e.target.value })}
						/>
					</label>
					<label className="block">
						<span className="text-xs font-medium text-zinc-600">Status</span>
						<select
							className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={String(draft.status ?? 'Open')}
							onChange={(e) => setDraft({ ...draft, status: e.target.value })}>
							{STATUSES.map((s) => (
								<option key={s} value={s}>
									{s}
								</option>
							))}
						</select>
					</label>
					<label className="block">
						<span className="text-xs font-medium text-zinc-600">Customer</span>
						<input
							className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={String(draft.customer ?? '')}
							onChange={(e) => setDraft({ ...draft, customer: e.target.value })}
							placeholder="Customer name"
						/>
					</label>
					<label className="block">
						<span className="text-xs font-medium text-zinc-600">Sales order (read-only shortcut)</span>
						<input
							className="mt-1 w-full rounded border border-zinc-200 bg-zinc-50 px-2 py-1.5 text-sm"
							readOnly
							value={String(draft.sales_order ?? '')}
						/>
					</label>
					<label className="block">
						<span className="text-xs font-medium text-zinc-600">Expected start</span>
						<input
							type="date"
							className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={(draft.expected_start_date as string) || ''}
							onChange={(e) => setDraft({ ...draft, expected_start_date: e.target.value })}
						/>
					</label>
					<label className="block">
						<span className="text-xs font-medium text-zinc-600">Expected end</span>
						<input
							type="date"
							className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={(draft.expected_end_date as string) || ''}
							onChange={(e) => setDraft({ ...draft, expected_end_date: e.target.value })}
						/>
					</label>
					<label className="block sm:col-span-2">
						<span className="text-xs font-medium text-zinc-600">ET task template</span>
						<input
							className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={tpl}
							onChange={(e) => setDraft({ ...draft, custom_et_task_template: e.target.value })}
							placeholder="Template code matching ET Task Template"
						/>
					</label>
					<label className="block sm:col-span-2">
						<span className="text-xs font-medium text-zinc-600">Notes</span>
						<textarea
							className="mt-1 min-h-[96px] w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={String(draft.notes ?? '')}
							onChange={(e) => setDraft({ ...draft, notes: e.target.value })}
						/>
					</label>
				</div>

				<p className="text-xs text-zinc-500">
					Add/remove <b>Project users</b> on Desk for assignee lists on spawned tasks.
				</p>

				<div className="flex flex-wrap gap-2 border-t border-zinc-100 pt-4">
					<button
						type="button"
						disabled={saving}
						onClick={() => void save()}
						className="rounded-md bg-emerald-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
						{saving ? 'Saving…' : 'Save project'}
					</button>
					<a
						href={`/app/project/${encodeURIComponent(name)}`}
						target="_blank"
						rel="noreferrer"
						className="px-3 py-2 text-sm text-emerald-900 underline">
						Desk form →
					</a>
				</div>
			</div>

			<h2 className="mt-10 text-lg font-semibold text-zinc-900">Tasks</h2>
			<div className="mt-3 overflow-hidden rounded-lg border bg-white shadow-sm">
				<table className="w-full text-left text-sm">
					<thead className="border-b bg-zinc-50">
						<tr>
							<th className="px-4 py-2 font-medium">Subject</th>
							<th className="px-4 py-2 font-medium">Status</th>
							<th className="px-4 py-2 font-medium">Priority</th>
						</tr>
					</thead>
					<tbody>
						{tasks.isLoading ? (
							<tr>
								<td colSpan={3} className="px-4 py-4 text-center text-zinc-500">
									Loading tasks…
								</td>
							</tr>
						) : (tasks.data ?? []).length === 0 ? (
							<tr>
								<td colSpan={3} className="px-4 py-6 text-center text-zinc-500">
									No tasks — set template above, assign company & project users, save; hooks create tasks once per project.
								</td>
							</tr>
						) : (
							(tasks.data ?? []).map((t, i) => (
								<tr key={t.name ?? i} className="border-t hover:bg-zinc-50">
									<td className="px-4 py-2">
										<a
											className="text-emerald-900 hover:underline"
											href={`/app/task/${encodeURIComponent(t.name ?? '')}`}
											target="_blank"
											rel="noreferrer">
											{t.subject || t.name || 'Task'}
										</a>
									</td>
									<td className="text-zinc-600">{t.status ?? '—'}</td>
									<td className="text-zinc-600">{t.priority ?? '—'}</td>
								</tr>
							))
						)}
					</tbody>
				</table>
			</div>
		</div>
	);
}

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useFrappeGetDocList } from 'frappe-react-sdk';
import { Plus } from 'lucide-react';
import { frappeMethod } from '@/lib/frappeCall';
import { bootUserName } from '@/lib/boot';

type LeadRow = {
	name: string;
	lead_name?: string;
	company_name?: string;
	status?: string;
	creation?: string;
};

export default function Leads() {
	const navigate = useNavigate();
	const [open, setOpen] = useState(false);
	const [creating, setCreating] = useState(false);
	const [formErr, setFormErr] = useState<string | null>(null);
	const [form, setForm] = useState({ kind: 'company' as 'person' | 'company', first_name: '', company_name: '' });

	const { data, error, isLoading, mutate } = useFrappeGetDocList<LeadRow>('Lead', {
		fields: ['name', 'lead_name', 'company_name', 'status', 'creation'],
		orderBy: { field: 'modified', order: 'desc' },
		limit: 150,
	});

	const createLead = async () => {
		if (form.kind === 'person' && !form.first_name.trim()) {
			setFormErr('Enter a first name.');
			return;
		}
		if (form.kind === 'company' && !form.company_name.trim()) {
			setFormErr('Enter an organization name.');
			return;
		}
		setCreating(true);
		setFormErr(null);
		const owner = bootUserName();
		try {
			const doc: Record<string, unknown> = {
				doctype: 'Lead',
				naming_series: 'CRM-LEAD-.YYYY.-',
				status: 'Lead',
			};
			if (owner) doc.lead_owner = owner;
			if (form.kind === 'person') {
				doc.first_name = form.first_name.trim();
			} else {
				doc.company_name = form.company_name.trim();
			}
			const created = await frappeMethod<{ name?: string }>('frappe.client.insert', { doc });
			const id = created?.name;
			if (!id) throw new Error('Lead insert did not return name.');
			setOpen(false);
			setForm({ kind: 'company', first_name: '', company_name: '' });
			await mutate?.();
			void navigate(`/leads/${encodeURIComponent(id)}`);
		} catch (e: unknown) {
			setFormErr(e instanceof Error ? e.message : String(e));
		} finally {
			setCreating(false);
		}
	};

	if (isLoading) {
		return <p className="text-zinc-500">Loading leads…</p>;
	}
	if (error) {
		const errObj = error as unknown as Error & { httpStatus?: number; exception?: string };
		const msg =
			errObj.httpStatus === 403
				? 'You do not have permission to read Leads.'
				: (errObj.exception ?? errObj.message ?? 'Failed to load leads');
		return (
			<div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
				{msg}
			</div>
		);
	}

	return (
		<div>
			<div className="mb-6 flex flex-wrap items-end justify-between gap-4">
				<div>
					<h1 className="text-2xl font-semibold text-zinc-900">Leads</h1>
					<p className="text-sm text-zinc-500">Manual capture plus web form · max 150 on this screen</p>
				</div>
				<div className="flex flex-wrap gap-2">
					<Link
						to="/dashboard"
						className="rounded-md border border-emerald-900 px-4 py-2 text-sm font-medium text-emerald-900 hover:bg-emerald-50">
						CRM home
					</Link>
					<button
						type="button"
						onClick={() => {
							setFormErr(null);
							setOpen(true);
						}}
						className="inline-flex items-center gap-1.5 rounded-md bg-emerald-900 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-800">
						<Plus className="h-4 w-4" />
						New lead
					</button>
				</div>
			</div>

			{open ? (
				<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
					<div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
						<h2 className="text-lg font-semibold text-zinc-900">New lead</h2>
						<div className="mt-4 flex gap-3 text-sm">
							<label className="flex items-center gap-2">
								<input
									type="radio"
									name="leadkind"
									checked={form.kind === 'company'}
									onChange={() => setForm((f) => ({ ...f, kind: 'company' }))}
								/>
								Organization
							</label>
							<label className="flex items-center gap-2">
								<input
									type="radio"
									name="leadkind"
									checked={form.kind === 'person'}
									onChange={() => setForm((f) => ({ ...f, kind: 'person' }))}
								/>
								Person
							</label>
						</div>
						<div className="mt-4 space-y-3">
							{form.kind === 'person' ? (
								<label className="block">
									<span className="text-xs font-medium text-zinc-600">First name</span>
									<input
										className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
										value={form.first_name}
										onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
									/>
								</label>
							) : (
								<label className="block">
									<span className="text-xs font-medium text-zinc-600">Company / lead title</span>
									<input
										className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
										value={form.company_name}
										onChange={(e) => setForm((f) => ({ ...f, company_name: e.target.value }))}
									/>
								</label>
							)}
						</div>
						{formErr ? <p className="mt-3 text-sm text-red-600">{formErr}</p> : null}
						<div className="mt-6 flex justify-end gap-2">
							<button type="button" className="rounded-md px-3 py-1.5 text-sm text-zinc-600" onClick={() => setOpen(false)}>
								Cancel
							</button>
							<button
								type="button"
								disabled={creating}
								onClick={() => void createLead()}
								className="rounded-md bg-emerald-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50">
								{creating ? 'Creating…' : 'Create & edit'}
							</button>
						</div>
					</div>
				</div>
			) : null}

			<div className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
				<table className="w-full text-left text-sm">
					<thead className="border-b border-zinc-200 bg-zinc-50">
						<tr>
							<th className="px-4 py-3 font-medium text-zinc-700">Name</th>
							<th className="px-4 py-3 font-medium text-zinc-700">Organization</th>
							<th className="px-4 py-3 font-medium text-zinc-700">Status</th>
							<th className="px-4 py-3 font-medium text-zinc-700">Created</th>
						</tr>
					</thead>
					<tbody>
						{(data ?? []).length === 0 ? (
							<tr>
								<td colSpan={4} className="px-4 py-8 text-center text-zinc-500">
									No leads in your view — ET Traders see only their owned leads unless you widen permissions.
								</td>
							</tr>
						) : (
							(data ?? []).map((row) => (
								<tr key={row.name} className="border-t border-zinc-100 hover:bg-zinc-50">
									<td className="px-4 py-3">
										<Link to={`/leads/${encodeURIComponent(row.name)}`} className="font-medium text-emerald-900 hover:underline">
											{row.lead_name || row.name}
										</Link>
									</td>
									<td className="px-4 py-3 text-zinc-600">{row.company_name ?? '—'}</td>
									<td className="px-4 py-3 text-zinc-600">{row.status ?? '—'}</td>
									<td className="px-4 py-3 text-zinc-500">
										{row.creation ? new Date(row.creation).toLocaleString() : '—'}
									</td>
								</tr>
							))
						)}
					</tbody>
				</table>
			</div>

			<p className="mt-4 text-center text-xs text-zinc-500">
				Intake ·{' '}
				<a href="/earth-trading-lead" className="text-emerald-900 underline">
					Public web form
				</a>
			</p>
		</div>
	);
}

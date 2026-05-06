import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useFrappeGetDoc } from 'frappe-react-sdk';
import type { OpportunityDoc } from '@/types/earthTrading';
import { frappeMethod } from '@/lib/frappeCall';

const DEAL_TYPES = ['', 'Brokerage', 'Principal'] as const;

export default function OpportunityDetail() {
	const { name } = useParams<{ name: string }>();
	const { data, error, isLoading, mutate } = useFrappeGetDoc<OpportunityDoc>('Opportunity', name);
	const [draft, setDraft] = useState<OpportunityDoc | null>(null);
	const [saving, setSaving] = useState(false);
	const [banner, setBanner] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
	const draftRef = useRef<OpportunityDoc | null>(null);

	useEffect(() => {
		if (data) setDraft(structuredClone(data));
	}, [data]);

	useEffect(() => {
		draftRef.current = draft;
	}, [draft]);

	const save = async () => {
		const snap = draftRef.current;
		if (!snap?.name) return;
		setSaving(true);
		setBanner(null);
		try {
			const payload = structuredClone(snap) as OpportunityDoc & Record<string, unknown>;
			payload.doctype = 'Opportunity';
			await frappeMethod('frappe.client.save', { doc: payload });
			await mutate?.();
			setBanner({ type: 'ok', text: 'Opportunity saved.' });
		} catch (e: unknown) {
			setBanner({ type: 'err', text: e instanceof Error ? e.message : String(e) });
		} finally {
			setSaving(false);
		}
	};

	if (!name) return <p className="text-red-600">Missing name.</p>;
	if (isLoading) return <p className="text-zinc-500">Loading…</p>;
	if (error || !draft) {
		return (
			<div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm">
				Not found. <Link to="/opportunities" className="underline">Back</Link>
			</div>
		);
	}

	const items = draft.items ?? [];

	return (
		<div className="mx-auto max-w-4xl">
			<Link to="/opportunities" className="text-sm text-zinc-600 hover:text-zinc-900">
				← Opportunities
			</Link>
			<h1 className="mt-2 text-2xl font-semibold text-zinc-900">{draft.title || draft.name}</h1>
			<p className="text-sm text-zinc-500">From lead: {draft.party_name ?? '—'}</p>

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

			<div className="mt-6 space-y-4 rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
				<div className="grid gap-4 sm:grid-cols-2">
					<label className="block">
						<span className="mb-1 block text-xs font-medium text-zinc-600">Customer</span>
						<input
							className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={draft.customer_name ?? ''}
							readOnly
						/>
					</label>
					<label className="block">
						<span className="mb-1 block text-xs font-medium text-zinc-600">Status</span>
						<input
							className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={draft.status ?? ''}
							onChange={(e) => setDraft({ ...draft, status: e.target.value })}
						/>
					</label>
					<label className="block">
						<span className="mb-1 block text-xs font-medium text-zinc-600">Opportunity owner</span>
						<input
							className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={draft.opportunity_owner ?? ''}
							onChange={(e) => setDraft({ ...draft, opportunity_owner: e.target.value })}
						/>
					</label>
					<label className="block">
						<span className="mb-1 block text-xs font-medium text-zinc-600">Assigned trader</span>
						<input
							className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={draft.custom_et_assigned_trader ?? ''}
							onChange={(e) => setDraft({ ...draft, custom_et_assigned_trader: e.target.value })}
						/>
					</label>
					<label className="block sm:col-span-2">
						<span className="mb-1 block text-xs font-medium text-zinc-600">Deal type</span>
						<select
							className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
							value={draft.custom_et_deal_type ?? ''}
							onChange={(e) =>
								setDraft({ ...draft, custom_et_deal_type: e.target.value as OpportunityDoc['custom_et_deal_type'] })
							}>
							{DEAL_TYPES.map((d) => (
								<option key={d || 'x'} value={d}>
									{d || '(not set)'}
								</option>
							))}
						</select>
					</label>
				</div>

				<div>
					<h3 className="mb-2 text-sm font-semibold text-zinc-800">Products (carried from lead lines)</h3>
					<div className="overflow-auto rounded border">
						<table className="w-full text-sm">
							<thead className="bg-zinc-50">
								<tr>
									<th className="px-3 py-2 text-left">Item</th>
									<th className="px-3 py-2 text-right">Qty</th>
									<th className="px-3 py-2 text-left">UOM</th>
									<th className="px-3 py-2 text-left">Description</th>
								</tr>
							</thead>
							<tbody>
								{items.length === 0 ? (
									<tr>
										<td colSpan={4} className="px-3 py-4 text-center text-zinc-500">
											No items on this opportunity.
										</td>
									</tr>
								) : (
									items.map((row, i) => (
										<tr key={i} className="border-t">
											<td className="px-3 py-2">
												{String((row as { item_code?: string }).item_code || (row as { item_name?: string }).item_name || '—')}
											</td>
											<td className="px-3 py-2 text-right">{String((row as { qty?: number }).qty ?? '')}</td>
											<td className="px-3 py-2">{String((row as { uom?: string }).uom ?? '')}</td>
											<td className="px-3 py-2 text-zinc-600">
												{String((row as { description?: string }).description ?? '')}
											</td>
										</tr>
									))
								)}
							</tbody>
						</table>
					</div>
					<p className="mt-2 text-xs text-zinc-500">Edit item grid in Desk for full pricing & delivery.</p>
				</div>

				<div className="flex gap-3 border-t pt-4">
					<button
						type="button"
						disabled={saving}
						onClick={() => void save()}
						className="rounded-md bg-emerald-900 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50">
						{saving ? 'Saving…' : 'Save'}
					</button>
					<a
						href={`/app/opportunity/${encodeURIComponent(draft.name!)}`}
						target="_blank"
						rel="noreferrer"
						className="text-sm text-zinc-600 underline">
						Open in Desk →
					</a>
				</div>
			</div>
		</div>
	);
}

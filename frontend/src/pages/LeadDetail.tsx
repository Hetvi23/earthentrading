import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useFrappeGetDoc } from 'frappe-react-sdk';
import { ArrowLeft, Plus, Trash2 } from 'lucide-react';
import type { EtLeadLine, LeadDoc } from '@/types/earthTrading';
import { frappeMethod, searchLink } from '@/lib/frappeCall';

const SALES_STAGES = ['Lead', 'Qualified', 'Negotiation', 'Won', 'Lost'] as const;
const DEAL_TYPES = ['', 'Brokerage', 'Principal'] as const;

function normalizeLeadLines(parentName: string, rows: EtLeadLine[]): EtLeadLine[] {
	return rows.map((row, i) => ({
		...row,
		idx: i + 1,
		parent: parentName,
		parentfield: 'custom_et_lines',
		parenttype: 'Lead',
		doctype: 'ET Lead Line',
	}));
}

export default function LeadDetail() {
	const { name } = useParams<{ name: string }>();
	const navigate = useNavigate();
	const { data: lead, error, isLoading, mutate } = useFrappeGetDoc<LeadDoc>('Lead', name);
	const [draft, setDraft] = useState<LeadDoc | null>(null);
	const [saving, setSaving] = useState(false);
	const [oppBusy, setOppBusy] = useState(false);
	const [banner, setBanner] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
	const draftRef = useRef<LeadDoc | null>(null);

	useEffect(() => {
		if (lead && name) {
			const copy = structuredClone(lead) as LeadDoc;
			copy.custom_et_lines = copy.custom_et_lines?.length ? copy.custom_et_lines : [];
			setDraft(copy);
		}
	}, [lead, name]);

	useEffect(() => {
		draftRef.current = draft;
	}, [draft]);

	const setField = useCallback(<K extends keyof LeadDoc>(k: K, v: LeadDoc[K]) => {
		setDraft((d) => (d ? { ...d, [k]: v } : d));
	}, []);

	const updateLineCells = useCallback((rowIndex: number, patch: Partial<EtLeadLine>) => {
		setDraft((d) => {
			if (!d?.name) return d;
			const rows = [...(d.custom_et_lines ?? [])];
			rows[rowIndex] = { ...rows[rowIndex], ...patch };
			return { ...d, custom_et_lines: normalizeLeadLines(d.name, rows) };
		});
	}, []);

	const addLine = () => {
		setDraft((d) => {
			if (!d?.name) return d;
			const lines = [...(d.custom_et_lines ?? []), { doctype: 'ET Lead Line', qty: 1, commodity: '' }];
			return { ...d, custom_et_lines: normalizeLeadLines(d.name, lines) };
		});
	};

	const removeLine = (idx: number) => {
		setDraft((d) => {
			if (!d?.name || !d.custom_et_lines) return d;
			const filtered = d.custom_et_lines.filter((_, i) => i !== idx);
			return { ...d, custom_et_lines: normalizeLeadLines(d.name, filtered) };
		});
	};

	const persistLead = async (): Promise<boolean> => {
		const snapshot = draftRef.current;
		if (!snapshot?.name) return false;
		setSaving(true);
		setBanner(null);
		try {
			const payload = structuredClone(snapshot) as LeadDoc & Record<string, unknown>;
			payload.doctype = 'Lead';
			await frappeMethod<LeadDoc>('frappe.client.save', { doc: payload });
			await mutate?.();
			setBanner({ type: 'ok', text: 'Lead saved.' });
			return true;
		} catch (e: unknown) {
			setBanner({ type: 'err', text: e instanceof Error ? e.message : String(e) });
			return false;
		} finally {
			setSaving(false);
		}
	};

	const ensureOppInserted = async (initial: Record<string, unknown>) => {
		if (initial.name) return initial as { name?: string };
		return frappeMethod<{ name?: string }>('frappe.client.insert', {
			doc: { ...initial, doctype: 'Opportunity' },
		});
	};

	const makeOpportunity = async () => {
		const snapshot = draftRef.current;
		if (!snapshot?.name || oppBusy) return;
		setOppBusy(true);
		setBanner(null);
		try {
			const persisted = await persistLead();
			if (!persisted || !snapshot.name) return;

			const rawDoc = await frappeMethod<Record<string, unknown>>(
				'erpnext.crm.doctype.lead.lead.make_opportunity',
				{
					source_name: snapshot.name,
				},
			);

			const doc = await ensureOppInserted(rawDoc);
			const oppName = doc?.name ? String(doc.name) : '';
			if (oppName) {
				setBanner({ type: 'ok', text: `Opportunity ${oppName} created.` });
				void navigate(`/opportunities/${encodeURIComponent(oppName)}`);
				return;
			}
			setBanner({ type: 'err', text: 'Opportunity draft had no identifier after insert.' });
		} catch (e: unknown) {
			setBanner({ type: 'err', text: e instanceof Error ? e.message : String(e) });
		} finally {
			setOppBusy(false);
		}
	};

	if (!name) {
		return <p className="text-red-600">Missing lead.</p>;
	}

	if (isLoading) return <p className="text-zinc-500">Loading lead…</p>;
	if (error || !draft) {
		return (
			<div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
				{error instanceof Error ? error.message : 'Lead not found.'}
				{' '}
				<Link to="/leads" className="text-emerald-900 underline">
					Back to list
				</Link>
			</div>
		);
	}

	return (
		<div className="mx-auto max-w-5xl">
			<div className="mb-6 flex flex-wrap items-center gap-3">
				<Link
					to="/leads"
					className="inline-flex items-center gap-1 text-sm text-zinc-600 hover:text-zinc-900">
					<ArrowLeft className="h-4 w-4" />
					Leads
				</Link>
				<h1 className="text-2xl font-semibold text-zinc-900">Lead · {draft.lead_name || draft.name}</h1>
			</div>

			{banner ? (
				<div
					className={`mb-4 rounded-md border px-3 py-2 text-sm ${
						banner.type === 'ok'
							? 'border-emerald-200 bg-emerald-50 text-emerald-900'
							: 'border-red-200 bg-red-50 text-red-800'
					}`}>
					{banner.text}
				</div>
			) : null}

			<div className="space-y-6 rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
				<section>
					<h2 className="mb-4 text-lg font-medium text-zinc-900">Core</h2>
					<div className="grid gap-4 sm:grid-cols-2">
						<Field label="Lead name">
							<input
								className="input"
								value={draft.lead_name ?? ''}
								onChange={(e) => setField('lead_name', e.target.value)}
							/>
						</Field>
						<Field label="Organization">
							<input
								className="input"
								value={draft.company_name ?? ''}
								onChange={(e) => setField('company_name', e.target.value)}
							/>
						</Field>
						<Field label="ERPNext status">
							<select
								className="input"
								value={draft.status ?? ''}
								onChange={(e) => setField('status', e.target.value)}>
								<option value="Lead">Lead</option>
								<option value="Open">Open</option>
								<option value="Replied">Replied</option>
								<option value="Opportunity">Opportunity</option>
								<option value="Quotation">Quotation</option>
								<option value="Lost Quotation">Lost Quotation</option>
								<option value="Converted">Converted</option>
								<option value="Do Not Contact">Do Not Contact</option>
							</select>
						</Field>
						<Field label="Email">
							<input
								type="email"
								className="input"
								value={draft.email_id ?? ''}
								onChange={(e) => setField('email_id', e.target.value)}
							/>
						</Field>
						<Field label="Phone">
							<input
								className="input"
								value={draft.phone ?? ''}
								onChange={(e) => setField('phone', e.target.value)}
							/>
						</Field>
						<Field label="Mobile">
							<input
								className="input"
								value={draft.mobile_no ?? ''}
								onChange={(e) => setField('mobile_no', e.target.value)}
							/>
						</Field>
					</div>
				</section>

				<section>
					<h2 className="mb-4 text-lg font-medium text-zinc-900">Trading · Earth Trading</h2>
					<div className="grid gap-4 sm:grid-cols-2">
						<Field label="Sales stage">
							<select
								className="input"
								value={draft.custom_et_sales_stage ?? 'Lead'}
								onChange={(e) =>
									setField('custom_et_sales_stage', e.target.value as LeadDoc['custom_et_sales_stage'])
								}>
								{SALES_STAGES.map((s) => (
									<option key={s} value={s}>
										{s}
									</option>
								))}
							</select>
						</Field>
						<Field label="Assigned trader (User link)">
							<input
								className="input"
								value={draft.custom_et_assigned_trader ?? ''}
								onChange={(e) => setField('custom_et_assigned_trader', e.target.value)}
								placeholder="user@company.com"
							/>
						</Field>
						<Field label="Region">
							<input
								className="input"
								value={draft.custom_et_region ?? ''}
								onChange={(e) => setField('custom_et_region', e.target.value)}
							/>
						</Field>
						<Field label="Deal type">
							<select
								className="input"
								value={draft.custom_et_deal_type ?? ''}
								onChange={(e) =>
									setField('custom_et_deal_type', e.target.value as LeadDoc['custom_et_deal_type'])
								}>
								{DEAL_TYPES.map((x) => (
									<option key={x || 'empty'} value={x}>
										{x || '(not set)'}
									</option>
								))}
							</select>
						</Field>
						<Field label="Incoterm (link name)">
							<input
								className="input"
								value={draft.custom_et_incoterm ?? ''}
								onChange={(e) => setField('custom_et_incoterm', e.target.value)}
								placeholder="e.g. CIF Mumbai"
							/>
						</Field>
					</div>
				</section>

				<section>
					<div className="mb-3 flex items-center justify-between gap-4">
						<h2 className="text-lg font-medium text-zinc-900">Commodity lines · ET Lead Line</h2>
						<button
							type="button"
							onClick={addLine}
							className="inline-flex items-center gap-1 rounded-md bg-zinc-100 px-3 py-1.5 text-sm hover:bg-zinc-200">
							<Plus className="h-4 w-4" /> Add row
						</button>
					</div>
					<p className="mb-4 text-xs text-zinc-500">
						Choose an Item or fill specification when there is no catalogue item yet. Lines carry into
						Opportunity on conversion.
					</p>

					<div className="overflow-x-auto rounded border border-zinc-200">
						<table className="min-w-full text-left text-sm">
							<thead className="bg-zinc-50">
								<tr>
									<th className="px-3 py-2 font-medium">Item</th>
									<th className="px-3 py-2 font-medium">Qty</th>
									<th className="px-3 py-2 font-medium">UOM</th>
									<th className="px-3 py-2 font-medium">Specification</th>
									<th className="w-10 px-3 py-2" />
								</tr>
							</thead>
							<tbody>
								{(draft.custom_et_lines ?? []).length === 0 ? (
									<tr>
										<td colSpan={5} className="px-3 py-6 text-center text-zinc-500">
											No lines — add catalogue items before converting to Opportunity.
										</td>
									</tr>
								) : (
									(draft.custom_et_lines ?? []).map((row, rowIndex) => (
										<LineEditorRow
											key={row.name ?? `${rowIndex}`}
											row={row}
											rowIndex={rowIndex}
											onPatch={(patch) => updateLineCells(rowIndex, patch)}
											onRemove={() => removeLine(rowIndex)}
										/>
									))
								)}
							</tbody>
						</table>
					</div>
				</section>

				<div className="flex flex-wrap gap-3 border-t border-zinc-100 pt-6">
					<button
						type="button"
						disabled={saving}
						onClick={() => void persistLead()}
						className="rounded-md bg-emerald-900 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50">
						{saving ? 'Saving…' : 'Save lead'}
					</button>
					<button
						type="button"
						disabled={oppBusy || saving}
						onClick={() => void makeOpportunity()}
						className="rounded-md border border-emerald-900 px-4 py-2 text-sm font-medium text-emerald-900 hover:bg-emerald-50 disabled:opacity-50">
						{oppBusy ? 'Opening opportunity…' : 'Convert to opportunity'}
					</button>
					<a
						className="inline-flex items-center rounded-md px-4 py-2 text-sm text-zinc-600 underline"
						href={`/app/lead/${encodeURIComponent(draft.name!)}`}
						target="_blank"
						rel="noreferrer">
						Full form on Desk →
					</a>
				</div>
			</div>

			<style>{`
				.input { width:100%; border:1px solid #d4d4d8; border-radius: 0.375rem; padding: 0.5rem 0.625rem; font-size: 0.875rem; outline: none;}
				.input:focus { ring: 2px solid #14532d; border-color:#14532d; }
			`}</style>
		</div>
	);
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
	return (
		<label className="block">
			<span className="mb-1 block text-xs font-medium text-zinc-600">{label}</span>
			{children}
		</label>
	);
}

function LineEditorRow({
	row,
	rowIndex,
	onPatch,
	onRemove,
}: {
	row: EtLeadLine;
	rowIndex: number;
	onPatch: (p: Partial<EtLeadLine>) => void;
	onRemove: () => void;
}) {
	const [suggest, setSuggest] = useState<{ value?: string }[]>([]);

	const runSearch = useCallback(async (txt: string) => {
		if (txt.length < 2) {
			setSuggest([]);
			return;
		}
		try {
			const r = await searchLink('Item', txt);
			setSuggest(Array.isArray(r) ? r : []);
		} catch {
			setSuggest([]);
		}
	}, []);

	return (
		<tr className="border-t border-zinc-100">
			<td className="relative px-3 py-2 align-top">
				<input
					className="input"
					value={row.item_code ?? ''}
					placeholder="Item code…"
					onChange={(e) => {
						onPatch({ item_code: e.target.value });
						void runSearch(e.target.value);
					}}
					onBlur={() => setTimeout(() => setSuggest([]), 200)}
				/>
				{suggest.length > 0 ? (
					<ul className="absolute z-10 mt-1 max-h-44 w-full overflow-auto rounded border bg-white shadow">
						{suggest.slice(0, 12).map((s, i) => (
							<li key={`${String(s.value)}-${i}`}>
								<button
									type="button"
									className="block w-full px-2 py-1.5 text-left text-xs hover:bg-zinc-50"
									onClick={() => {
										onPatch({ item_code: s.value ?? '' });
										setSuggest([]);
									}}>
									{s.value ?? '—'}
								</button>
							</li>
						))}
					</ul>
				) : null}
				<span className="sr-only">{rowIndex}</span>
			</td>
			<td className="px-3 py-2 align-top">
				<input
					type="number"
					step="any"
					className="input w-28"
					value={row.qty ?? ''}
					onChange={(e) => onPatch({ qty: Number(e.target.value) || 0 })}
				/>
			</td>
			<td className="px-3 py-2 align-top">
				<input
					className="input w-24"
					value={row.uom ?? ''}
					onChange={(e) => onPatch({ uom: e.target.value })}
					placeholder="Nos…"
				/>
			</td>
			<td className="px-3 py-2 align-top">
				<textarea
					className="input min-h-[2.75rem]"
					value={row.commodity ?? ''}
					onChange={(e) => onPatch({ commodity: e.target.value })}
				/>
			</td>
			<td className="align-top pt-3">
				<button
					type="button"
					className="text-zinc-400 hover:text-red-600"
					onClick={onRemove}
					aria-label="Remove line">
					<Trash2 className="h-4 w-4" />
				</button>
			</td>
		</tr>
	);
}

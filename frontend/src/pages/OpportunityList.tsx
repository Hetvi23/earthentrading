import { Link } from 'react-router-dom';
import { useFrappeGetDocList } from 'frappe-react-sdk';

type Row = {
	name: string;
	title?: string;
	customer_name?: string;
	opportunity_owner?: string;
	status?: string;
	modified?: string;
};

export default function OpportunityList() {
	const { data, error, isLoading } = useFrappeGetDocList<Row>('Opportunity', {
		fields: ['name', 'title', 'customer_name', 'opportunity_owner', 'status', 'modified'],
		orderBy: { field: 'modified', order: 'desc' },
		limit: 150,
	});

	if (isLoading) return <p className="text-zinc-500">Loading opportunities…</p>;
	if (error) {
		return (
			<div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
				Could not load opportunities.
			</div>
		);
	}

	return (
		<div>
			<h1 className="text-2xl font-semibold text-zinc-900">Opportunities</h1>
			<p className="mt-1 text-sm text-zinc-500">Latest (max 100). Open Hub or Desk for quotations & sales orders.</p>
			<div className="mt-6 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
				<table className="w-full text-left text-sm">
					<thead className="border-b bg-zinc-50">
						<tr>
							<th className="px-4 py-3 font-medium">Opportunity</th>
							<th className="px-4 py-3 font-medium">Customer</th>
							<th className="px-4 py-3 font-medium">Owner</th>
							<th className="px-4 py-3 font-medium">Status</th>
							<th className="px-4 py-3 font-medium">Modified</th>
						</tr>
					</thead>
					<tbody>
						{(data ?? []).length === 0 ? (
							<tr>
								<td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
									No opportunities yet — convert from a lead or create in Desk.
								</td>
							</tr>
						) : (
							(data ?? []).map((row) => (
								<tr key={row.name} className="border-t border-zinc-100 hover:bg-zinc-50">
									<td className="px-4 py-3">
										<Link className="font-medium text-emerald-900 hover:underline" to={`/opportunities/${encodeURIComponent(row.name)}`}>
											{row.title || row.name}
										</Link>
									</td>
									<td className="text-zinc-600">{row.customer_name ?? '—'}</td>
									<td className="text-zinc-600">{row.opportunity_owner ?? '—'}</td>
									<td className="text-zinc-600">{row.status ?? '—'}</td>
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

import { useFrappeGetDocList } from 'frappe-react-sdk';

type Row = {
	name: string;
	customer_name?: string;
	transaction_date?: string;
	status?: string;
	grand_total?: number;
	currency?: string;
	custom_et_assigned_trader?: string;
};

export default function SalesOrdersList() {
	const { data, error, isLoading } = useFrappeGetDocList<Row>('Sales Order', {
		fields: [
			'name',
			'customer_name',
			'transaction_date',
			'status',
			'grand_total',
			'currency',
			'custom_et_assigned_trader',
		],
		orderBy: { field: 'modified', order: 'desc' },
		limit: 150,
	});

	if (isLoading) return <p className="text-zinc-500">Loading sales orders…</p>;
	if (error) {
		return (
			<div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
				Could not load sales orders (check role / permissions).
			</div>
		);
	}

	return (
		<div>
			<h1 className="text-2xl font-semibold text-zinc-900">Sales orders</h1>
			<p className="mt-1 text-sm text-zinc-500">Open in Desk for delivery, invoicing & stock linkage.</p>
			<div className="mt-6 overflow-x-auto rounded-lg border border-zinc-200 bg-white shadow-sm">
				<table className="w-full text-left text-sm">
					<thead className="border-b bg-zinc-50">
						<tr>
							<th className="whitespace-nowrap px-4 py-3 font-medium">Sales order</th>
							<th className="px-4 py-3 font-medium">Customer</th>
							<th className="px-4 py-3 font-medium">Date</th>
							<th className="px-4 py-3 font-medium">Status</th>
							<th className="whitespace-nowrap px-4 py-3 text-right font-medium">Total</th>
							<th className="px-4 py-3 font-medium">Trader</th>
						</tr>
					</thead>
					<tbody>
						{(data ?? []).length === 0 ? (
							<tr>
								<td colSpan={6} className="px-4 py-10 text-center text-zinc-500">
									No sales orders in your scope.
								</td>
							</tr>
						) : (
							(data ?? []).map((row) => (
								<tr key={row.name} className="border-t border-zinc-100 hover:bg-zinc-50">
									<td className="px-4 py-3">
										<a
											href={`/app/sales-order/${encodeURIComponent(row.name)}`}
											className="font-medium text-emerald-900 hover:underline">
											{row.name}
										</a>
									</td>
									<td className="text-zinc-600">{row.customer_name ?? '—'}</td>
									<td className="whitespace-nowrap text-zinc-600">{row.transaction_date ?? '—'}</td>
									<td className="text-zinc-600">{row.status ?? '—'}</td>
									<td className="whitespace-nowrap text-right text-zinc-700">
										{row.grand_total != null ? `${row.currency ?? ''} ${row.grand_total}`.trim() : '—'}
									</td>
									<td className="text-zinc-500">{row.custom_et_assigned_trader ?? '—'}</td>
								</tr>
							))
						)}
					</tbody>
				</table>
			</div>
		</div>
	);
}

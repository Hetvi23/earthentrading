import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

export default function Login() {
	const [usr, setUsr] = useState('');
	const [pwd, setPwd] = useState('');
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const navigate = useNavigate();
	const location = useLocation();
	const from = (location.state as { from?: string } | null)?.from || '/dashboard';

	async function handleSubmit(e: React.FormEvent) {
		e.preventDefault();
		setLoading(true);
		setError(null);
		try {
			const form = new URLSearchParams();
			form.append('usr', usr);
			form.append('pwd', pwd);
			const res = await fetch('/api/method/login', {
				method: 'POST',
				credentials: 'include',
				headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
				body: form.toString(),
			});
			const data = (await res.json().catch(() => ({}))) as { message?: string };
			if (res.ok) {
				window.location.href = `/earthentrading${from.startsWith('/') ? from : '/dashboard'}`;
				return;
			}
			setError(typeof data.message === 'string' ? data.message : 'Login failed');
		} catch {
			setError('Login failed');
		} finally {
			setLoading(false);
		}
	}

	return (
		<div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-emerald-950 via-zinc-900 to-zinc-950 p-6">
			<div className="w-full max-w-md rounded-xl border border-zinc-700/50 bg-white/95 p-8 shadow-2xl">
				<h1 className="text-center text-xl font-semibold text-zinc-900">Earth Trading Hub</h1>
				<p className="mb-6 text-center text-sm text-zinc-500">Sign in with your Frappe user</p>
				<form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
					<div>
						<label htmlFor="usr" className="mb-1 block text-xs font-medium text-zinc-700">
							Email or username
						</label>
						<input
							id="usr"
							className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-emerald-800 focus:border-emerald-800 focus:ring-1"
							value={usr}
							onChange={(e) => setUsr(e.target.value)}
							autoComplete="username"
							required
						/>
					</div>
					<div>
						<label htmlFor="pwd" className="mb-1 block text-xs font-medium text-zinc-700">
							Password
						</label>
						<input
							id="pwd"
							type="password"
							className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-emerald-800 focus:border-emerald-800 focus:ring-1"
							value={pwd}
							onChange={(e) => setPwd(e.target.value)}
							autoComplete="current-password"
							required
						/>
					</div>
					{error ? <p className="text-sm text-red-600">{error}</p> : null}
					<button
						type="submit"
						disabled={loading}
						className="w-full rounded-md bg-emerald-900 py-2.5 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-60">
						{loading ? 'Signing in…' : 'Sign in'}
					</button>
				</form>
				<button
					type="button"
					className="mt-4 w-full text-center text-xs text-zinc-500 underline"
					onClick={() => navigate(-1)}>
					Back
				</button>
			</div>
		</div>
	);
}

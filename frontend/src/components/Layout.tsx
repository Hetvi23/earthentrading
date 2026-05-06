import { Link, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import {
	BookMarked,
	FolderKanban,
	LayoutDashboard,
	ListIcon,
	LogOut,
	Receipt,
	ShoppingCart,
	SquareKanban,
	ListChecks,
	ListTodo,
} from 'lucide-react';

function NavSection({ title, children }: { title: string; children: ReactNode }) {
	return (
		<div className="mb-4">
			<p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">{title}</p>
			<div className="flex flex-col gap-0.5">{children}</div>
		</div>
	);
}

export default function Layout({ children }: { children: ReactNode }) {
	const { pathname } = useLocation();
	const active = (prefix: string) => pathname === prefix || pathname.startsWith(`${prefix}/`);
	const linkCls = (prefix: string) =>
		`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${
			active(prefix) ? 'bg-emerald-900 text-white' : 'text-zinc-700 hover:bg-zinc-100'
		}`;

	async function logout() {
		await fetch('/api/method/logout', { method: 'POST', credentials: 'include' });
		window.location.href = '/earthentrading/login';
	}

	return (
		<div className="flex min-h-screen bg-zinc-50">
			<aside className="flex w-56 shrink-0 flex-col border-r border-zinc-200 bg-white">
				<div className="shrink-0 border-b border-zinc-100 px-4 py-4">
					<p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Earth Trading</p>
					<p className="text-sm text-zinc-500">Hub</p>
				</div>
				<nav className="min-h-0 flex-1 overflow-y-auto px-2 py-3">
					<NavSection title="Overview">
						<Link className={linkCls('/dashboard')} to="/dashboard">
							<LayoutDashboard className="h-4 w-4 shrink-0" />
							Dashboard
						</Link>
					</NavSection>
					<NavSection title="Pipeline">
						<Link className={linkCls('/leads')} to="/leads">
							<ListIcon className="h-4 w-4 shrink-0" />
							Leads
						</Link>
						<Link className={linkCls('/opportunities')} to="/opportunities">
							<SquareKanban className="h-4 w-4 shrink-0" />
							Opportunities
						</Link>
						<Link className={linkCls('/quotations')} to="/quotations">
							<Receipt className="h-4 w-4 shrink-0" />
							Quotations
						</Link>
						<Link className={linkCls('/sales-orders')} to="/sales-orders">
							<ShoppingCart className="h-4 w-4 shrink-0" />
							Sales orders
						</Link>
					</NavSection>
					<NavSection title="Delivery">
						<Link className={linkCls('/projects')} to="/projects">
							<FolderKanban className="h-4 w-4 shrink-0" />
							Projects
						</Link>
						<Link className={linkCls('/tasks')} to="/tasks">
							<ListChecks className="h-4 w-4 shrink-0" />
							Tasks
						</Link>
						<Link className={linkCls('/todos')} to="/todos">
							<ListTodo className="h-4 w-4 shrink-0" />
							My to-dos
						</Link>
						<Link className={linkCls('/task-templates')} to="/task-templates">
							<BookMarked className="h-4 w-4 shrink-0" />
							Task templates
						</Link>
					</NavSection>
				</nav>
				<div className="shrink-0 border-t border-zinc-100 p-3">
					<button
						type="button"
						onClick={() => void logout()}
						className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-zinc-600 hover:bg-zinc-100">
						<LogOut className="h-4 w-4" />
						Log out
					</button>
				</div>
			</aside>
			<main className="min-h-screen min-w-0 flex-1 overflow-auto p-6 md:p-8">{children}</main>
		</div>
	);
}

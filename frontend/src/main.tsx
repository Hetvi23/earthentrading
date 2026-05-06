import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';

function initApp() {
	const win = window as Window & { frappe?: { boot?: unknown; model?: { sync?: (d: unknown) => void } } };
	if (!win.frappe) {
		win.frappe = {};
	}
	if (win.frappe.boot && win.frappe.model && typeof win.frappe.model.sync === 'function') {
		try {
			const boot = win.frappe.boot as { docs?: unknown };
			if (boot.docs) {
				win.frappe.model.sync(boot.docs);
			}
		} catch {
			// frappe-react-sdk still works without model.sync
		}
	}
	createRoot(document.getElementById('root') as HTMLElement).render(
		<StrictMode>
			<App />
		</StrictMode>,
	);
}

if (import.meta.env.DEV) {
	fetch('/api/method/earthentrading.www.earthentrading.get_context_for_dev', { method: 'POST' })
		.then((response) => response.json())
		.then((values: { message: string }) => {
			const v = JSON.parse(values.message) as Record<string, unknown>;
			const win = window as Window & { frappe?: Record<string, unknown> };
			if (!win.frappe) win.frappe = {};
			win.frappe.boot = v;
			win.frappe._messages = (v.__messages as Record<string, string>) || {};
			initApp();
		})
		.catch(() => {
			initApp();
		});
} else if (document.readyState === 'loading') {
	document.addEventListener('DOMContentLoaded', () => initApp());
} else {
	initApp();
}

import { Navigate, Outlet, useLocation } from 'react-router-dom';

function isLoggedIn(): boolean {
	const user = (window as unknown as { frappe?: { boot?: { user?: { name?: string } } } }).frappe?.boot?.user;
	const name = typeof user === 'string' ? user : user?.name;
	return Boolean(name && name !== 'Guest');
}

export default function ProtectedRoute() {
	const location = useLocation();
	if (!isLoggedIn()) {
		return <Navigate to="/login" replace state={{ from: location.pathname }} />;
	}
	return <Outlet />;
}

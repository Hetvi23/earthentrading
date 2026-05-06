import { FrappeProvider } from 'frappe-react-sdk';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import LeadDetail from './pages/LeadDetail';
import Leads from './pages/Leads';
import Login from './pages/Login';
import OpportunityDetail from './pages/OpportunityDetail';
import OpportunityList from './pages/OpportunityList';
import ProjectDetail from './pages/ProjectDetail';
import ProjectsList from './pages/ProjectsList';
import QuotationsList from './pages/QuotationsList';
import SalesOrdersList from './pages/SalesOrdersList';
import TaskTemplatesList from './pages/TaskTemplatesList';
import TasksHub from './pages/TasksHub';
import TodosHub from './pages/TodosHub';

export default function App() {
	return (
		<FrappeProvider
			swrConfig={{ errorRetryCount: 2 }}
			socketPort={import.meta.env.VITE_SOCKET_PORT || undefined}
			siteName={(window as unknown as { frappe?: { boot?: { sitename?: string } } }).frappe?.boot?.sitename ?? import.meta.env.VITE_SITE_NAME}>
			<BrowserRouter basename="/earthentrading">
				<Routes>
					<Route path="/login" element={<Login />} />
					<Route element={<ProtectedRoute />}>
						<Route path="/" element={<Navigate to="/dashboard" replace />} />
						<Route
							path="/dashboard"
							element={
								<Layout>
									<Dashboard />
								</Layout>
							}
						/>
						<Route
							path="/leads"
							element={
								<Layout>
									<Leads />
								</Layout>
							}
						/>
						<Route
							path="/leads/:name"
							element={
								<Layout>
									<LeadDetail />
								</Layout>
							}
						/>
						<Route
							path="/opportunities"
							element={
								<Layout>
									<OpportunityList />
								</Layout>
							}
						/>
						<Route
							path="/opportunities/:name"
							element={
								<Layout>
									<OpportunityDetail />
								</Layout>
							}
						/>
						<Route
							path="/quotations"
							element={
								<Layout>
									<QuotationsList />
								</Layout>
							}
						/>
						<Route
							path="/sales-orders"
							element={
								<Layout>
									<SalesOrdersList />
								</Layout>
							}
						/>
						<Route
							path="/projects"
							element={
								<Layout>
									<ProjectsList />
								</Layout>
							}
						/>
						<Route
							path="/projects/:name"
							element={
								<Layout>
									<ProjectDetail />
								</Layout>
							}
						/>
						<Route
							path="/tasks"
							element={
								<Layout>
									<TasksHub />
								</Layout>
							}
						/>
						<Route
							path="/todos"
							element={
								<Layout>
									<TodosHub />
								</Layout>
							}
						/>
						<Route
							path="/task-templates"
							element={
								<Layout>
									<TaskTemplatesList />
								</Layout>
							}
						/>
					</Route>
					<Route path="*" element={<Navigate to="/dashboard" replace />} />
				</Routes>
			</BrowserRouter>
		</FrappeProvider>
	);
}

import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import { useAuth } from './context/AuthContext';
import { Spinner } from './components/ui';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import RiskMap from './pages/RiskMap';
import Monitoring from './pages/Monitoring';
import Alerts from './pages/Alerts';
import FieldReports from './pages/FieldReports';
import RoadsPage from './pages/RoadsPage';
import Emergency from './pages/Emergency';
import Analytics from './pages/Analytics';
import SimulationCenter from './pages/SimulationCenter';

function Protected({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return <Spinner label="Loading session…" />;
  // Demo mode: the backend accepts anonymous demo access, so the app does
  // not lock pages - login is offered but optional.
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/map" element={<RiskMap />} />
        <Route path="/monitoring" element={<Monitoring />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/reports" element={<FieldReports />} />
        <Route path="/roads" element={<RoadsPage />} />
        <Route path="/emergency" element={<Emergency />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/simulation" element={<SimulationCenter />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

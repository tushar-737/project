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


/* ==========================================================
   AUTHENTICATION PROTECTION
========================================================== */

function Protected({ children }) {
  const { user, ready } = useAuth();

  if (!ready) {
    return <Spinner label="Loading session…" />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}


/* ==========================================================
   ROLE-BASED PROTECTION
========================================================== */

function RoleProtected({ children, allowedRoles }) {
  const { user, ready } = useAuth();

  if (!ready) {
    return <Spinner label="Checking access…" />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return children;
}


/* ==========================================================
   APPLICATION ROUTES
========================================================== */

export default function App() {

  return (

    <Routes>

      {/* ==================================================
          LOGIN
      ================================================== */}

      <Route path="/login" element={<Login />} />


      {/* ==================================================
          PROTECTED APPLICATION
      ================================================== */}

      <Route
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >

        {/* ALL USERS */}

        <Route
          path="/"
          element={<Dashboard />}
        />

        <Route
          path="/map"
          element={<RiskMap />}
        />

        <Route
          path="/alerts"
          element={<Alerts />}
        />

        <Route
          path="/reports"
          element={<FieldReports />}
        />

        <Route
          path="/roads"
          element={<RoadsPage />}
        />


        {/* ==================================================
            FIELD OFFICER + ADMIN
        ================================================== */}

        <Route
          path="/monitoring"
          element={
            <RoleProtected
              allowedRoles={[
                'FIELD_OFFICER',
                'ADMIN'
              ]}
            >
              <Monitoring />
            </RoleProtected>
          }
        />

        <Route
          path="/emergency"
          element={
            <RoleProtected
              allowedRoles={[
                'FIELD_OFFICER',
                'ADMIN'
              ]}
            >
              <Emergency />
            </RoleProtected>
          }
        />


        {/* ==================================================
            ADMIN ONLY
        ================================================== */}

        <Route
          path="/analytics"
          element={
            <RoleProtected
              allowedRoles={['ADMIN']}
            >
              <Analytics />
            </RoleProtected>
          }
        />

        <Route
          path="/simulation"
          element={
            <RoleProtected
              allowedRoles={['ADMIN']}
            >
              <SimulationCenter />
            </RoleProtected>
          }
        />

      </Route>


      {/* ==================================================
          UNKNOWN ROUTES
      ================================================== */}

      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />

    </Routes>

  );

}
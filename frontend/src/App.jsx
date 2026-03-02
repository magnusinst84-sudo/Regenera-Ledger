import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/routes/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import CompanyDashboard from './pages/CompanyDashboard';
import ESGAnalysis from './pages/ESGAnalysis';
import Scope3Viz from './pages/Scope3Viz';
import CarbonGap from './pages/CarbonGap';
import Matching from './pages/Matching';
import FarmerDashboard from './pages/FarmerDashboard';
import FarmerProfile from './pages/FarmerProfile';
import FarmerEstimation from './pages/FarmerEstimation';

function DashboardDispatcher() {
  const { user } = useAuth();
  if (user?.role === 'farmer') return <FarmerDashboard />;
  return <CompanyDashboard />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes — redirect to /login if not authenticated */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardDispatcher />} />
              <Route path="/esg-analysis" element={<ESGAnalysis />} />
              <Route path="/scope3" element={<Scope3Viz />} />
              <Route path="/carbon-gap" element={<CarbonGap />} />
              <Route path="/matching" element={<Matching />} />
              <Route path="/farmer/profile" element={<FarmerProfile />} />
              <Route path="/farmer/estimate" element={<FarmerEstimation />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

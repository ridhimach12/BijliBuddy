import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import CustomerDashboard from './pages/CustomerDashboard';
import CustomerProfilePage from './pages/CustomerProfilePage';
import RequestServicePage from './pages/RequestServicePage';
import BookingStatusPage from './pages/BookingStatusPage';
import ElectriciansDirectoryPage from './pages/ElectriciansDirectoryPage';
import ElectricianPublicProfilePage from './pages/ElectricianPublicProfilePage';
import ElectricianDashboard from './pages/ElectricianDashboard';
import ElectricianProfileEditPage from './pages/ElectricianProfileEditPage';
import AdminDashboard from './pages/AdminDashboard';

function ProtectedRoute({ allowedRoles, children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="max-w-7xl mx-auto p-8 text-sm text-slate-500">Verifying session...</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col bg-[#FAF9F5] text-[#0F1E36]">
          <Navbar />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/request-service" element={<RequestServicePage />} />
              <Route path="/electricians" element={<ElectriciansDirectoryPage />} />
              <Route path="/electricians/:id" element={<ElectricianPublicProfilePage />} />

              <Route
                path="/customer/dashboard"
                element={
                  <ProtectedRoute allowedRoles={['customer']}>
                    <CustomerDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/customer/profile"
                element={
                  <ProtectedRoute allowedRoles={['customer']}>
                    <CustomerProfilePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/bookings/:id"
                element={
                  <ProtectedRoute allowedRoles={['customer', 'electrician', 'admin']}>
                    <BookingStatusPage />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/electrician/dashboard"
                element={
                  <ProtectedRoute allowedRoles={['electrician']}>
                    <ElectricianDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/electrician/profile"
                element={
                  <ProtectedRoute allowedRoles={['electrician']}>
                    <ElectricianProfileEditPage />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/admin/dashboard"
                element={
                  <ProtectedRoute allowedRoles={['admin']}>
                    <AdminDashboard />
                  </ProtectedRoute>
                }
              />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

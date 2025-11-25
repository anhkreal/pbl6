import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './state/authStore';
import LayoutShell from './components/LayoutShell';
import AdminDashboard from './pages/admin/Dashboard';
import AdminEmotionLog from './pages/admin/EmotionLog';
import AdminAttendance from './pages/admin/Attendance';
import AdminKPIReport from './pages/admin/KPIReport';
import Employees from './pages/admin/Employees';
import EmployeeDetail from './pages/admin/EmployeeDetail';
import Profile from './pages/admin/Profile';
import StaffDashboard from './pages/staff/Dashboard';
import StaffEmotionLog from './pages/staff/EmotionLog';
import StaffAttendance from './pages/staff/Attendance';
import StaffKPIReport from './pages/staff/KPIReport';
import StaffProfile from './pages/staff/Profile';
import StaffImageUpdate from './pages/staff/ImageUpdate';
import StaffContact from './pages/staff/Contact';
import LoginPage from './components/LoginPage';

const AdminRoutes = () => (
  <Routes>
    <Route path="dashboard" element={<AdminDashboard />} />
    <Route path="emotions" element={<AdminEmotionLog />} />
    <Route path="attendance" element={<AdminAttendance />} />
    <Route path="kpi" element={<AdminKPIReport />} />
    <Route path="employees" element={<Employees />} />
    <Route path="employeedetail" element={<EmployeeDetail />} />
    <Route path="employees/:id" element={<EmployeeDetail />} />
    <Route path="profile" element={<Profile />} />
    <Route path="*" element={<Navigate to="dashboard" replace />} />
  </Routes>
);

const StaffRoutes = () => (
  <Routes>
    <Route path="dashboard" element={<StaffDashboard />} />
    <Route path="emotions" element={<StaffEmotionLog />} />
    <Route path="attendance" element={<StaffAttendance />} />
    <Route path="kpi" element={<StaffKPIReport />} />
    <Route path="profile" element={<StaffProfile />} />
    <Route path="image" element={<StaffImageUpdate />} />
    <Route path="contact" element={<StaffContact />} />
    <Route path="*" element={<Navigate to="dashboard" replace />} />
  </Routes>
);

export default function AppRouter() {
  const { token, role } = useAuthStore();
  if (!token) return <LoginPage />;
  return <LayoutShell>
    {role === 'admin' ? <AdminRoutes /> : <StaffRoutes />}
  </LayoutShell>;
}

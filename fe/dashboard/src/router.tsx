import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './state/authStore';
import LayoutShell from './components/LayoutShell';
import AdminDashboard from './pages/admin/Dashboard';
import AdminEmotionLog from './pages/admin/EmotionLog';
import AdminAttendance from './pages/admin/Attendance';
import AdminKPIReport from './pages/admin/KPIReport';
import AdminAnalysis from './pages/admin/Analysis';
import Employees from './pages/admin/Employees';
import EmployeeDetail from './pages/admin/EmployeeDetail';
import Profile from './pages/admin/Profile';
import StaffDashboard from './pages/staff/Dashboard';
import StaffEmotionLog from './pages/staff/EmotionLog';
import StaffAttendance from './pages/staff/Attendance';
import StaffKPIReport from './pages/staff/KPIReport';
import StaffAnalysis from './pages/staff/Analysis';
import StaffProfile from './pages/staff/Profile';
import StaffImageUpdate from './pages/staff/ImageUpdate';
import StaffContact from './pages/staff/Contact';
import LoginPage from './components/LoginPage';

const AdminRoutes = () => (
  <Routes>
    <Route path="/admin/dashboard" element={<AdminDashboard />} />
    <Route path="/admin/analysis" element={<AdminAnalysis />} />
    <Route path="/admin/emotions" element={<AdminEmotionLog />} />
    <Route path="/admin/attendance" element={<AdminAttendance />} />
    <Route path="/admin/kpi" element={<AdminKPIReport />} />
    <Route path="/admin/employees" element={<Employees />} />
    <Route path="/admin/employeedetail" element={<EmployeeDetail />} />
    <Route path="/admin/employees/:id" element={<EmployeeDetail />} />
    <Route path="/admin/profile" element={<Profile />} />
    <Route path="*" element={<Navigate to="/admin/dashboard" replace />} />
  </Routes>
);

const StaffRoutes = () => (
  <Routes>
    <Route path="/staff/dashboard" element={<StaffDashboard />} />
    <Route path="/staff/analysis" element={<StaffAnalysis />} />
    <Route path="/staff/emotions" element={<StaffEmotionLog />} />
    <Route path="/staff/attendance" element={<StaffAttendance />} />
    <Route path="/staff/kpi" element={<StaffKPIReport />} />
    <Route path="/staff/profile" element={<StaffProfile />} />
    <Route path="/staff/image" element={<StaffImageUpdate />} />
    <Route path="/staff/contact" element={<StaffContact />} />
    <Route path="*" element={<Navigate to="/staff/dashboard" replace />} />
  </Routes>
);

export default function AppRouter() {
  const { token, role } = useAuthStore();
  if (!token) return <LoginPage />;
  return <LayoutShell>
    {role === 'admin' ? <AdminRoutes /> : <StaffRoutes />}
  </LayoutShell>;
}

import React, { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import Login from './pages/Login';
import AdminDashboard from './pages/admin/Dashboard';
import Employees from './pages/admin/Employees';
import EmotionLog from './pages/admin/EmotionLog';
import Attendance from './pages/admin/Attendance';
import KPIReport from './pages/admin/KPIReport';
import AdminProfile from './pages/admin/Profile';
import StaffDashboard from './pages/staff/Dashboard';
import StaffEmotionLog from './pages/staff/EmotionLog';
import StaffAttendance from './pages/staff/Attendance';
import StaffKPIReport from './pages/staff/KPIReport';
import StaffProfile from './pages/staff/Profile';
import ImageUpdate from './pages/staff/ImageUpdate';
import Contact from './pages/staff/Contact';
import EmployeeDetail from './pages/admin/EmployeeDetail';
import { ErrorBoundary } from './ErrorBoundary';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        {/* Admin */}
        <Route path="/admin/dashboard" element={<AdminDashboard />} />
        <Route path="/admin/employees" element={<Employees />} />
        <Route path="/admin/emotions" element={<EmotionLog />} />
        <Route path="/admin/employeedetail" element={<EmployeeDetail />} />
        <Route path="/admin/attendance" element={<Attendance />} />
        <Route path="/admin/kpi" element={<KPIReport />} />
        <Route path="/admin/profile" element={<AdminProfile />} />
        {/* Staff */}
        <Route path="/staff/dashboard" element={<StaffDashboard />} />
        <Route path="/staff/emotions" element={<StaffEmotionLog />} />
        <Route path="/staff/attendance" element={<StaffAttendance />} />
        <Route path="/staff/kpi" element={<StaffKPIReport />} />
        <Route path="/staff/profile" element={<StaffProfile />} />
        <Route path="/staff/image-update" element={<ImageUpdate />} />
        <Route path="/staff/contact" element={<Contact />} />
        <Route path="*" element={<div style={{ padding: 32 }}>404</div>} />
      </Routes>
    </BrowserRouter>
  );
}

const rootEl = document.getElementById('root');
if (rootEl) {
  createRoot(rootEl).render(
    <StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </StrictMode>
  );
} else {
  console.error('Missing <div id="root"></div> in index.html');
}
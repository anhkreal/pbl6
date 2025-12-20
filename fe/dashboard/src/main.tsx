import React, { StrictMode, Suspense, lazy } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
const Login = lazy(() => import('./pages/Login'));
const AdminDashboard = lazy(() => import('./pages/admin/Dashboard'));
const Employees = lazy(() => import('./pages/admin/Employees'));
const EmotionLog = lazy(() => import('./pages/admin/EmotionLog'));
const Attendance = lazy(() => import('./pages/admin/Attendance'));
const KPIReport = lazy(() => import('./pages/admin/KPIReport'));
const AdminProfile = lazy(() => import('./pages/admin/Profile'));
const AdminAnalysis = lazy(() => import('./pages/admin/Analysis'));
const StaffDashboard = lazy(() => import('./pages/staff/Dashboard'));
const StaffEmotionLog = lazy(() => import('./pages/staff/EmotionLog'));
const StaffAttendance = lazy(() => import('./pages/staff/Attendance'));
const StaffKPIReport = lazy(() => import('./pages/staff/KPIReport'));
const StaffProfile = lazy(() => import('./pages/staff/Profile'));
const StaffAnalysis = lazy(() => import('./pages/staff/Analysis'));
const ImageUpdate = lazy(() => import('./pages/staff/ImageUpdate'));
const Contact = lazy(() => import('./pages/staff/Contact'));
const EmployeeDetail = lazy(() => import('./pages/admin/EmployeeDetail'));
import { ErrorBoundary } from './ErrorBoundary';

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div style={{ padding: 24 }}>Đang tải...</div>}>
        <Routes>
          <Route path="/" element={<Login />} />
          {/* Admin */}
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/admin/employees" element={<Employees />} />
          <Route path="/admin/emotions" element={<EmotionLog />} />
          <Route path="/admin/employeedetail" element={<EmployeeDetail />} />
          <Route path="/admin/attendance" element={<Attendance />} />
          <Route path="/admin/kpi" element={<KPIReport />} />
          <Route path="/admin/analysis" element={<AdminAnalysis />} />
          <Route path="/admin/profile" element={<AdminProfile />} />
          {/* Staff */}
          <Route path="/staff/dashboard" element={<StaffDashboard />} />
          <Route path="/staff/emotions" element={<StaffEmotionLog />} />
          <Route path="/staff/attendance" element={<StaffAttendance />} />
          <Route path="/staff/kpi" element={<StaffKPIReport />} />
          <Route path="/staff/analysis" element={<StaffAnalysis />} />
          <Route path="/staff/profile" element={<StaffProfile />} />
          <Route path="/staff/image-update" element={<ImageUpdate />} />
          <Route path="/staff/contact" element={<Contact />} />
          <Route path="*" element={<div style={{ padding: 32 }}>404</div>} />
        </Routes>
      </Suspense>
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
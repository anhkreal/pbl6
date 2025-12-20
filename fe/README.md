# 📊 Dashboard Frontend - Face Recognition System

**Version:** 2.0.0  
**Technology:** React + TypeScript + Vite  
**Last Updated:** December 2025

---

## 📋 Table of Contents

1. [Module Overview](#module-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Installation & Setup](#installation--setup)
6. [Key Components](#key-components)
7. [API Integration](#api-integration)
8. [Features](#features)
9. [Deployment](#deployment)

---

## 🎯 Module Overview

### **Purpose**
The Dashboard Frontend provides a **comprehensive web interface** for:

- Real-time face recognition monitoring
- Employee attendance tracking
- Emotion analytics and KPI scores
- User & account management
- System administration and configuration

### **Target Users**
- **Managers:** View KPI, attendance, emotion analytics
- **Admins:** Manage users, embeddings, system settings
- **HR:** Employee data, shift assignment, role management

### **Key Features**

| Feature | User | Purpose |
|---------|------|---------|
| **Real-time Monitor** | Manager | Live face recognition feed |
| **Attendance Dashboard** | HR | Check-in/out logs, reports |
| **Emotion Analytics** | Manager | Emotional state trends |
| **KPI Scores** | Manager | Employee performance metrics |
| **User Management** | Admin | CRUD employees & accounts |
| **Embedding Management** | Admin | View/delete face embeddings |
| **System Settings** | Admin | Model configuration, API setup |

---

## 🏛️ Architecture

### **Frontend Architecture**

```
┌─────────────────────────────────────────────────────┐
│          React SPA (Single Page App)                 │
│           Running in Browser                         │
└────────────┬────────────────────────────────────────┘
             │
   ┌─────────┴──────────┬──────────┬─────────────┐
   │                    │          │             │
┌──▼──┐    ┌────────┐  ┌┴────┐  ┌─┴────┐  ┌────▼──┐
│Pages│    │ Routes │  │State│  │Hooks │  │Utils  │
│     │    │ (Router)  │     │  │      │  │       │
└──┬──┘    └────────┘  └─────┘  └──────┘  └───────┘
   │
   ├─ Login
   ├─ Dashboard (Main)
   ├─ Attendance
   │  ├─ Real-time
   │  ├─ Check-in History
   │  └─ Reports
   │
   ├─ Users
   │  ├─ List
   │  ├─ Add/Edit
   │  └─ Delete
   │
   ├─ Emotions
   │  ├─ Analytics
   │  ├─ Logs
   │  └─ KPI
   │
   ├─ Embeddings
   │  ├─ List
   │  ├─ Upload
   │  └─ Delete
   │
   └─ Admin
      ├─ Settings
      ├─ Database
      └─ System Health

         │
         ▼
   ┌──────────────────┐
   │ UI Components    │
   │ (Reusable)       │
   │                  │
   ├─ Button          │
   ├─ Form            │
   ├─ Table           │
   ├─ Modal           │
   ├─ Chart           │
   └─ Alert           │
   └──────────────────┘
         │
         ▼
   ┌──────────────────────────────┐
   │ Styling & Theme              │
   │ (Tailwind CSS / Material UI) │
   └──────────────────────────────┘
         │
         ▼
   ┌────────────────────────────────┐
   │ HTTP Client (Axios/Fetch)      │
   │ Authentication & Headers       │
   └────────────┬───────────────────┘
                │
                ▼
        ┌───────────────────┐
        │ Central API       │
        │ Server (FastAPI)  │
        │ port 8000         │
        └───────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Framework** | React | 18.x | UI library |
| **Language** | TypeScript | 5.x | Type safety |
| **Build Tool** | Vite | 5.x | Fast bundling |
| **Routing** | React Router | 6.x | Page navigation |
| **State** | Context API / Redux | - | Global state |
| **HTTP** | Axios | 1.x | API calls |
| **Charts** | Chart.js / Recharts | - | Analytics visualization |
| **UI Framework** | Tailwind CSS | 3.x | Styling |
| **Icons** | React Icons | 5.x | Icon library |
| **Date/Time** | Day.js | 1.x | Date handling |

---

## 📁 Project Structure

```
fe/dashboard/
├── package.json                    # Dependencies & scripts
├── tsconfig.json                  # TypeScript config
├── vite.config.ts                 # Vite config
├── tailwind.config.js             # Tailwind config
│
├── public/                        # Static assets
│   ├── favicon.ico
│   └── index.html
│
├── src/
│   ├── main.tsx                   # Entry point
│   ├── App.tsx                    # Root component
│   │
│   ├── api/
│   │   ├── client.ts              # Axios instance with auth
│   │   ├── auth.api.ts            # Auth endpoints
│   │   ├── users.api.ts           # User endpoints
│   │   ├── attendance.api.ts      # Attendance endpoints
│   │   ├── emotion.api.ts         # Emotion endpoints
│   │   └── kpi.api.ts             # KPI endpoints
│   │
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Header.tsx         # Top navigation
│   │   │   ├── Sidebar.tsx        # Left menu
│   │   │   └── Layout.tsx         # Main layout
│   │   │
│   │   ├── Common/
│   │   │   ├── Button.tsx
│   │   │   ├── Form.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Loading.tsx
│   │   │   └── Alert.tsx
│   │   │
│   │   ├── Dashboard/
│   │   │   ├── MetricCard.tsx     # KPI card
│   │   │   ├── Chart.tsx
│   │   │   └── RecentActivity.tsx
│   │   │
│   │   └── Forms/
│   │       ├── LoginForm.tsx
│   │       ├── UserForm.tsx
│   │       └── EmbeddingUpload.tsx
│   │
│   ├── pages/
│   │   ├── auth/
│   │   │   └── Login.tsx
│   │   │
│   │   ├── admin/
│   │   │   ├── Dashboard.tsx      # Main dashboard
│   │   │   ├── Users.tsx          # User management
│   │   │   ├── AttendanceLog.tsx
│   │   │   ├── EmotionLog.tsx
│   │   │   ├── Embeddings.tsx
│   │   │   └── Settings.tsx
│   │   │
│   │   ├── staff/
│   │   │   ├── Dashboard.tsx      # Staff view
│   │   │   ├── AttendanceLog.tsx
│   │   │   ├── EmotionLog.tsx
│   │   │   └── KPI.tsx
│   │   │
│   │   └── error/
│   │       ├── NotFound.tsx       # 404 page
│   │       └── Unauthorized.tsx   # 401 page
│   │
│   ├── hooks/
│   │   ├── useAuth.ts             # Auth context hook
│   │   ├── useApi.ts              # API call hook
│   │   ├── useLocalStorage.ts     # Local storage hook
│   │   └── usePagination.ts       # Pagination hook
│   │
│   ├── context/
│   │   ├── AuthContext.tsx        # Auth global state
│   │   └── NotificationContext.tsx
│   │
│   ├── types/
│   │   ├── index.ts               # TypeScript interfaces
│   │   ├── api.ts                 # API response types
│   │   └── domain.ts              # Domain models
│   │
│   ├── utils/
│   │   ├── constants.ts           # Constants
│   │   ├── helpers.ts             # Utility functions
│   │   ├── formatters.ts          # Format functions
│   │   └── validators.ts          # Validation
│   │
│   ├── styles/
│   │   ├── globals.css            # Global styles
│   │   └── variables.css          # CSS variables
│   │
│   └── router/
│       └── index.tsx              # Route definitions
│
└── .env.example                   # Environment variables
```

---

## 🚀 Installation & Setup

### **Prerequisites**
- Node.js 16+ & npm/yarn
- Modern browser (Chrome, Firefox, Edge)
- Face Recognition API Server running

### **Step 1: Install Dependencies**

```bash
cd fe/dashboard
npm install
# or
yarn install
```

### **Step 2: Environment Configuration**

Create `.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_APP_NAME=Face Recognition Dashboard
```

### **Step 3: Development Server**

```bash
npm run dev
# or
yarn dev

# Server starts at http://localhost:5173
```

### **Step 4: Build for Production**

```bash
npm run build
# or
yarn build

# Output: dist/
```

### **Step 5: Preview Production Build**

```bash
npm run preview
```

---

## 🎨 Key Components

### **1. Authentication Context**

```typescript
// context/AuthContext.tsx
interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  sessionToken: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>(undefined!);

export const AuthProvider: React.FC<{children: React.ReactNode}> = ({children}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  
  const login = async (username: string, password: string) => {
    const response = await authApi.login(username, password);
    setSessionToken(response.session_token);
    setIsAuthenticated(true);
    localStorage.setItem('sessionToken', response.session_token);
  };
  
  return (
    <AuthContext.Provider value={{isAuthenticated, user, sessionToken, login, logout}}>
      {children}
    </AuthContext.Provider>
  );
};
```

### **2. API Client Setup**

```typescript
// api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: import.meta.env.VITE_API_TIMEOUT,
});

// Add session token to all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('sessionToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### **3. Main Dashboard Page**

```typescript
// pages/admin/Dashboard.tsx
const Dashboard: React.FC = () => {
  const [kpiData, setKpiData] = useState<KPIRecord[]>([]);
  const [attendanceRate, setAttendanceRate] = useState(0);
  const [emotionScore, setEmotionScore] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const kpi = await kpiApi.getKPI();
        const attendance = await attendanceApi.getAttendanceRate();
        
        setKpiData(kpi);
        setAttendanceRate(attendance.rate);
        setEmotionScore(attendance.emotionScore);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <Loading />;

  return (
    <Layout>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard title="Attendance" value={`${attendanceRate.toFixed(1)}%`} />
        <MetricCard title="Emotion Score" value={`${emotionScore.toFixed(1)}/100`} />
        <MetricCard title="Total Employees" value={kpiData.length} />
      </div>
      
      <KPIChart data={kpiData} />
      <KPITable data={kpiData} />
    </Layout>
  );
};
```

### **4. Emotion Analytics Component**

```typescript
// components/Dashboard/EmotionChart.tsx
const EmotionChart: React.FC<{data: EmotionLog[]}> = ({data}) => {
  const emotionCounts = useMemo(() => {
    const counts: {[key: string]: number} = {};
    data.forEach(log => {
      counts[log.emotion] = (counts[log.emotion] || 0) + 1;
    });
    return Object.entries(counts).map(([emotion, count]) => ({
      emotion,
      count,
      percentage: (count / data.length * 100).toFixed(1)
    }));
  }, [data]);

  return (
    <BarChart data={emotionCounts}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="emotion" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Bar dataKey="count" fill="#8884d8" name="Count" />
      <Bar dataKey="percentage" fill="#82ca9d" name="Percentage %" />
    </BarChart>
  );
};
```

### **5. User Management Table**

```typescript
// pages/admin/Users.tsx
const Users: React.FC = () => {
  const [users, setUsers] = useState<Nguoi[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [showForm, setShowForm] = useState(false);

  const columns: TableColumn[] = [
    { header: 'ID', render: (row) => row.id },
    { header: 'Name', render: (row) => row.full_name },
    { header: 'Role', render: (row) => row.role },
    { header: 'Shift', render: (row) => row.shift },
    { header: 'Status', render: (row) => <Badge>{row.status}</Badge> },
    { 
      header: 'Actions', 
      render: (row) => (
        <>
          <Button onClick={() => handleEdit(row)}>Edit</Button>
          <Button onClick={() => handleDelete(row.id)}>Delete</Button>
        </>
      )
    }
  ];

  return (
    <Layout>
      <Button onClick={() => setShowForm(true)}>Add User</Button>
      
      {showForm && <UserForm onClose={() => setShowForm(false)} />}
      
      <Table columns={columns} data={users} onPageChange={setPage} />
    </Layout>
  );
};
```

---

## 🔌 API Integration

### **Attendance Endpoints Used**

```typescript
// api/attendance.api.ts
export const attendanceApi = {
  // Get attendance logs
  getChecklog: async (params: {
    user_id?: number;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }) => {
    const response = await apiClient.get('/checklog', {params});
    return response.data;
  },

  // Get attendance rate
  getAttendanceRate: async () => {
    const logs = await attendanceApi.getChecklog({limit: 1000});
    const presentDays = logs.filter(l => l.status === 'present').length;
    return {
      rate: (presentDays / logs.length * 100)
    };
  },

  // Check-in
  checkin: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/checkin', formData);
  }
};
```

### **Emotion Analytics Endpoints**

```typescript
// api/emotion.api.ts
export const emotionApi = {
  // Query emotion logs with filters
  queryEmotions: async (params: {
    user_id?: number;
    emotion_type?: string;
    start_ts?: string;
    end_ts?: string;
    limit?: number;
    offset?: number;
  }) => {
    const response = await apiClient.get('/emotion', {params});
    return response.data.records;
  },

  // Get emotion statistics
  getEmotionStats: async (userId?: number) => {
    const logs = await emotionApi.queryEmotions({
      user_id: userId,
      limit: 1000
    });
    
    const stats: {[key: string]: number} = {};
    logs.forEach(log => {
      stats[log.emotion_type] = (stats[log.emotion_type] || 0) + 1;
    });
    
    return stats;
  }
};
```

### **KPI Endpoints**

```typescript
// api/kpi.api.ts
export const kpiApi = {
  // Get KPI for all users
  getKPI: async (params?: {
    start_date?: string;
    end_date?: string;
  }) => {
    const response = await apiClient.get('/kpi', {params});
    return response.data;
  },

  // Get KPI for specific user
  getUserKPI: async (userId: number, period: 'day' | 'week' | 'month' = 'month') => {
    const response = await apiClient.get(`/kpi/user/${userId}`, {
      params: {period}
    });
    return response.data;
  }
};
```

---

## ✨ Features

### **Admin Dashboard**
- Real-time KPI overview
- Employee list with filtering
- Attendance statistics
- Emotion analytics
- System health status

### **Attendance Tracking**
- Historical attendance logs
- Filter by date range & employee
- Export to CSV/PDF
- Attendance rate calculation

### **Emotion Analytics**
- Emotion distribution charts
- Time-series emotion trends
- Negative emotion alerts
- Emotion score calculation

### **User Management**
- Add/edit/delete employees
- Avatar upload
- Shift assignment
- Role management
- Bulk import (Excel)

### **Embedding Management**
- View stored face embeddings
- Upload new embeddings
- Delete embeddings
- Index statistics

---

## 🚀 Deployment

### **Docker Deployment**

```dockerfile
# Dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### **Build & Run**

```bash
docker build -t dashboard:latest .
docker run -p 80:80 dashboard:latest
```

### **Nginx Configuration**

```nginx
# nginx.conf
server {
  listen 80;
  server_name _;

  location / {
    root /usr/share/nginx/html;
    index index.html;
    try_files $uri $uri/ /index.html;  # SPA routing
  }

  location /api {
    proxy_pass http://api-server:8000;
  }
}
```

---

## 📊 Page Routes

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | Dashboard | Overview & KPIs |
| `/login` | Login | Authentication |
| `/admin/users` | Users | User management |
| `/admin/attendance` | Attendance | Attendance logs |
| `/admin/emotions` | Emotions | Emotion analytics |
| `/admin/embeddings` | Embeddings | Face embedding management |
| `/admin/settings` | Settings | System configuration |
| `/staff/kpi` | KPI | Personal KPI view |

---

---

## 📚 Documentation Files Created

All documentation has been successfully created in the project:

1. **[ARCHITECTURE.md](../face-recognition/ARCHITECTURE.md)** - System design & components
2. **[MODULE_GUIDE.md](../face-recognition/MODULE_GUIDE.md)** - Detailed module descriptions
3. **[WORKFLOW.md](../face-recognition/WORKFLOW.md)** - Execution flows & step-by-step guides
4. **[README.md](../face-recognition/README.md)** - Main project documentation
5. **[IoT README.md](../IOT/README.md)** - Raspberry Pi module guide
6. **[Dashboard README.md](./README.md)** - Frontend dashboard documentation

---

**Last Updated:** December 20, 2025  
**Maintainer:** Development Team

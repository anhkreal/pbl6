import { create } from 'zustand';

interface AuthState {
  token: string | null;
  role: 'admin' | 'staff' | null;
  profile: { id: string; name: string; age?: number; address?: string; phone?: string; } | null;
  login: (token: string, role: 'admin' | 'staff') => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>(set => ({
  token: sessionStorage.getItem('authToken') || null,
  role: (sessionStorage.getItem('userRole') as any) || null,
  profile: null,
  login: (token, role) => {
    sessionStorage.setItem('authToken', token);
    sessionStorage.setItem('userRole', role);
    return set({ token, role });
  },
  logout: () => {
    sessionStorage.clear();
    return set({ token: null, role: null, profile: null });
  }
}));
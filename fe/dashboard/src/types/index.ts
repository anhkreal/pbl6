export interface EmotionLog { id: string; staffId: string; staffName: string; timestamp: number; emotion: string; imageThumb: string; }
export interface AttendanceRecord { id: string; staffId: string; staffName: string; date: string; checkIn?: number; checkOut?: number; workHours?: number; shift: 'day' | 'night'; status: 'late' | 'early_leave' | 'working' | 'normal' | 'absent'; }
export interface KPIRecord { staffId: string; staffName: string; dateOrMonth: string; attendanceScore: number; emotionScore: number; totalScore: number; }
export interface Employee { id: string; name: string; age?: number; address?: string; phone?: string; shift: 'day' | 'night'; active: boolean; avatarThumb?: string; }

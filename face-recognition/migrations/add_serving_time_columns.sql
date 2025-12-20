-- Migration: Add serving_time and no_serving_count to shift_attendance table
-- Date: 2025-12-20
-- Purpose: Track customer serving status for KPI calculation

-- Add serving_time column (TINYINT(1) used for MySQL BOOLEAN)
ALTER TABLE shift_attendance 
ADD COLUMN IF NOT EXISTS serving_time TINYINT(1) DEFAULT 0 
COMMENT 'True khi nhân viên đang phục vụ khách hàng';

ALTER TABLE shift_attendance 
ADD COLUMN IF NOT EXISTS no_serving_count INT DEFAULT 0 
COMMENT 'Đếm số lần liên tiếp không phát hiện isServing (reset về 0 sau 2 lần)';

-- Create index for better query performance (MySQL 8.0+ supports IF NOT EXISTS)
CREATE INDEX IF NOT EXISTS idx_shift_attendance_serving 
ON shift_attendance(user_id, date, shift, serving_time);

-- Verify the changes
DESCRIBE shift_attendance;

/*
Expected columns after migration:
- id
- user_id
- date
- shift
- absence_count
- last_seen
- serving_time (NEW)
- no_serving_count (NEW)
- updated_at
*/

-- NOTE: This file contains only SQL. Use MySQL client to execute it.

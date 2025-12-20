from datetime import time

# Single source of truth for shift times
SHIFT_DAY_START = time(8, 0, 0)
SHIFT_DAY_END = time(14, 0, 0)
SHIFT_NIGHT_START = time(14, 0, 0)
SHIFT_NIGHT_END = time(20, 0, 0)

def get_shift_by_time(t):
    if SHIFT_DAY_START <= t < SHIFT_DAY_END:
        return 'day'
    if SHIFT_NIGHT_START <= t < SHIFT_NIGHT_END:
        return 'night'
    return 'none'

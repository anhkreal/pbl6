# Import shift configuration from config.py
# Single source of truth for shift times
try:
    from config import (
        SHIFT_DAY_START,
        SHIFT_DAY_END,
        SHIFT_NIGHT_START,
        SHIFT_NIGHT_END,
        GRACE_PERIOD_MINUTES,
        ABSENCE_THRESHOLD_SECONDS,
        INCREMENT_INTERVAL_SECONDS
    )
except ImportError:
    # Fallback to default values if config.py is not available
    from datetime import time
    SHIFT_DAY_START = time(8, 0, 0)
    SHIFT_DAY_END = time(14, 0, 0)
    SHIFT_NIGHT_START = time(14, 0, 0)
    SHIFT_NIGHT_END = time(20, 0, 0)
    GRACE_PERIOD_MINUTES = 30
    ABSENCE_THRESHOLD_SECONDS = 30
    INCREMENT_INTERVAL_SECONDS = 10

def get_shift_by_time(t):
    """Determine which shift a given time belongs to.
    
    Args:
        t: time object to check
        
    Returns:
        'day' if in day shift, 'night' if in night shift, 'none' otherwise
    """
    if SHIFT_DAY_START <= t < SHIFT_DAY_END:
        return 'day'
    if SHIFT_NIGHT_START <= t < SHIFT_NIGHT_END:
        return 'night'
    return 'none'

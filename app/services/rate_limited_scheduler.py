import time
from datetime import datetime, timedelta
from app.services.advanced_scheduler import advanced_scheduler
import logging

logger = logging.getLogger(__name__)

class RateLimitedScheduler:
    def __init__(self):
        self.last_generation = {}
        self.min_interval_minutes = 30  # Minimum 30 minutes between generations
        
    def safe_add_job(self, job_id: str, schedule_type: str, **kwargs):
        """Add job with rate limiting checks"""
        
        # Check if interval is too frequent
        if schedule_type == "interval":
            hours = kwargs.get('hours', kwargs.get('hour', 1))
            if hours < 0.5:  # Less than 30 minutes
                logger.warning(f"⚠️ Interval too frequent for {job_id}: {hours} hours. Minimum is 0.5 hours")
                return False, "Minimum interval is 30 minutes for safety"
        
        # Add the job
        success = advanced_scheduler.add_custom_schedule(job_id, schedule_type, 
                                                       advanced_scheduler.generate_scheduled_blog, **kwargs)
        
        if success:
            return True, f"Job {job_id} added successfully with rate limiting"
        else:
            return False, "Failed to add job"

# Global rate-limited scheduler
rate_limited_scheduler = RateLimitedScheduler()

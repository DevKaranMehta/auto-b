from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.services.advanced_scheduler import advanced_scheduler

router = APIRouter()

@router.get("/scheduler/jobs")
async def get_jobs_api():
    """Get all scheduled jobs as JSON for the frontend"""
    try:
        jobs = advanced_scheduler.list_jobs()
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@router.post("/scheduler/quick-schedule")
async def quick_schedule_job(
    job_type: str = Form(...),
    schedule_type: str = Form(...),
    hour: int = Form(9),
    minute: int = Form(0),
    day_of_week: int = Form(1),
    day: int = Form(1),
    cron_expression: str = Form(""),
    description: str = Form(""),
    custom_minutes_value: int = Form(10),  # NEW: Custom minutes input
    db: Session = Depends(get_db)
):
    """Quick schedule a job with predefined templates including minutes support"""
    try:
        # Job function mapping
        job_functions = {
            'trending_topics': advanced_scheduler.update_trending_topics_only,
            'blog_generation': advanced_scheduler.generate_blog_only,
            'cleanup': lambda: print("🧹 Database cleanup executed"),
            'newsletter': lambda: print("📧 Newsletter digest sent")
        }
        
        job_func = job_functions.get(job_type)
        if not job_func:
            return RedirectResponse(url="/admin/scheduler?error=Invalid job type", status_code=303)
        
        # Generate job ID
        if schedule_type == "custom_minutes":
            job_id = f"{job_type}_every_{custom_minutes_value}_minutes"
        else:
            job_id = f"{job_type}_{schedule_type}_{hour}_{minute}"
        
        # Generate description if not provided
        if not description:
            descriptions = {
                'trending_topics': f"🔥 Update trending topics - {schedule_type}",
                'blog_generation': f"📝 Generate blog posts - {schedule_type}",
                'cleanup': f"🧹 Database cleanup - {schedule_type}",
                'newsletter': f"📧 Newsletter digest - {schedule_type}"
            }
            if schedule_type == "custom_minutes":
                descriptions[job_type] = f"{descriptions[job_type].split(' - ')[0]} - every {custom_minutes_value} minutes"
            description = descriptions.get(job_type, f"Job: {job_type}")
        
        # Schedule based on type
        success = False
        
        # ENHANCED: Minute-based scheduling
        if schedule_type == "every_1_minute":
            success = advanced_scheduler.add_minute_interval_job(job_id, job_func, 1, description=description)
        elif schedule_type == "every_2_minutes":
            success = advanced_scheduler.add_minute_interval_job(job_id, job_func, 2, description=description)
        elif schedule_type == "every_3_minutes":
            success = advanced_scheduler.add_minute_interval_job(job_id, job_func, 3, description=description)
        elif schedule_type == "every_5_minutes":
            success = advanced_scheduler.add_minute_interval_job(job_id, job_func, 5, description=description)
        elif schedule_type == "every_10_minutes":
            success = advanced_scheduler.add_minute_interval_job(job_id, job_func, 10, description=description)
        elif schedule_type == "every_15_minutes":
            success = advanced_scheduler.add_minute_interval_job(job_id, job_func, 15, description=description)
        elif schedule_type == "every_20_minutes":
            success = advanced_scheduler.add_minute_interval_job(job_id, job_func, 20, description=description)
        elif schedule_type == "every_30_minutes":
            success = advanced_scheduler.add_minute_interval_job(job_id, job_func, 30, description=description)
        elif schedule_type == "custom_minutes":
            # NEW: Custom minutes input
            if 1 <= custom_minutes_value <= 1440:  # 1 minute to 24 hours
                success = advanced_scheduler.add_minute_interval_job(job_id, job_func, custom_minutes_value, description=description)
            else:
                return RedirectResponse(url="/admin/scheduler?error=Minutes must be between 1 and 1440", status_code=303)
        elif schedule_type == "hourly":
            success = advanced_scheduler.add_interval_job(job_id, job_func, hours=1, description=description)
        elif schedule_type == "every_2_hours":
            success = advanced_scheduler.add_interval_job(job_id, job_func, hours=2, description=description)
        elif schedule_type == "every_4_hours":
            success = advanced_scheduler.add_interval_job(job_id, job_func, hours=4, description=description)
        elif schedule_type == "every_6_hours":
            success = advanced_scheduler.add_interval_job(job_id, job_func, hours=6, description=description)
        elif schedule_type == "every_12_hours":
            success = advanced_scheduler.add_interval_job(job_id, job_func, hours=12, description=description)
        elif schedule_type == "daily":
            success = advanced_scheduler.add_cron_job(job_id, job_func, hour=hour, minute=minute, description=description)
        elif schedule_type == "weekly":
            success = advanced_scheduler.add_cron_job(job_id, job_func, day_of_week=day_of_week, hour=hour, minute=minute, description=description)
        elif schedule_type == "monthly":
            success = advanced_scheduler.add_cron_job(job_id, job_func, day=day, hour=hour, minute=minute, description=description)
        elif schedule_type == "custom_cron" and cron_expression:
            # Parse custom cron expression
            parts = cron_expression.split()
            if len(parts) == 5:
                success = advanced_scheduler.add_cron_job(
                    job_id, job_func,
                    minute=parts[0], hour=parts[1], day=parts[2], month=parts[3], day_of_week=parts[4],
                    description=description
                )
        
        if success:
            return RedirectResponse(url="/admin/scheduler?success=Job scheduled successfully", status_code=303)
        else:
            return RedirectResponse(url="/admin/scheduler?error=Failed to schedule job", status_code=303)
        
    except Exception as e:
        return RedirectResponse(url=f"/admin/scheduler?error={str(e)}", status_code=303)

@router.post("/scheduler/add-job")
async def add_custom_job(
    job_id: str = Form(...),
    job_function: str = Form(...),
    schedule_type: str = Form(...),
    minutes: int = Form(60),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    """Add a custom job with manual configuration including minutes support"""
    try:
        # Job function mapping
        functions = {
            'update_trending_topics_only': advanced_scheduler.update_trending_topics_only,
            'generate_blog_only': advanced_scheduler.generate_blog_only
        }
        
        job_func = functions.get(job_function)
        if not job_func:
            return RedirectResponse(url="/admin/scheduler?error=Invalid job function", status_code=303)
        
        success = False
        if schedule_type == "interval":
            # ENHANCED: Support minute-based intervals
            if minutes >= 60:
                hours = minutes // 60
                success = advanced_scheduler.add_interval_job(job_id, job_func, hours=hours, description=description)
            else:
                # Use minute intervals for values under 60
                success = advanced_scheduler.add_minute_interval_job(job_id, job_func, minutes, description=description)
        
        if success:
            return RedirectResponse(url="/admin/scheduler?success=Custom job added successfully", status_code=303)
        else:
            return RedirectResponse(url="/admin/scheduler?error=Failed to add custom job", status_code=303)
        
    except Exception as e:
        return RedirectResponse(url=f"/admin/scheduler?error={str(e)}", status_code=303)

@router.post("/scheduler/remove-job")
async def remove_job(
    job_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Remove a scheduled job"""
    try:
        success = advanced_scheduler.remove_job(job_id)
        
        if success:
            return RedirectResponse(url="/admin/scheduler?success=Job removed successfully", status_code=303)
        else:
            return RedirectResponse(url="/admin/scheduler?error=Failed to remove job", status_code=303)
        
    except Exception as e:
        return RedirectResponse(url=f"/admin/scheduler?error={str(e)}", status_code=303)

import sys
import os
import asyncio
sys.path.append('.')

def fix_scheduler_jobs():
    """Safely clear all jobs and reinitialize scheduler"""
    try:
        print("🔄 Starting scheduler fix...")
        
        # Import the scheduler
        from app.services.advanced_scheduler import advanced_scheduler
        
        # SAFE STOP: Check if scheduler is running before stopping
        try:
            if hasattr(advanced_scheduler, 'scheduler') and advanced_scheduler.scheduler:
                # Check if scheduler is actually running
                if hasattr(advanced_scheduler.scheduler, 'running') and advanced_scheduler.scheduler.running:
                    print("📋 Scheduler is running, attempting to stop...")
                    advanced_scheduler.scheduler.shutdown(wait=False)
                    print("✅ Scheduler stopped successfully")
                else:
                    print("⚠️ Scheduler not running, skipping stop")
            else:
                print("⚠️ No scheduler instance found, skipping stop")
        except Exception as stop_error:
            print(f"⚠️ Error stopping scheduler (continuing anyway): {stop_error}")
        
        print("🚀 Creating new scheduler instance...")
        
        # Create completely new scheduler instance
        from app.services.advanced_scheduler import AdvancedBlogScheduler
        new_scheduler = AdvancedBlogScheduler()
        
        # Start the new scheduler
        new_scheduler.start()
        
        print("✅ New scheduler started successfully!")
        
        # List current jobs to verify
        jobs = new_scheduler.list_jobs()
        print(f"\n�� Active jobs after fix ({len(jobs)}):")
        for job in jobs:
            print(f"   • {job['id']}: {job.get('description', 'No description')}")
        
        # Update the global reference
        import app.services.advanced_scheduler as scheduler_module
        scheduler_module.advanced_scheduler = new_scheduler
        
        print("\n✅ Scheduler fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing scheduler: {e}")
        print("🔄 Attempting alternative fix...")
        
        # Alternative: Just restart the application
        print("💡 Please restart your application with: python run.py")
        return False

if __name__ == "__main__":
    fix_scheduler_jobs()

import sys
import os
sys.path.append('.')

def create_correct_jobs():
    """Create jobs with correct function assignments - FIXED VERSION"""
    try:
        from app.services.advanced_scheduler import advanced_scheduler
        
        print("🔄 Ensuring scheduler is started...")
        
        # Ensure scheduler is started first
        if not advanced_scheduler._is_started:
            advanced_scheduler.start()
            print("✅ Scheduler started")
        else:
            print("✅ Scheduler already running")
        
        print("🗑️ Stopping all existing jobs...")
        
        # Get all current jobs and remove them
        try:
            current_jobs = advanced_scheduler.scheduler.get_jobs()
            for job in current_jobs:
                try:
                    advanced_scheduler.scheduler.remove_job(job.id)
                    print(f"❌ Removed job: {job.id}")
                except Exception as e:
                    print(f"⚠️ Error removing job {job.id}: {e}")
            
            # Clear the internal jobs tracking
            advanced_scheduler.jobs.clear()
            print("✅ All jobs removed")
        except Exception as e:
            print(f"⚠️ Error during job removal: {e}")
        
        print("🚀 Adding correct jobs with explicit functions...")
        
        # Add TRENDING TOPICS job - ONLY updates topics
        try:
            job1 = advanced_scheduler.scheduler.add_job(
                advanced_scheduler.update_trending_topics_only,
                'interval',
                hours=2,
                id='trending_topics_updater',
                replace_existing=True
            )
            
            # Store job info manually
            advanced_scheduler.jobs['trending_topics_updater'] = {
                'job': job1,
                'type': 'interval',
                'trigger': {'hours': 2},
                'description': "🔥 Update Trending Topics with AI (NO blogs)"
            }
            
            print("✅ Added trending topics updater job")
        except Exception as e:
            print(f"❌ Failed to add trending topics job: {e}")
        
        # Add BLOG GENERATION job - ONLY generates blogs  
        try:
            job2 = advanced_scheduler.scheduler.add_job(
                advanced_scheduler.generate_blog_only,
                'interval',
                hours=4,
                id='blog_generator',
                replace_existing=True
            )
            
            # Store job info manually
            advanced_scheduler.jobs['blog_generator'] = {
                'job': job2,
                'type': 'interval',
                'trigger': {'hours': 4},
                'description': "📝 Generate Blogs from Topics (NO topic updates)"
            }
            
            print("✅ Added blog generator job")
        except Exception as e:
            print(f"❌ Failed to add blog generator job: {e}")
        
        # Verify the jobs
        print("\n📊 Current jobs after fix:")
        try:
            jobs = advanced_scheduler.scheduler.get_jobs()
            for job in jobs:
                job_info = advanced_scheduler.jobs.get(job.id, {})
                description = job_info.get('description', f'Job: {job.id}')
                next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'Not scheduled'
                print(f"   • {job.id}: {description}")
                print(f"     Next run: {next_run}")
        except Exception as e:
            print(f"⚠️ Error listing jobs: {e}")
        
        total_jobs = len(advanced_scheduler.scheduler.get_jobs())
        print(f"\n✅ Job creation complete! {total_jobs} jobs active")
        return True
        
    except Exception as e:
        print(f"❌ Error creating jobs: {e}")
        return False

if __name__ == "__main__":
    create_correct_jobs()

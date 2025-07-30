from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from datetime import datetime, timedelta
import random
import asyncio
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models.blog import Blog, TrendingTopic
from app.services.ai_service import AIContentService

class AdvancedBlogScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.ai_service = AIContentService()
        self.jobs = {}  # Track active jobs
        self._is_started = False
        
    def start(self):
        """Start the scheduler safely"""
        try:
            if not self._is_started:
                self.scheduler.start()
                self._is_started = True
                logger.info("🤖 Advanced AI Blog Scheduler started successfully!")
                
                # Ensure tables exist before starting
                self._ensure_tables_exist()
                
                # CLEAR existing jobs first
                self._clear_existing_jobs()
                
                # Add default jobs with CORRECT functions
                self.add_default_schedules()
            else:
                logger.info("⚠️ Scheduler already started")
        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {e}")
    
    def _clear_existing_jobs(self):
        """Clear any existing jobs to prevent conflicts"""
        try:
            existing_jobs = self.scheduler.get_jobs()
            for job in existing_jobs:
                self.scheduler.remove_job(job.id)
                logger.info(f"🗑️ Cleared existing job: {job.id}")
            self.jobs.clear()
        except Exception as e:
            logger.warning(f"⚠️ Error clearing jobs: {e}")
    
    def stop(self):
        """Stop the scheduler safely"""
        try:
            if self._is_started and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                self._is_started = False
                logger.info("🛑 Advanced Blog Scheduler stopped")
            else:
                logger.info("⚠️ Scheduler not running or already stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
            self._is_started = False
    
    def _ensure_tables_exist(self):
        """Ensure database tables exist"""
        try:
            inspector = inspect(engine)
            
            if not inspector.has_table('trending_topics'):
                logger.info("📊 Creating missing database tables...")
                from app.models.blog import Base
                Base.metadata.create_all(bind=engine)
                logger.info("✅ Database tables created successfully")
            
            db = SessionLocal()
            topic_count = db.query(TrendingTopic).count()
            if topic_count == 0:
                logger.info("🔄 Adding initial trending topics...")
                self._add_initial_topics(db)
            db.close()
            
        except Exception as e:
            logger.error(f"❌ Error ensuring tables exist: {e}")
    
    def _add_initial_topics(self, db):
        """Add initial trending topics to database"""
        try:
            initial_topics = [
                "Modular Blockchain Architecture Development",
                "Zero-Knowledge Proofs at Scale Implementation", 
                "Real-World Asset Tokenization Growth",
                "AI and Blockchain Infrastructure Integration",
                "DeFi Evolution and Traditional Finance Convergence"
            ]
            
            for topic_text in initial_topics:
                topic = TrendingTopic(
                    topic=topic_text,
                    relevance_score=random.randint(75, 95),
                    search_volume=random.randint(2000, 8000),
                    created_at=datetime.now()
                )
                db.add(topic)
            
            db.commit()
            logger.info("✅ Initial trending topics added")
            
        except Exception as e:
            logger.error(f"❌ Error adding initial topics: {e}")
            db.rollback()
    
    def add_default_schedules(self):
        """FIXED: Add correct default jobs - NO LEGACY FUNCTIONS"""
        logger.info("📋 Adding correct scheduled jobs...")
        
        # JOB 1: ONLY Update trending topics - calls update_trending_topics_only()
        try:
            self.add_interval_job(
                "trending_topics_updater",
                self.update_trending_topics_only,  # DIRECT CALL - NO LEGACY
                hours=2,
                description="🔥 Update Trending Topics with AI (NO blogs)"
            )
            logger.info("✅ Added trending topics updater job")
        except Exception as e:
            logger.error(f"❌ Failed to add trending topics job: {e}")
        
        # JOB 2: ONLY Generate blogs - calls generate_blog_only()
        try:
            self.add_interval_job(
                "blog_generator",
                self.generate_blog_only,  # DIRECT CALL - NO LEGACY
                hours=4,
                description="📝 Generate Blogs from Topics (NO topic updates)"
            )
            logger.info("✅ Added blog generator job")
        except Exception as e:
            logger.error(f"❌ Failed to add blog generator job: {e}")
        
        logger.info("✅ Correct default jobs added successfully")
    
    def add_interval_job(self, job_id: str, func, **interval_kwargs):
        """Add an interval job safely"""
        description = interval_kwargs.pop('description', f'Interval job: {job_id}')
        
        try:
            # Remove existing job if it exists
            if job_id in self.jobs:
                try:
                    self.scheduler.remove_job(job_id)
                except:
                    pass
            
            trigger = IntervalTrigger(**interval_kwargs)
            
            job = self.scheduler.add_job(
                func,
                trigger,
                id=job_id,
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                'job': job,
                'type': 'interval',
                'trigger': interval_kwargs,
                'next_run': job.next_run_time,
                'description': description
            }
            
            logger.info(f"✅ Added interval job '{job_id}': {description}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add interval job '{job_id}': {e}")
            return False
    
    def add_minute_interval_job(self, job_id: str, func, minutes: int, **kwargs):
        """Add a job that runs every X minutes"""
        description = kwargs.pop('description', f'Interval job every {minutes} minutes: {job_id}')
        
        try:
            if job_id in self.jobs:
                try:
                    self.scheduler.remove_job(job_id)
                except:
                    pass
            
            trigger = IntervalTrigger(minutes=minutes)
            
            job = self.scheduler.add_job(
                func,
                trigger,
                id=job_id,
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                'job': job,
                'type': 'interval',
                'trigger': {'minutes': minutes},
                'next_run': job.next_run_time,
                'description': description
            }
            
            logger.info(f"✅ Added minute interval job '{job_id}': {description}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add minute interval job '{job_id}': {e}")
            return False
    
    def add_cron_job(self, job_id: str, func, **cron_kwargs):
        """Add a cron job with flexible scheduling"""
        description = cron_kwargs.pop('description', f'Cron job: {job_id}')
        
        try:
            if job_id in self.jobs:
                try:
                    self.scheduler.remove_job(job_id)
                except:
                    pass
            
            trigger = CronTrigger(**cron_kwargs)
            
            job = self.scheduler.add_job(
                func,
                trigger,
                id=job_id,
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                'job': job,
                'type': 'cron',
                'trigger': cron_kwargs,
                'next_run': job.next_run_time,
                'description': description
            }
            
            logger.info(f"✅ Added cron job '{job_id}': {description}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add cron job '{job_id}': {e}")
            return False
    
    def add_custom_schedule(self, job_id: str, schedule_type: str, func, **kwargs):
        """Add custom schedule based on type"""
        if schedule_type == 'hourly':
            return self.add_cron_job(job_id, func, hour='*', minute=0, **kwargs)
        elif schedule_type == 'daily':
            hour = kwargs.get('hour', 9)
            minute = kwargs.get('minute', 0)
            return self.add_cron_job(job_id, func, hour=hour, minute=minute, **kwargs)
        elif schedule_type == 'weekly':
            day_of_week = kwargs.get('day_of_week', 1)  # Monday
            hour = kwargs.get('hour', 9)
            minute = kwargs.get('minute', 0)
            return self.add_cron_job(job_id, func, day_of_week=day_of_week, hour=hour, minute=minute, **kwargs)
        elif schedule_type == 'monthly':
            day = kwargs.get('day', 1)
            hour = kwargs.get('hour', 9)
            minute = kwargs.get('minute', 0)
            return self.add_cron_job(job_id, func, day=day, hour=hour, minute=minute, **kwargs)
        elif schedule_type == 'interval':
            hours = kwargs.get('hours', kwargs.get('hour', 1))
            return self.add_interval_job(job_id, func, hours=hours, **kwargs)
        else:
            logger.error(f"Unknown schedule type: {schedule_type}")
            return False
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job safely"""
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                logger.info(f"❌ Removed job '{job_id}'")
                return True
            else:
                try:
                    self.scheduler.remove_job(job_id)
                    return True
                except:
                    pass
        except Exception as e:
            logger.error(f"Error removing job '{job_id}': {e}")
        return False
    
    def list_jobs(self):
        """List all active jobs safely"""
        jobs_info = []
        
        try:
            scheduler_jobs = self.scheduler.get_jobs()
            
            for job in scheduler_jobs:
                job_info = {
                    'id': job.id,
                    'name': job.name or job.id,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'next_run_formatted': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'Not scheduled'
                }
                
                if job.id in self.jobs:
                    stored_job = self.jobs[job.id]
                    job_info.update({
                        'type': stored_job['type'].title(),
                        'description': stored_job['description'],
                        'trigger_info': stored_job['trigger']
                    })
                else:
                    trigger_type = type(job.trigger).__name__
                    if 'Cron' in trigger_type:
                        job_info['type'] = 'Cron'
                    elif 'Interval' in trigger_type:
                        job_info['type'] = 'Interval'
                    else:
                        job_info['type'] = 'Other'
                    
                    job_info['description'] = f"{job_info['type']} job"
                
                jobs_info.append(job_info)
        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
        
        return jobs_info
    
    def generate_blog_only(self):
        """EXPLICIT: Generate a new blog post ONLY - NO LEGACY REDIRECT"""
        try:
            db = SessionLocal()
            logger.info("📝 DIRECT blog generation (no legacy function)")
            
            # Get trending topics
            trending_topics = db.query(TrendingTopic).order_by(
                TrendingTopic.relevance_score.desc()
            ).limit(10).all()
            
            if not trending_topics:
                logger.warning("No trending topics found")
                return
            
            # Select a topic
            available_topics = [
                topic for topic in trending_topics 
                if not topic.last_used or 
                (datetime.now() - topic.last_used).days > 7
            ]
            
            if not available_topics:
                available_topics = trending_topics[:3]
            
            selected_topic = random.choice(available_topics)
            
            # Generate blog content
            blog_data = asyncio.run(self.ai_service.generate_blog_content(
                selected_topic.topic,
                self._get_random_category()
            ))
            
            # Ensure field lengths are within limits
            meta_description = blog_data["meta_description"]
            if len(meta_description) > 300:
                meta_description = meta_description[:297] + "..."
            
            meta_keywords = blog_data["meta_keywords"]
            if len(meta_keywords) > 500:
                meta_keywords = meta_keywords[:497] + "..."
            
            # Create blog post
            new_blog = Blog(
                title=blog_data["title"],
                content=blog_data["content"],
                meta_description=meta_description,
                meta_keywords=meta_keywords,
                slug=blog_data["slug"],
                category=blog_data["category"],
                tags=blog_data["tags"],
                is_published=True,
                is_ai_generated=True,
                ai_prompt=blog_data["ai_prompt"],
                trending_score=selected_topic.relevance_score
            )
            
            db.add(new_blog)
            selected_topic.last_used = datetime.now()
            db.commit()
            
            logger.info(f"✅ DIRECT blog generation: {blog_data['title']}")
            
        except Exception as e:
            logger.error(f"❌ Error in direct blog generation: {e}")
            db.rollback()
        finally:
            db.close()
    
    def update_trending_topics_only(self):
        """EXPLICIT: Update trending topics ONLY - NO LEGACY REDIRECT"""
        try:
            db = SessionLocal()
            logger.info("🔥 DIRECT trending topics update (no legacy function)")
            
            # Generate new topics using AI
            try:
                topics = self.ai_service.generate_trending_topics_sync()
                logger.info(f"📝 AI generated {len(topics)} trending topics")
            except Exception as ai_error:
                logger.error(f"❌ AI generation failed: {ai_error}")
                topics = [
                    "Ethereum Layer 2 Solutions Expansion 2025",
                    "Bitcoin Ordinals and NFT Integration",
                    "DeFi Yield Farming Evolution Strategies",
                    "Central Bank Digital Currency Implementations",
                    "Cross-Chain Bridge Security Improvements"
                ]
                logger.info(f"🔄 Using fallback topics: {len(topics)}")
            
            # Clear old topics
            old_date = datetime.now() - timedelta(days=30)
            deleted_count = db.query(TrendingTopic).filter(
                TrendingTopic.created_at < old_date
            ).delete()
            
            # Add new topics
            added_count = 0
            for topic in topics:
                existing = db.query(TrendingTopic).filter(
                    TrendingTopic.topic.ilike(f"%{topic[:25]}%")
                ).first()
                
                if not existing:
                    new_topic = TrendingTopic(
                        topic=topic,
                        relevance_score=random.randint(70, 100),
                        search_volume=random.randint(1000, 10000),
                        created_at=datetime.now()
                    )
                    db.add(new_topic)
                    added_count += 1
            
            db.commit()
            logger.info(f"✅ DIRECT trending topics update: Added {added_count} topics")
            
        except Exception as e:
            logger.error(f"❌ Error in direct trending topics update: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _get_random_category(self) -> str:
        """Get a random blog category"""
        categories = [
            "Market Analysis", "Technology", "DeFi", "NFTs", 
            "Regulation", "Trading", "Investment", "News"
        ]
        return random.choice(categories)

# Global scheduler instance
advanced_scheduler = AdvancedBlogScheduler()

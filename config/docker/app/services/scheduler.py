from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.blog import Blog, TrendingTopic
from app.services.ai_service import AIContentService

class BlogScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.ai_service = AIContentService()
        
    def start(self):
        """Start the scheduler"""
        # Schedule blog generation every 4 hours
        self.scheduler.add_job(
            self.generate_scheduled_blog,
            CronTrigger(hour="*/4"),  # Every 4 hours
            id="auto_blog_generation",
            replace_existing=True
        )
        
        # Schedule trending topics update daily at 6 AM
        self.scheduler.add_job(
            self.update_trending_topics,
            CronTrigger(hour=6, minute=0),  # Daily at 6 AM
            id="trending_topics_update",
            replace_existing=True
        )
        
        # Schedule content publishing every hour
        self.scheduler.add_job(
            self.publish_scheduled_content,
            CronTrigger(minute=0),  # Every hour
            id="publish_scheduled_content",
            replace_existing=True
        )
        
        self.scheduler.start()
        print("🤖 AI Blog Scheduler started successfully!")
    
    async def generate_scheduled_blog(self):
        """Generate a new blog post automatically"""
        try:
            db = next(get_db())
            
            # Get trending topics
            trending_topics = db.query(TrendingTopic).order_by(
                TrendingTopic.relevance_score.desc()
            ).limit(10).all()
            
            if not trending_topics:
                # Generate new trending topics if none exist
                await self.update_trending_topics()
                trending_topics = db.query(TrendingTopic).limit(5).all()
            
            # Select a random topic that hasn't been used recently
            available_topics = [
                topic for topic in trending_topics 
                if not topic.last_used or 
                (datetime.now() - topic.last_used).days > 7
            ]
            
            if not available_topics:
                available_topics = trending_topics[:3]  # Fallback
            
            selected_topic = random.choice(available_topics)
            
            # Generate content
            blog_data = await self.ai_service.generate_blog_content(
                selected_topic.topic,
                self._get_random_category()
            )
            
            # Create blog post
            new_blog = Blog(
                title=blog_data["title"],
                content=blog_data["content"],
                meta_description=blog_data["meta_description"],
                meta_keywords=blog_data["meta_keywords"],
                slug=blog_data["slug"],
                category=blog_data["category"],
                tags=blog_data["tags"],
                is_published=True,  # Auto-publish
                is_ai_generated=True,
                ai_prompt=blog_data["ai_prompt"],
                trending_score=selected_topic.relevance_score
            )
            
            db.add(new_blog)
            
            # Update topic usage
            selected_topic.last_used = datetime.now()
            
            db.commit()
            
            print(f"✅ Auto-generated blog: {blog_data['title']}")
            
        except Exception as e:
            print(f"❌ Error in scheduled blog generation: {e}")
        finally:
            db.close()
    
    async def update_trending_topics(self):
        """Update trending topics using AI"""
        try:
            db = next(get_db())
            
            # Generate new trending topics
            topics = await self.ai_service.generate_trending_topics()
            
            # Clear old topics (older than 30 days)
            old_date = datetime.now() - timedelta(days=30)
            db.query(TrendingTopic).filter(
                TrendingTopic.created_at < old_date
            ).delete()
            
            # Add new topics
            for topic in topics:
                # Check if topic already exists
                existing = db.query(TrendingTopic).filter(
                    TrendingTopic.topic == topic
                ).first()
                
                if not existing:
                    new_topic = TrendingTopic(
                        topic=topic,
                        relevance_score=random.randint(70, 100),
                        search_volume=random.randint(1000, 10000)
                    )
                    db.add(new_topic)
            
            db.commit()
            print("✅ Trending topics updated")
            
        except Exception as e:
            print(f"❌ Error updating trending topics: {e}")
        finally:
            db.close()
    
    async def publish_scheduled_content(self):
        """Publish content that's scheduled for publishing"""
        try:
            db = next(get_db())
            
            # Find content scheduled for now or earlier
            now = datetime.now()
            scheduled_posts = db.query(Blog).filter(
                Blog.scheduled_publish_date <= now,
                Blog.is_published == False
            ).all()
            
            for post in scheduled_posts:
                post.is_published = True
                post.scheduled_publish_date = None
                print(f"📰 Published scheduled post: {post.title}")
            
            db.commit()
            
        except Exception as e:
            print(f"❌ Error publishing scheduled content: {e}")
        finally:
            db.close()
    
    def _get_random_category(self) -> str:
        """Get a random blog category"""
        categories = [
            "Market Analysis", "Technology", "DeFi", "NFTs", 
            "Regulation", "Trading", "Investment", "News"
        ]
        return random.choice(categories)
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("🛑 Blog Scheduler stopped")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.blog import Blog
from app.models.newsletter import NewsletterSubscription

router = APIRouter()

@router.get("/blogs")
async def get_blogs(limit: int = 10, db: Session = Depends(get_db)):
    """Get latest published blogs"""
    blogs = db.query(Blog).filter(
        Blog.is_published == True
    ).order_by(desc(Blog.created_at)).limit(limit).all()
    
    return {
        "blogs": [
            {
                "id": blog.id,
                "title": blog.title,
                "slug": blog.slug,
                "category": blog.category,
                "created_at": blog.created_at.isoformat(),
                "view_count": blog.view_count
            }
            for blog in blogs
        ]
    }

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get blog statistics"""
    total_blogs = db.query(Blog).count()
    published_blogs = db.query(Blog).filter(Blog.is_published == True).count()
    total_subscribers = db.query(NewsletterSubscription).filter(
        NewsletterSubscription.is_active == True
    ).count()
    
    return {
        "total_blogs": total_blogs,
        "published_blogs": published_blogs,
        "total_subscribers": total_subscribers
    }

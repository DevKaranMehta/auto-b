from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import Optional
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.blog import Blog, TrendingTopic
from app.models.newsletter import NewsletterSubscription
from app.services.ai_service import AIContentService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
ai_service = AIContentService()

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard with statistics"""
    
    # Get statistics
    total_blogs = db.query(func.count(Blog.id)).scalar() or 0
    published_blogs = db.query(func.count(Blog.id)).filter(Blog.is_published == True).scalar() or 0
    total_subscribers = db.query(func.count(NewsletterSubscription.id)).filter(
        NewsletterSubscription.is_active == True
    ).scalar() or 0
    trending_topics_count = db.query(func.count(TrendingTopic.id)).scalar() or 0
    
    # Recent blogs
    recent_blogs = db.query(Blog).order_by(desc(Blog.created_at)).limit(10).all()
    
    # Popular blogs
    popular_blogs = db.query(Blog).filter(
        Blog.is_published == True
    ).order_by(desc(Blog.view_count)).limit(5).all()
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "total_blogs": total_blogs,
            "published_blogs": published_blogs,
            "total_subscribers": total_subscribers,
            "trending_topics_count": trending_topics_count,
            "recent_blogs": recent_blogs,
            "popular_blogs": popular_blogs
        }
    )

@router.get("/blogs", response_class=HTMLResponse)
async def admin_blogs(request: Request, db: Session = Depends(get_db)):
    """Blog management page"""
    blogs = db.query(Blog).order_by(desc(Blog.created_at)).all()
    return templates.TemplateResponse(
        "admin/blogs.html",
        {"request": request, "blogs": blogs}
    )

@router.get("/newsletters", response_class=HTMLResponse)
async def newsletter_management(request: Request, db: Session = Depends(get_db)):
    """Newsletter subscriber management"""
    subscribers = db.query(NewsletterSubscription).order_by(
        desc(NewsletterSubscription.subscribed_at)
    ).all()
    
    return templates.TemplateResponse(
        "admin/newsletters.html",
        {"request": request, "subscribers": subscribers}
    )

@router.get("/ai-generate", response_class=HTMLResponse)
async def ai_generate_form(request: Request, db: Session = Depends(get_db)):
    """AI blog generation form"""
    trending_topics = db.query(TrendingTopic).order_by(
        desc(TrendingTopic.relevance_score)
    ).limit(10).all()
    
    return templates.TemplateResponse(
        "admin/ai_generate.html",
        {"request": request, "trending_topics": trending_topics}
    )

@router.post("/ai-generate")
async def ai_generate_blog(
    topic: str = Form(...),
    category: str = Form("Technology"),
    auto_publish: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Generate blog using AI"""
    try:
        # Generate content
        blog_data = await ai_service.generate_blog_content(topic, category)
        
        new_blog = Blog(
            title=blog_data["title"],
            content=blog_data["content"],
            meta_description=blog_data["meta_description"],
            meta_keywords=blog_data["meta_keywords"],
            slug=blog_data["slug"],
            category=blog_data["category"],
            tags=blog_data["tags"],
            is_published=auto_publish,
            is_ai_generated=True,
            ai_prompt=blog_data["ai_prompt"]
        )
        
        db.add(new_blog)
        db.commit()
        
        return RedirectResponse(url="/admin/blogs", status_code=303)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/scheduler", response_class=HTMLResponse)
async def scheduler_management(request: Request):
    """Scheduler management page"""
    return templates.TemplateResponse(
        "admin/scheduler.html",
        {"request": request}
    )

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func
import sys
import os
import math

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.blog import TrendingTopic

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/trending-topics", response_class=HTMLResponse)
async def trending_topics_page(
    request: Request, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=5, le=100),
    search: str = Query("", description="Search topics"),
    sort_by: str = Query("relevance_score", description="Sort by field"),
    order: str = Query("desc", description="Sort order")
):
    """Trending topics management page with pagination and search"""
    try:
        # Build query with search
        query = db.query(TrendingTopic)
        
        if search:
            query = query.filter(
                or_(
                    TrendingTopic.topic.ilike(f"%{search}%"),
                    func.cast(TrendingTopic.relevance_score, db.String).ilike(f"%{search}%")
                )
            )
        
        # Apply sorting
        if sort_by == "relevance_score":
            if order == "desc":
                query = query.order_by(desc(TrendingTopic.relevance_score))
            else:
                query = query.order_by(TrendingTopic.relevance_score)
        elif sort_by == "created_at":
            if order == "desc":
                query = query.order_by(desc(TrendingTopic.created_at))
            else:
                query = query.order_by(TrendingTopic.created_at)
        elif sort_by == "last_used":
            if order == "desc":
                query = query.order_by(desc(TrendingTopic.last_used))
            else:
                query = query.order_by(TrendingTopic.last_used)
        elif sort_by == "search_volume":
            if order == "desc":
                query = query.order_by(desc(TrendingTopic.search_volume))
            else:
                query = query.order_by(TrendingTopic.search_volume)
        else:
            # Default sorting
            query = query.order_by(desc(TrendingTopic.relevance_score))
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        trending_topics = query.offset(offset).limit(per_page).all()
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / per_page)
        has_prev = page > 1
        has_next = page < total_pages
        prev_page = page - 1 if has_prev else None
        next_page = page + 1 if has_next else None
        
        # Generate page numbers for pagination display
        page_numbers = []
        start_page = max(1, page - 2)
        end_page = min(total_pages, page + 2)
        
        for p in range(start_page, end_page + 1):
            page_numbers.append(p)
        
        # Get statistics for all topics (not just current page)
        all_topics_query = db.query(TrendingTopic)
        if search:
            all_topics_query = all_topics_query.filter(
                or_(
                    TrendingTopic.topic.ilike(f"%{search}%"),
                    func.cast(TrendingTopic.relevance_score, db.String).ilike(f"%{search}%")
                )
            )
        
        all_topics = all_topics_query.all()
        
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_page': prev_page,
            'next_page': next_page,
            'page_numbers': page_numbers,
            'search': search,
            'sort_by': sort_by,
            'order': order
        }
        
        print(f"📊 Retrieved {len(trending_topics)} trending topics from database (page {page}/{total_pages})")
        
        return templates.TemplateResponse(
            "admin/trending_topics.html",
            {
                "request": request,
                "trending_topics": trending_topics,
                "all_topics": all_topics,  # For statistics
                "pagination": pagination_info
            }
        )
    except Exception as e:
        print(f"❌ Error in trending topics page: {e}")
        return templates.TemplateResponse(
            "admin/trending_topics.html",
            {
                "request": request,
                "trending_topics": [],
                "all_topics": [],
                "pagination": {
                    'page': 1, 'per_page': 20, 'total_count': 0, 'total_pages': 0,
                    'has_prev': False, 'has_next': False, 'prev_page': None, 'next_page': None,
                    'page_numbers': [], 'search': '', 'sort_by': 'relevance_score', 'order': 'desc'
                }
            }
        )

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.blog import Blog

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/category/{category}", response_class=HTMLResponse)
async def blogs_by_category(request: Request, category: str, db: Session = Depends(get_db)):
    """Get blogs by category"""
    blogs = db.query(Blog).filter(
        Blog.category == category,
        Blog.is_published == True
    ).order_by(desc(Blog.created_at)).all()
    
    return templates.TemplateResponse(
        "blog/category.html",
        {
            "request": request,
            "blogs": blogs,
            "category": category
        }
    )

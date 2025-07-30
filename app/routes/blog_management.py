from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.blog import Blog
from app.services.ai_service import AIContentService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
ai_service = AIContentService()

@router.get("/blogs/edit/{blog_id}", response_class=HTMLResponse)
async def edit_blog_form(request: Request, blog_id: int, db: Session = Depends(get_db)):
    """Blog edit form"""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    return templates.TemplateResponse(
        "admin/blog_edit.html",
        {"request": request, "blog": blog}
    )

@router.post("/blogs/edit/{blog_id}")
async def update_blog(
    blog_id: int,
    title: str = Form(...),
    content: str = Form(...),
    meta_description: str = Form(""),
    meta_keywords: str = Form(""),
    category: str = Form("Technology"),
    tags: str = Form(""),
    is_published: bool = Form(False),
    is_featured: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Update blog post"""
    try:
        blog = db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        # Update blog fields
        blog.title = title
        blog.content = content
        blog.meta_description = meta_description
        blog.meta_keywords = meta_keywords
        blog.category = category
        blog.tags = tags
        blog.is_published = is_published
        blog.is_featured = is_featured
        
        db.commit()
        
        return RedirectResponse(url="/admin/blogs?success=Blog updated successfully", status_code=303)
        
    except Exception as e:
        return RedirectResponse(url=f"/admin/blogs?error={str(e)}", status_code=303)

@router.post("/blogs/delete/{blog_id}")
async def delete_blog(blog_id: int, db: Session = Depends(get_db)):
    """Delete blog post"""
    try:
        blog = db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        db.delete(blog)
        db.commit()
        
        return RedirectResponse(url="/admin/blogs?success=Blog deleted successfully", status_code=303)
        
    except Exception as e:
        return RedirectResponse(url=f"/admin/blogs?error={str(e)}", status_code=303)

@router.post("/blogs/ai-generate-meta")
async def ai_generate_meta(
    field: str = Form(...),  # title, description, keywords
    current_content: str = Form(""),
    blog_title: str = Form(""),
    blog_category: str = Form("Technology"),
    db: Session = Depends(get_db)
):
    """Generate AI content for specific meta fields"""
    try:
        if field == "title":
            new_content = await ai_service.generate_seo_title(current_content, blog_category)
        elif field == "description":
            new_content = await ai_service.generate_meta_description(blog_title, current_content)
        elif field == "keywords":
            new_content = await ai_service.generate_meta_keywords(blog_title, current_content, blog_category)
        else:
            raise ValueError("Invalid field specified")
        
        return JSONResponse({"success": True, "content": new_content})
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

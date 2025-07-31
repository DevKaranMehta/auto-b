from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/blogs", response_class=HTMLResponse)
@router.head("/admin/blogs")
async def blogs_management(request: Request, db: Session = Depends(get_db)):
    try:
        # Try to get blog data from blog_posts table
        blog_data = []
        blog_count = 0
        total_count = 0
        table_used = "blog_posts"
        
        try:
            # Get blog posts
            result = db.execute(text("""
                SELECT id, title, 
                       COALESCE(LEFT(content, 100), LEFT(summary, 100), 'No content') as content_preview,
                       created_at, 
                       COALESCE(published, false) as published,
                       COALESCE(status, 'draft') as status
                FROM blog_posts 
                ORDER BY created_at DESC 
                LIMIT 20
            """))
            blog_data = result.fetchall()
            blog_count = len(blog_data)
            
            # Get total count
            result = db.execute(text("SELECT COUNT(*) as count FROM blog_posts"))
            total_count = result.fetchone().count
            
        except Exception as e:
            print(f"Error fetching blog_posts: {e}")
            # Return empty data but working page
            pass
            
        return templates.TemplateResponse("admin/blogs.html", {
            "request": request,
            "blogs": blog_data,
            "blog_count": blog_count,
            "total_count": total_count,
            "table_used": table_used,
            "title": "Blog Management"
        })
        
    except Exception as e:
        print(f"Blog management error: {str(e)}")
        # Return basic HTML page
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Blog Management</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1>📝 Blog Management</h1>
            <p><a href="/admin/">← Back to Admin Dashboard</a></p>
            <div style="background: #f8d7da; padding: 15px; border-radius: 5px;">
                <p><strong>Error:</strong> {str(e)}</p>
                <p>Database connection or query issue detected.</p>
            </div>
        </body>
        </html>
        """, status_code=200)

@router.get("/admin/blogs/debug")
async def debug_blog_info(db: Session = Depends(get_db)):
    try:
        debug_info = {}
        
        # Check tables
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%blog%'
        """))
        debug_info["blog_tables"] = [row.table_name for row in result.fetchall()]
        
        # Check blog_posts data
        try:
            result = db.execute(text("SELECT COUNT(*) as count FROM blog_posts"))
            debug_info["blog_posts_count"] = result.fetchone().count
            
            result = db.execute(text("""
                SELECT id, title, created_at 
                FROM blog_posts 
                ORDER BY created_at DESC 
                LIMIT 5
            """))
            debug_info["recent_posts"] = [
                {"id": row.id, "title": row.title, "created_at": str(row.created_at)} 
                for row in result.fetchall()
            ]
        except Exception as e:
            debug_info["blog_posts_error"] = str(e)
        
        return JSONResponse(content=debug_info)
        
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

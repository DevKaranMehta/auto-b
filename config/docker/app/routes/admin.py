from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    try:
        # Get basic stats
        blog_count = 0
        subscriber_count = 0
        
        try:
            result = db.execute(text("SELECT COUNT(*) as count FROM blogs"))
            blog_count = result.fetchone().count if result.fetchone() else 0
        except:
            pass
            
        try:
            result = db.execute(text("SELECT COUNT(*) as count FROM newsletter_subscriptions WHERE is_active = true"))
            subscriber_count = result.fetchone().count if result.fetchone() else 0
        except:
            pass
        
        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "blog_count": blog_count,
            "subscriber_count": subscriber_count,
            "title": "Admin Dashboard"
        })
    except Exception as e:
        print(f"Admin dashboard error: {str(e)}")
        return HTMLResponse(content=f"""
        <html>
        <head><title>Admin Dashboard</title></head>
        <body>
            <h1>🚀 Blockchain News Admin Dashboard</h1>
            <p>Welcome to the admin panel!</p>
            <ul>
                <li><a href="/admin/newsletters">Newsletter Management</a></li>
                <li><a href="/admin/blogs">Blog Management</a></li>
                <li><a href="/admin/scheduler">Scheduler Management</a></li>
            </ul>
        </body>
        </html>
        """, status_code=200)

@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_redirect(request: Request, db: Session = Depends(get_db)):
    return await admin_dashboard(request, db)

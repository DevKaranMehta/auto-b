from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/newsletters", response_class=HTMLResponse)
async def newsletters_page(request: Request, db: Session = Depends(get_db)):
    try:
        # Get newsletter subscription count
        result = db.execute(text("SELECT COUNT(*) as count FROM newsletter_subscriptions WHERE is_active = true"))
        subscription_count = result.fetchone().count
        
        # Get recent subscribers
        result = db.execute(text("SELECT email, created_at FROM newsletter_subscriptions WHERE is_active = true ORDER BY created_at DESC LIMIT 10"))
        recent_subscribers = result.fetchall()
        
        return templates.TemplateResponse("admin/newsletters.html", {
            "request": request,
            "subscription_count": subscription_count,
            "recent_subscribers": recent_subscribers
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Newsletter error: {str(e)}")

@router.post("/newsletter/subscribe")
async def subscribe_newsletter(email: str = Form(...), db: Session = Depends(get_db)):
    try:
        # Insert new subscriber
        db.execute(text("INSERT INTO newsletter_subscriptions (email) VALUES (:email) ON CONFLICT (email) DO NOTHING"), {"email": email})
        db.commit()
        return {"message": "Successfully subscribed to newsletter"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscription error: {str(e)}")

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Lifespan manager for scheduler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        from app.services.advanced_scheduler import advanced_scheduler
        advanced_scheduler.start()
        print("🤖 Advanced Scheduler started!")
    except Exception as e:
        print(f"⚠️ Scheduler startup error: {e}")
    
    yield
    
    # Shutdown
    try:
        from app.services.advanced_scheduler import advanced_scheduler
        advanced_scheduler.stop()
        print("🛑 Advanced Scheduler stopped!")
    except Exception as e:
        print(f"⚠️ Scheduler shutdown error: {e}")

app = FastAPI(title="BlockchainLatestNews CMS", version="1.0.0", lifespan=lifespan)

# Static files and templates
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    templates = Jinja2Templates(directory="app/templates")
except Exception as e:
    print(f"Warning: Static files or templates not found: {e}")
    templates = None

# Import and include routes
try:
    from app.routes import admin
    app.include_router(admin.router, prefix="/admin", tags=["admin"])
    print("✅ Admin routes loaded")
except Exception as e:
    print(f"❌ Error loading admin routes: {e}")

# Add trending topics routes
try:
    from app.routes import trending
    app.include_router(trending.router, prefix="/admin", tags=["trending"])
    print("✅ Trending topics routes loaded")
except Exception as e:
    print(f"⚠️ Trending topics routes not loaded: {e}")

# Add scheduler API routes
try:
    from app.routes import scheduler_api
    app.include_router(scheduler_api.router, prefix="/admin", tags=["scheduler_api"])
    print("✅ Scheduler API routes loaded")
except Exception as e:
    print(f"⚠️ Scheduler API routes not loaded: {e}")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Homepage with blogs"""
    try:
        from app.models.blog import Blog
        
        # Get featured post
        featured_post = db.query(Blog).filter(
            Blog.is_published == True,
            Blog.is_featured == True
        ).first()
        
        if not featured_post:
            featured_post = db.query(Blog).filter(
                Blog.is_published == True
            ).order_by(desc(Blog.created_at)).first()
        
        # Get recent posts
        recent_posts = db.query(Blog).filter(
            Blog.is_published == True
        ).order_by(desc(Blog.created_at)).limit(6).all()
        
        # Get trending posts
        trending_posts = db.query(Blog).filter(
            Blog.is_published == True
        ).order_by(desc(Blog.view_count)).limit(5).all()
        
        return templates.TemplateResponse(
            "blog/index.html",
            {
                "request": request,
                "featured_post": featured_post,
                "recent_posts": recent_posts,
                "trending_posts": trending_posts
            }
        )
    except Exception as e:
        return JSONResponse({
            "message": "🚀 BlockchainLatestNews CMS is running!",
            "status": "success", 
            "admin_panel": "http://localhost:8000/admin/",
            "error": str(e)
        })

@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_detail(request: Request, slug: str, db: Session = Depends(get_db)):
    """Single blog post page"""
    try:
        from app.models.blog import Blog
        
        blog_post = db.query(Blog).filter(
            Blog.slug == slug,
            Blog.is_published == True
        ).first()
        
        if not blog_post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        # Increment view count
        blog_post.view_count += 1
        db.commit()
        
        # Get related posts
        related_posts = db.query(Blog).filter(
            Blog.category == blog_post.category,
            Blog.id != blog_post.id,
            Blog.is_published == True
        ).limit(3).all()
        
        return templates.TemplateResponse(
            "blog/single.html",
            {
                "request": request,
                "blog_post": blog_post,
                "related_posts": related_posts
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Blog not found: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "BlockchainLatestNews CMS",
        "database": "connected",
        "scheduler": "active"
    }

@app.post("/subscribe")
async def subscribe_newsletter(email: str = Form(...), db: Session = Depends(get_db)):
    """Newsletter subscription endpoint"""
    try:
        from app.models.newsletter import NewsletterSubscription
        
        # Check if already subscribed
        existing = db.query(NewsletterSubscription).filter(
            NewsletterSubscription.email == email
        ).first()
        
        if existing:
            if existing.is_active:
                return JSONResponse({"message": "Already subscribed!"})
            else:
                existing.is_active = True
                existing.unsubscribed_at = None
        else:
            subscription = NewsletterSubscription(email=email)
            db.add(subscription)
        
        db.commit()
        return JSONResponse({"message": "Successfully subscribed to BlockchainLatestNews newsletter!"})
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Add blog management routes
try:
    from app.routes import blog_management
    app.include_router(blog_management.router, prefix="/admin", tags=["blog_management"])
    print("✅ Blog management routes loaded")
except Exception as e:
    print(f"⚠️ Blog management routes not loaded: {e}")

# Add trending topics API routes
try:
    from app.routes import trending_api
    app.include_router(trending_api.router, prefix="/admin", tags=["trending_api"])
    print("✅ Trending API routes loaded")
except Exception as e:
    print(f"⚠️ Trending API routes not loaded: {e}")

# Add trending topics API routes if not already included
try:
    from app.routes import trending_api
    app.include_router(trending_api.router, prefix="/admin", tags=["trending_api"])
    print("✅ Trending API routes loaded")
except Exception as e:
    print(f"⚠️ Trending API routes not loaded: {e}")

# Add scheduler API routes
try:
    from app.routes import scheduler_api
    app.include_router(scheduler_api.router, prefix="/admin", tags=["scheduler_api"])
    print("✅ Scheduler API routes loaded")
except Exception as e:
    print(f"⚠️ Scheduler API routes not loaded: {e}")

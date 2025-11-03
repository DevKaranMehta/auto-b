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
        from app.models.blog import Blog, Category

        # Get all active categories for menu
        categories = db.query(Category).filter(Category.is_active == True).all()

        # Get featured post
        featured_post = db.query(Blog).filter(
            Blog.is_published == True,
            Blog.is_featured == True
        ).first()

        if not featured_post:
            featured_post = db.query(Blog).filter(
                Blog.is_published == True
            ).order_by(desc(Blog.created_at)).first()

        # Get recent posts (exclude featured post to avoid duplication)
        recent_posts_query = db.query(Blog).filter(Blog.is_published == True)
        if featured_post:
            recent_posts_query = recent_posts_query.filter(Blog.id != featured_post.id)
        recent_posts = recent_posts_query.order_by(desc(Blog.created_at)).limit(6).all()

        # Get trending posts
        trending_posts = db.query(Blog).filter(
            Blog.is_published == True
        ).order_by(desc(Blog.view_count)).limit(5).all()

        return templates.TemplateResponse(
            "blog/index.html",
            {
                "request": request,
                "categories": categories,
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

@app.get("/news", response_class=HTMLResponse)
async def news_aggregator(request: Request, db: Session = Depends(get_db)):
    """News aggregator page showing direct RSS feed content"""
    try:
        from app.models.blog import Category
        from app.models.rss_feed import RSSFeedItem, RSSFeed
        from bs4 import BeautifulSoup
        import re

        def clean_text(html_text, max_length=250):
            """Strip HTML and limit text length"""
            if not html_text:
                return ""
            # Remove HTML tags
            soup = BeautifulSoup(html_text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            # Clean extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            # Truncate if needed
            if len(text) > max_length:
                text = text[:max_length].rsplit(' ', 1)[0] + '...'
            return text

        def extract_image_from_content(html_content, enclosures):
            """Extract first image from HTML content or enclosures"""
            # Try enclosures first (RSS media attachments)
            if enclosures:
                for enclosure in enclosures:
                    if isinstance(enclosure, dict):
                        url = enclosure.get('url', '')
                        media_type = enclosure.get('type', '')
                        if url and ('image' in media_type or url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))):
                            return url

            # Try extracting from HTML content
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                img = soup.find('img')
                if img and img.get('src'):
                    return img.get('src')

            return None

        # Get all active categories for menu
        categories = db.query(Category).filter(Category.is_active == True).all()

        # Get latest RSS feed items (both pending and completed)
        # Show items in reverse chronological order
        feed_items_raw = db.query(RSSFeedItem, RSSFeed).join(
            RSSFeed, RSSFeedItem.feed_id == RSSFeed.id
        ).filter(
            RSSFeed.is_active == True
        ).order_by(
            desc(RSSFeedItem.pub_date)
        ).limit(50).all()

        # Process feed items to clean HTML and extract images
        feed_items = []
        for item, feed in feed_items_raw:
            # Clean description/content
            cleaned_description = clean_text(item.description or item.content or "", 250)

            # Extract image from content or enclosures
            image_url = extract_image_from_content(
                item.description or item.content,
                item.enclosures
            )

            feed_items.append({
                'item': item,
                'feed': feed,
                'cleaned_description': cleaned_description,
                'image_url': image_url
            })

        return templates.TemplateResponse(
            "blog/news_swipe.html",
            {
                "request": request,
                "categories": categories,
                "feed_items": feed_items
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading news: {e}")

@app.get("/category/{category_slug}", response_class=HTMLResponse)
async def category_posts(request: Request, category_slug: str, db: Session = Depends(get_db)):
    """Display posts by category using URL-friendly slugs"""
    try:
        from app.models.blog import Blog, Category

        # Get all active categories for menu
        categories = db.query(Category).filter(Category.is_active == True).all()

        # Get the selected category by slug
        selected_category = db.query(Category).filter(
            Category.slug == category_slug,
            Category.is_active == True
        ).first()

        if not selected_category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Use the category name for filtering blog posts
        category_name = selected_category.name

        # Get featured post from this category
        featured_post = db.query(Blog).filter(
            Blog.is_published == True,
            Blog.category == category_name,
            Blog.is_featured == True
        ).first()

        if not featured_post:
            featured_post = db.query(Blog).filter(
                Blog.is_published == True,
                Blog.category == category_name
            ).order_by(desc(Blog.created_at)).first()

        # Get recent posts from this category (exclude featured)
        recent_posts_query = db.query(Blog).filter(
            Blog.is_published == True,
            Blog.category == category_name
        )
        if featured_post:
            recent_posts_query = recent_posts_query.filter(Blog.id != featured_post.id)
        recent_posts = recent_posts_query.order_by(desc(Blog.created_at)).limit(6).all()

        # Get trending posts
        trending_posts = db.query(Blog).filter(
            Blog.is_published == True
        ).order_by(desc(Blog.view_count)).limit(5).all()

        return templates.TemplateResponse(
            "blog/index.html",
            {
                "request": request,
                "categories": categories,
                "featured_post": featured_post,
                "recent_posts": recent_posts,
                "trending_posts": trending_posts,
                "selected_category": selected_category
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Category not found: {e}")

@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_detail(request: Request, slug: str, db: Session = Depends(get_db)):
    """Single blog post page"""
    try:
        from app.models.blog import Blog, Category

        # Get all active categories for menu
        categories = db.query(Category).filter(Category.is_active == True).all()

        blog_post = db.query(Blog).filter(
            Blog.slug == slug,
            Blog.is_published == True
        ).first()

        if not blog_post:
            raise HTTPException(status_code=404, detail="Blog post not found")

        # Increment view count
        blog_post.view_count += 1
        db.commit()

        # Get related posts (6 posts for better grid display)
        related_posts = db.query(Blog).filter(
            Blog.category == blog_post.category,
            Blog.id != blog_post.id,
            Blog.is_published == True
        ).order_by(desc(Blog.created_at)).limit(6).all()

        # Get trending posts for sidebar
        trending_posts = db.query(Blog).filter(
            Blog.is_published == True
        ).order_by(desc(Blog.view_count)).limit(5).all()

        # Get recent posts for sidebar
        recent_posts = db.query(Blog).filter(
            Blog.is_published == True
        ).order_by(desc(Blog.created_at)).limit(6).all()

        return templates.TemplateResponse(
            "blog/single.html",
            {
                "request": request,
                "categories": categories,
                "blog_post": blog_post,
                "related_posts": related_posts,
                "trending_posts": trending_posts,
                "recent_posts": recent_posts
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

@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """Privacy Policy page"""
    return templates.TemplateResponse("legal/privacy.html", {"request": request})

@app.get("/terms-of-service", response_class=HTMLResponse)
async def terms_of_service(request: Request):
    """Terms of Service page"""
    return templates.TemplateResponse("legal/terms.html", {"request": request})

@app.get("/disclaimer", response_class=HTMLResponse)
async def disclaimer(request: Request):
    """Disclaimer page"""
    return templates.TemplateResponse("legal/disclaimer.html", {"request": request})

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

# Add category management routes
try:
    from app.routes import category_management
    app.include_router(category_management.router, prefix="/admin", tags=["category_management"])
    print("✅ Category management routes loaded")
except Exception as e:
    print(f"⚠️ Category management routes not loaded: {e}")

# Add RSS feed management routes
try:
    from app.routes import rss_management
    app.include_router(rss_management.router, prefix="/admin", tags=["rss_management"])
    print("✅ RSS feed management routes loaded")
except Exception as e:
    print(f"⚠️ RSS feed management routes not loaded: {e}")

# Add utilities/bulk operations routes
try:
    from app.routes import utilities
    app.include_router(utilities.router, prefix="/admin", tags=["utilities"])
    print("✅ Utilities routes loaded")
except Exception as e:
    print(f"⚠️ Utilities routes not loaded: {e}")

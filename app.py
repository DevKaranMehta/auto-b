from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import os
import csv
import io
import requests
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection with proper error handling"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'blockchain_news'),
            user=os.getenv('DB_USER', 'blockchain_admin'),
            password=os.getenv('DB_PASSWORD', 'secure_blockchain_2024'),
            connect_timeout=10,
            cursor_factory=RealDictCursor
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to database: {e}")
        return None

def create_slug(title):
    """Create URL-friendly slug from title"""
    if not title:
        return ""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')[:200]  # Limit slug length

def login_required(f):
    """Decorator for admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access the admin panel.')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def track_analytics(event_type, page_url=None):
    """Track user analytics"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analytics (event_type, page_url, ip_address, user_agent) 
                VALUES (%s, %s, %s, %s)
            """, (
                event_type, 
                page_url or request.url, 
                request.remote_addr or 'unknown',
                request.headers.get('User-Agent', '')[:500]  # Limit user agent length
            ))
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        logger.warning(f"Analytics tracking failed: {e}")

def get_setting(key, default=None):
    """Get setting value from database"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key = %s", (key,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result['setting_value'] if result else default
    except Exception as e:
        logger.warning(f"Failed to get setting {key}: {e}")
        return default

def generate_ai_content(topic, openai_key):
    """Generate AI content - placeholder for OpenAI integration"""
    try:
        # This is a placeholder. In production, integrate with OpenAI API
        return {
            'title': f'Latest Developments in {topic}: Comprehensive Market Analysis',
            'content': f'''
            <h3>Executive Summary</h3>
            <p>The {topic} sector continues to demonstrate significant growth and innovation in the blockchain ecosystem. Recent developments indicate strong market momentum and increased institutional adoption.</p>
            
            <h3>Market Analysis</h3>
            <p>Current market data shows {topic} experiencing substantial interest from both retail and institutional investors. Key metrics indicate:</p>
            <ul>
                <li>Increased transaction volume by 25% over the past month</li>
                <li>Growing developer activity and ecosystem expansion</li>
                <li>Enhanced security protocols and governance mechanisms</li>
            </ul>
            
            <h3>Technical Developments</h3>
            <p>Recent technical improvements in {topic} include enhanced scalability solutions, improved user experience, and robust security implementations.</p>
            
            <h3>Future Outlook</h3>
            <p>Looking ahead, {topic} is well-positioned for continued growth with upcoming protocol upgrades and increased mainstream adoption.</p>
            ''',
            'excerpt': f'Comprehensive analysis of {topic} market trends, technical developments, and future outlook in the rapidly evolving blockchain landscape.'
        }
    except Exception as e:
        logger.error(f"AI content generation failed: {e}")
        return None

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('public/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return render_template('public/500.html'), 500

# Public Routes
@app.route('/')
def index():
    track_analytics('pageview', '/')
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category')
    search = request.args.get('search', '').strip()
    
    try:
        conn = get_db_connection()
        if not conn:
            return render_template('public/index.html', 
                                 posts=[], categories=[], featured_post=None, 
                                 error="Database connection unavailable")
        
        cursor = conn.cursor()
        
        # Get categories
        cursor.execute("SELECT * FROM category ORDER BY name")
        categories = cursor.fetchall()
        
        # Build query for posts
        query = """
            SELECT p.*, c.name as category_name, c.color as category_color 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.is_published = TRUE
        """
        params = []
        
        if category_slug:
            query += " AND c.slug = %s"
            params.append(category_slug)
        
        if search:
            query += " AND (p.title ILIKE %s OR p.content ILIKE %s OR p.excerpt ILIKE %s)"
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        limit = 10
        offset = (page - 1) * limit
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        posts = cursor.fetchall()
        
        # Get featured post
        cursor.execute("""
            SELECT p.*, c.name as category_name, c.color as category_color 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.is_featured = TRUE AND p.is_published = TRUE 
            ORDER BY p.created_at DESC LIMIT 1
        """)
        featured_post = cursor.fetchone()
        
        # Get popular posts
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.is_published = TRUE 
            ORDER BY p.views DESC LIMIT 5
        """)
        popular_posts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('public/index.html', 
                             posts=posts, 
                             categories=categories,
                             featured_post=featured_post,
                             popular_posts=popular_posts,
                             current_category=category_slug,
                             search=search,
                             page=page)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template('public/index.html', 
                             posts=[], categories=[], featured_post=None,
                             error="An error occurred while loading content")

@app.route('/post/<slug>')
def post_detail(slug):
    if not slug or len(slug) > 200:
        abort(404)
        
    try:
        conn = get_db_connection()
        if not conn:
            abort(500)
        
        cursor = conn.cursor()
        
        # Get post with category information
        cursor.execute("""
            SELECT p.*, c.name as category_name, c.color as category_color 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.slug = %s AND p.is_published = TRUE
        """, (slug,))
        post = cursor.fetchone()
        
        if not post:
            abort(404)
        
        # Increment view count
        cursor.execute("UPDATE post SET views = views + 1 WHERE id = %s", (post['id'],))
        
        # Get related posts
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.id != %s AND p.category_id = %s AND p.is_published = TRUE 
            ORDER BY p.created_at DESC LIMIT 3
        """, (post['id'], post['category_id']))
        related_posts = cursor.fetchall()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        track_analytics('post_view', f'/post/{slug}')
        
        return render_template('public/post_detail.html', 
                             post=post, 
                             related_posts=related_posts)
    except Exception as e:
        logger.error(f"Error in post_detail route: {e}")
        abort(500)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return render_template('public/search.html', posts=[], query=query)
    
    try:
        conn = get_db_connection()
        if not conn:
            return render_template('public/search.html', posts=[], query=query, 
                                 error="Database connection unavailable")
        
        cursor = conn.cursor()
        
        search_term = f'%{query}%'
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE (p.title ILIKE %s OR p.content ILIKE %s OR p.excerpt ILIKE %s) 
            AND p.is_published = TRUE 
            ORDER BY p.created_at DESC LIMIT %s OFFSET %s
        """, (search_term, search_term, search_term, 10, (page - 1) * 10))
        posts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        track_analytics('search', f'/search?q={query}')
        
        return render_template('public/search.html', posts=posts, query=query, page=page)
    except Exception as e:
        logger.error(f"Error in search route: {e}")
        return render_template('public/search.html', posts=[], query=query,
                             error="An error occurred during search")

@app.route('/sitemap.xml')
def sitemap():
    try:
        conn = get_db_connection()
        if not conn:
            return "Error generating sitemap", 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT slug, updated_at FROM post 
            WHERE is_published = TRUE AND include_in_sitemap = TRUE 
            ORDER BY updated_at DESC
        """)
        posts = cursor.fetchall()
        
        cursor.execute("SELECT slug FROM category")
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Generate XML sitemap
        urlset = Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # Add homepage
        url = SubElement(urlset, 'url')
        SubElement(url, 'loc').text = request.url_root.rstrip('/')
        SubElement(url, 'lastmod').text = datetime.utcnow().strftime('%Y-%m-%d')
        SubElement(url, 'changefreq').text = 'daily'
        SubElement(url, 'priority').text = '1.0'
        
        # Add posts
        for post in posts:
            url = SubElement(urlset, 'url')
            SubElement(url, 'loc').text = f"{request.url_root.rstrip('/')}/post/{post['slug']}"
            SubElement(url, 'lastmod').text = post['updated_at'].strftime('%Y-%m-%d')
            SubElement(url, 'changefreq').text = 'weekly'
            SubElement(url, 'priority').text = '0.8'
        
        # Add category pages
        for category in categories:
            url = SubElement(urlset, 'url')
            SubElement(url, 'loc').text = f"{request.url_root.rstrip('/')}/?category={category['slug']}"
            SubElement(url, 'changefreq').text = 'weekly'
            SubElement(url, 'priority').text = '0.6'
        
        xml_str = minidom.parseString(tostring(urlset)).toprettyxml(indent="  ")
        
        response = app.make_response(xml_str)
        response.headers['Content-Type'] = 'application/xml'
        return response
    except Exception as e:
        logger.error(f"Error generating sitemap: {e}")
        return "Error generating sitemap", 500

@app.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email', '').strip()
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    # Basic email validation
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        return jsonify({'success': False, 'message': 'Invalid email format'})
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'})
        
        cursor = conn.cursor()
        
        # Check if already subscribed
        cursor.execute("SELECT id FROM newsletter WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email already subscribed'})
        
        # Add new subscriber
        cursor.execute("INSERT INTO newsletter (email) VALUES (%s)", (email,))
        conn.commit()
        cursor.close()
        conn.close()
        
        track_analytics('newsletter_signup')
        
        return jsonify({'success': True, 'message': 'Successfully subscribed!'})
    except Exception as e:
        logger.error(f"Newsletter subscription error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'})

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection error')
            return redirect(url_for('admin_login'))
        
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as count FROM post")
        total_posts = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM category")
        total_categories = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM newsletter WHERE is_active = TRUE")
        total_subscribers = cursor.fetchone()['count']
        
        # Get recent posts
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            ORDER BY p.created_at DESC LIMIT 5
        """)
        recent_posts = cursor.fetchall()
        
        # Get weekly views
        week_ago = datetime.utcnow() - timedelta(days=7)
        cursor.execute("""
            SELECT COUNT(*) as count FROM analytics 
            WHERE event_type = 'pageview' AND created_at >= %s
        """, (week_ago,))
        weekly_views = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return render_template('admin/dashboard.html',
                             total_posts=total_posts,
                             total_categories=total_categories,
                             total_subscribers=total_subscribers,
                             recent_posts=recent_posts,
                             weekly_views=weekly_views)
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        flash('An error occurred loading the dashboard')
        return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Redirect if already logged in
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required')
            return render_template('admin/login.html')
        
        try:
            conn = get_db_connection()
            if not conn:
                flash('Database connection error. Please try again.')
                return render_template('admin/login.html')
            
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admin_user WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['admin_logged_in'] = True
                session['admin_username'] = username
                session['admin_id'] = user['id']
                cursor.close()
                conn.close()
                
                flash('Welcome back!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid username or password')
            
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('An error occurred during login. Please try again.')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('You have been logged out successfully')
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"🚀 Starting Blockchain Latest News Platform on port {port}")
    logger.info(f"🌐 Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

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

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'blockchain-news-secret-key-2024')

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'n8n-postgres'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'blockchain_news'),
            user=os.getenv('DB_USER', 'n8n_user'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            connect_timeout=10,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def create_slug(title):
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def track_analytics(event_type, page_url=None):
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analytics (event_type, page_url, ip_address, user_agent) 
                VALUES (%s, %s, %s, %s)
            """, (event_type, page_url or request.url, request.remote_addr, request.headers.get('User-Agent', '')))
            conn.commit()
            cursor.close()
            conn.close()
    except:
        pass

def generate_ai_content(topic, openai_key):
    """AI content generation - integrate with your preferred AI service"""
    try:
        return {
            'title': f'Latest Developments in {topic}: Market Analysis and Future Outlook',
            'content': f'<h3>Introduction</h3><p>The {topic} sector continues to show remarkable growth...</p><h3>Market Analysis</h3><p>Recent developments indicate...</p><h3>Future Outlook</h3><p>Looking ahead, {topic} is positioned for...</p>',
            'excerpt': f'Comprehensive analysis of the latest {topic} developments, market trends, and future predictions.'
        }
    except Exception as e:
        print(f"AI content generation failed: {e}")
        return None

# Public Routes
@app.route('/')
def index():
    track_analytics('pageview', '/')
    try:
        conn = get_db_connection()
        if not conn:
            return render_template('public/index.html', posts=[], categories=[], featured_post=None)
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM category ORDER BY name")
        categories = cursor.fetchall()
        
        cursor.execute("""
            SELECT p.*, c.name as category_name, c.color as category_color 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.is_published = TRUE ORDER BY p.created_at DESC LIMIT 10
        """)
        posts = cursor.fetchall()
        
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.is_featured = TRUE AND p.is_published = TRUE LIMIT 1
        """)
        featured_post = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('public/index.html', 
                             posts=posts, 
                             categories=categories,
                             featured_post=featured_post)
    except Exception as e:
        print(f"Error in index: {e}")
        return render_template('public/index.html', posts=[], categories=[], featured_post=None)

@app.route('/post/<slug>')
def post_detail(slug):
    try:
        conn = get_db_connection()
        if not conn:
            abort(404)
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.slug = %s AND p.is_published = TRUE
        """, (slug,))
        post = cursor.fetchone()
        
        if not post:
            abort(404)
        
        cursor.execute("UPDATE post SET views = views + 1 WHERE id = %s", (post['id'],))
        conn.commit()
        cursor.close()
        conn.close()
        
        track_analytics('post_view', f'/post/{slug}')
        
        return render_template('public/post_detail.html', post=post)
    except Exception as e:
        print(f"Error in post_detail: {e}")
        abort(404)

@app.route('/sitemap.xml')
def sitemap():
    try:
        conn = get_db_connection()
        if not conn:
            return "Error generating sitemap", 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT slug, updated_at FROM post WHERE is_published = TRUE ORDER BY updated_at DESC")
        posts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        urlset = Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        url = SubElement(urlset, 'url')
        SubElement(url, 'loc').text = request.host_url
        SubElement(url, 'lastmod').text = datetime.utcnow().strftime('%Y-%m-%d')
        
        for post in posts:
            url = SubElement(urlset, 'url')
            SubElement(url, 'loc').text = f"{request.host_url}post/{post['slug']}"
            SubElement(url, 'lastmod').text = post['updated_at'].strftime('%Y-%m-%d')
        
        xml_str = minidom.parseString(tostring(urlset)).toprettyxml(indent="  ")
        
        response = app.make_response(xml_str)
        response.headers['Content-Type'] = 'application/xml'
        return response
    except Exception as e:
        return "Error generating sitemap", 500

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed"
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM post")
        total_posts = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) FROM category")
        total_categories = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) FROM newsletter")
        total_subscribers = cursor.fetchone()['count']
        
        cursor.execute("SELECT p.*, c.name as category_name FROM post p LEFT JOIN category c ON p.category_id = c.id ORDER BY p.created_at DESC LIMIT 5")
        recent_posts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/dashboard.html',
                             total_posts=total_posts,
                             total_categories=total_categories,
                             total_subscribers=total_subscribers,
                             recent_posts=recent_posts)
    except Exception as e:
        return f"Dashboard error: {str(e)}"

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            if not conn:
                flash('Database connection error')
                return render_template('admin/login.html')
            
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admin_user WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['admin_logged_in'] = True
                session['admin_username'] = username
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid credentials')
            
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Login error: {str(e)}')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🚀 Starting Blockchain Latest News Platform...")
    app.run(host='0.0.0.0', port=5000, debug=False)

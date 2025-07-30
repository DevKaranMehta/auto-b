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
            host='n8n-postgres',
            port='5432',
            database='blockchain_news',
            user='n8n_user',
            password='7661607468AAHE5Xc97@123??',
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

# Public Routes
@app.route('/')
def index():
    track_analytics('pageview', '/')
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category')
    search = request.args.get('search', '')
    
    try:
        conn = get_db_connection()
        if not conn:
            return render_template('public/index.html', posts=[], categories=[], featured_post=None, popular_posts=[])
        
        cursor = conn.cursor()
        
        # Get categories
        cursor.execute("SELECT * FROM category ORDER BY name")
        categories = cursor.fetchall()
        
        # Base query for posts
        query = "SELECT p.*, c.name as category_name, c.color as category_color FROM post p LEFT JOIN category c ON p.category_id = c.id WHERE p.is_published = TRUE"
        params = []
        
        if category_slug:
            query += " AND c.slug = %s"
            params.append(category_slug)
        
        if search:
            query += " AND (p.title ILIKE %s OR p.content ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        query += " ORDER BY p.created_at DESC LIMIT 10 OFFSET %s"
        params.append((page - 1) * 10)
        
        cursor.execute(query, params)
        posts = cursor.fetchall()
        
        # Get featured post
        cursor.execute("SELECT p.*, c.name as category_name, c.color as category_color FROM post p LEFT JOIN category c ON p.category_id = c.id WHERE p.is_featured = TRUE AND p.is_published = TRUE LIMIT 1")
        featured_post = cursor.fetchone()
        
        # Get popular posts
        cursor.execute("SELECT p.*, c.name as category_name FROM post p LEFT JOIN category c ON p.category_id = c.id WHERE p.is_published = TRUE ORDER BY p.views DESC LIMIT 5")
        popular_posts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('public/index.html', 
                             posts=posts, 
                             categories=categories,
                             featured_post=featured_post,
                             popular_posts=popular_posts,
                             current_category=category_slug,
                             search=search)
    except Exception as e:
        print(f"Error in index: {e}")
        return render_template('public/index.html', posts=[], categories=[], featured_post=None, popular_posts=[])

@app.route('/post/<slug>')
def post_detail(slug):
    """Fixed post detail route with proper error handling"""
    try:
        conn = get_db_connection()
        if not conn:
            print("Database connection failed")
            abort(500)
        
        cursor = conn.cursor()
        
        # Get post and increment views
        cursor.execute("""
            SELECT p.*, c.name as category_name, c.color as category_color 
            FROM post p 
            LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.slug = %s AND p.is_published = TRUE
        """, (slug,))
        post = cursor.fetchone()
        
        if not post:
            print(f"Post not found: {slug}")
            cursor.close()
            conn.close()
            abort(404)
        
        # Increment view count
        cursor.execute("UPDATE post SET views = views + 1 WHERE id = %s", (post['id'],))
        
        # Get related posts
        cursor.execute("""
            SELECT p.*, c.name as category_name FROM post p 
            LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.id != %s AND p.category_id = %s AND p.is_published = TRUE 
            ORDER BY p.created_at DESC LIMIT 3
        """, (post['id'], post['category_id']))
        related_posts = cursor.fetchall()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        track_analytics('post_view', f'/post/{slug}')
        
        return render_template('public/post_detail.html', post=post, related_posts=related_posts)
    except Exception as e:
        print(f"Error in post_detail: {e}")
        abort(404)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    try:
        conn = get_db_connection()
        if not conn:
            return render_template('public/search.html', posts=[], query=query)
        
        cursor = conn.cursor()
        
        if query:
            cursor.execute("""
                SELECT p.*, c.name as category_name FROM post p 
                LEFT JOIN category c ON p.category_id = c.id 
                WHERE (p.title ILIKE %s OR p.content ILIKE %s) AND p.is_published = TRUE 
                ORDER BY p.created_at DESC LIMIT 10 OFFSET %s
            """, (f'%{query}%', f'%{query}%', (page - 1) * 10))
            posts = cursor.fetchall()
        else:
            posts = []
        
        cursor.close()
        conn.close()
        
        track_analytics('search', f'/search?q={query}')
        
        return render_template('public/search.html', posts=posts, query=query)
    except Exception as e:
        print(f"Error in search: {e}")
        return render_template('public/search.html', posts=[], query=query)

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
        SubElement(url, 'loc').text = 'https://blockchainlatestnews.com'
        SubElement(url, 'lastmod').text = datetime.utcnow().strftime('%Y-%m-%d')
        
        for post in posts:
            url = SubElement(urlset, 'url')
            SubElement(url, 'loc').text = f"https://blockchainlatestnews.com/post/{post['slug']}"
            SubElement(url, 'lastmod').text = post['updated_at'].strftime('%Y-%m-%d')
        
        xml_str = minidom.parseString(tostring(urlset)).toprettyxml(indent="  ")
        
        response = app.make_response(xml_str)
        response.headers['Content-Type'] = 'application/xml'
        return response
        
    except Exception as e:
        print(f"Error generating sitemap: {e}")
        return "Error generating sitemap", 500

@app.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'})
        
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM newsletter WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email already subscribed'})
        
        cursor.execute("INSERT INTO newsletter (email) VALUES (%s)", (email,))
        conn.commit()
        cursor.close()
        conn.close()
        
        track_analytics('newsletter_signup')
        
        return jsonify({'success': True, 'message': 'Successfully subscribed!'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'An error occurred'})

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
        
        cursor.execute("SELECT COUNT(*) FROM newsletter WHERE is_active = TRUE")
        total_subscribers = cursor.fetchone()['count']
        
        cursor.execute("SELECT p.*, c.name as category_name FROM post p LEFT JOIN category c ON p.category_id = c.id ORDER BY p.created_at DESC LIMIT 5")
        recent_posts = cursor.fetchall()
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        cursor.execute("SELECT COUNT(*) FROM analytics WHERE event_type = 'pageview' AND created_at >= %s", (week_ago,))
        weekly_views_result = cursor.fetchone()
        weekly_views = weekly_views_result['count'] if weekly_views_result else 0
        
        cursor.close()
        conn.close()
        
        return render_template('admin/dashboard.html',
                             total_posts=total_posts,
                             total_categories=total_categories,
                             total_subscribers=total_subscribers,
                             recent_posts=recent_posts,
                             weekly_views=weekly_views)
    except Exception as e:
        return f"Admin dashboard error: {str(e)}"

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
                cursor.close()
                conn.close()
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid username or password')
            
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Login error: {str(e)}')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('index'))

@app.route('/admin/posts')
@login_required
def admin_posts():
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed"
        
        cursor = conn.cursor()
        cursor.execute("SELECT p.*, c.name as category_name FROM post p LEFT JOIN category c ON p.category_id = c.id ORDER BY p.created_at DESC")
        posts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('admin/posts.html', posts=posts)
    except Exception as e:
        return f"Posts error: {str(e)}"

@app.route('/admin/posts/new', methods=['GET', 'POST'])
@login_required
def admin_new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        excerpt = request.form.get('excerpt', '')
        category_id = request.form.get('category_id') or None
        is_featured = 'is_featured' in request.form
        is_published = 'is_published' in request.form
        
        slug = create_slug(title)
        
        try:
            conn = get_db_connection()
            if not conn:
                flash('Database connection error')
                return redirect(url_for('admin_posts'))
            
            cursor = conn.cursor()
            
            # Ensure unique slug
            counter = 1
            original_slug = slug
            while True:
                cursor.execute("SELECT id FROM post WHERE slug = %s", (slug,))
                if not cursor.fetchone():
                    break
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            cursor.execute("""
                INSERT INTO post (title, slug, content, excerpt, category_id, is_featured, is_published, author) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, slug, content, excerpt, category_id, is_featured, is_published, session.get('admin_username', 'Admin')))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Post created successfully!')
            return redirect(url_for('admin_posts'))
        except Exception as e:
            flash(f'Error creating post: {str(e)}')
    
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed"
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM category ORDER BY name")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('admin/post_form.html', categories=categories)
    except Exception as e:
        return f"Form error: {str(e)}"

@app.route('/admin/posts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_post(id):
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed"
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM post WHERE id = %s", (id,))
        post = cursor.fetchone()
        
        if not post:
            abort(404)
        
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            excerpt = request.form.get('excerpt', '')
            category_id = request.form.get('category_id') or None
            is_featured = 'is_featured' in request.form
            is_published = 'is_published' in request.form
            
            cursor.execute("""
                UPDATE post SET title = %s, content = %s, excerpt = %s, category_id = %s, 
                is_featured = %s, is_published = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (title, content, excerpt, category_id, is_featured, is_published, id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Post updated successfully!')
            return redirect(url_for('admin_posts'))
        
        cursor.execute("SELECT * FROM category ORDER BY name")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('admin/post_form.html', post=post, categories=categories)
    except Exception as e:
        return f"Edit error: {str(e)}"

@app.route('/admin/posts/<int:id>/delete', methods=['POST'])
@login_required
def admin_delete_post(id):
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection error')
            return redirect(url_for('admin_posts'))
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM post WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Post deleted successfully!')
    except Exception as e:
        flash(f'Error deleting post: {str(e)}')
    
    return redirect(url_for('admin_posts'))

@app.route('/admin/settings')
@login_required
def admin_settings():
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed"
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settings ORDER BY setting_key")
        settings_list = cursor.fetchall()
        
        # Convert to dictionary for easier access
        settings = {}
        for setting in settings_list:
            settings[setting['setting_key']] = setting['setting_value']
        
        cursor.close()
        conn.close()
        
        return render_template('admin/settings.html', settings=settings)
    except Exception as e:
        return f"Settings error: {str(e)}"

if __name__ == '__main__':
    print("🚀 Starting Blockchain Latest News Platform...")
    print("🌐 Public: https://blockchainlatestnews.com")
    print("🔐 Admin: https://blockchainlatestnews.com/admin")
    app.run(host='0.0.0.0', port=5000, debug=False)

@app.route('/admin/topics')
@login_required
def admin_topics():
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed"
        
        cursor = conn.cursor()
        cursor.execute("SELECT t.*, c.name as category_name FROM topics t LEFT JOIN category c ON t.category_id = c.id ORDER BY t.created_at DESC")
        topics = cursor.fetchall()
        
        cursor.execute("SELECT * FROM category ORDER BY name")
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/topics.html', topics=topics, categories=categories)
    except Exception as e:
        return f"Topics error: {str(e)}"

@app.route('/admin/topics/add', methods=['POST'])
@login_required
def admin_add_topic():
    try:
        topic_name = request.form.get('topic_name', '').strip()
        category_id = request.form.get('category_id') or None
        is_active = 'is_active' in request.form
        
        if not topic_name:
            flash('Topic name is required')
            return redirect(url_for('admin_topics'))
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error')
            return redirect(url_for('admin_topics'))
        
        cursor = conn.cursor()
        cursor.execute("INSERT INTO topics (name, category_id, is_active) VALUES (%s, %s, %s)", 
                      (topic_name, category_id, is_active))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Topic added successfully!')
        return redirect(url_for('admin_topics'))
    except Exception as e:
        flash(f'Error adding topic: {str(e)}')
        return redirect(url_for('admin_topics'))

@app.route('/admin/topics/import', methods=['POST'])
@login_required
def import_topics():
    try:
        if 'csv_file' not in request.files:
            flash('No CSV file uploaded')
            return redirect(url_for('admin_topics'))
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No file selected')
            return redirect(url_for('admin_topics'))
        
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error')
            return redirect(url_for('admin_topics'))
        
        cursor = conn.cursor()
        imported_count = 0
        
        for row in csv_input:
            if len(row) >= 2:
                topic_name = row[0].strip()
                category_id = int(row[1]) if row[1].isdigit() else None
                
                cursor.execute("SELECT id FROM topics WHERE name = %s", (topic_name,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO topics (name, category_id, is_active) VALUES (%s, %s, %s)", 
                                  (topic_name, category_id, True))
                    imported_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Successfully imported {imported_count} topics!')
        return redirect(url_for('admin_topics'))
        
    except Exception as e:
        flash(f'Error importing topics: {str(e)}')
        return redirect(url_for('admin_topics'))

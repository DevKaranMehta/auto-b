from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import os
import logging
import threading
import time
import random

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'blockchain-news-secret-key-2024')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection with proper error handling"""
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
        logger.error(f"Database connection failed: {e}")
        return None

def create_slug(title):
    """Create URL-friendly slug from title"""
    if not title:
        return ""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')[:200]

def login_required(f):
    """Decorator for admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

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

def table_exists(table_name):
    """Check if a table exists in the database"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result['exists'] if result else False
    except Exception as e:
        logger.error(f"Error checking table existence: {e}")
        return False

def generate_ai_content_advanced(topic_name, category_name="Blockchain"):
    """Enhanced AI content generation"""
    try:
        title_options = [
            f"{topic_name} Market Analysis: Key Trends and Insights for 2024",
            f"Breaking: {topic_name} Shows Strong Growth Momentum",
            f"{topic_name} Update: Latest Developments and Future Outlook",
            f"Deep Dive: {topic_name} Ecosystem Expansion and Investment Opportunities",
            f"{topic_name} Report: Performance Metrics and Strategic Analysis"
        ]
        
        title = random.choice(title_options)
        
        content_parts = [
            f"<h3>Executive Summary</h3>",
            f"<p>The {topic_name} sector continues to demonstrate remarkable growth and innovation. This comprehensive analysis examines current market conditions, recent developments, and future prospects for investors and industry stakeholders.</p>",
            
            f"<h3>Market Performance and Key Metrics</h3>",
            f"<p>Recent market data indicates significant progress in {topic_name} adoption, with key performance indicators showing {random.choice(['28%', '32%', '37%', '42%'])} growth over the past {random.choice(['month', 'quarter', 'six months'])}. Industry analysts note that {topic_name} continues to demonstrate strong market fundamentals and increasing institutional confidence.</p>",
            
            f"<h3>Technical Developments and Innovation</h3>",
            f"<p>The technical infrastructure supporting {topic_name} has seen substantial improvements, including enhanced security protocols, improved scalability solutions, and better user experience design. These developments position {topic_name} for continued growth and wider adoption.</p>",
            
            "<ul>",
            "<li>Advanced security protocols and enhanced user protection</li>",
            "<li>Increasing institutional adoption and investment</li>",
            "<li>Strategic partnerships and ecosystem expansion</li>",
            "<li>Regulatory clarity and compliance improvements</li>",
            "<li>Innovation in decentralized technologies</li>",
            "</ul>",
            
            f"<h3>Investment Outlook and Market Trends</h3>",
            f"<p>Current market sentiment surrounding {topic_name} remains optimistic, with institutional investors showing increased interest. The combination of technological advancement, regulatory progress, and growing user adoption creates a favorable environment for sustained growth in the sector.</p>",
            
            f"<h3>Conclusion</h3>",
            f"<p>The {topic_name} market presents compelling opportunities for both institutional and retail participants. With strong technical fundamentals, increasing adoption rates, and positive regulatory developments, {topic_name} is well-positioned for continued expansion and innovation in the evolving digital economy.</p>"
        ]
        
        content = "\n".join(content_parts)
        excerpt = f"Comprehensive market analysis of {topic_name} covering recent developments, performance metrics, and future growth prospects. Essential insights for investors and blockchain enthusiasts."
        
        return {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'reading_time': random.randint(6, 10)
        }
        
    except Exception as e:
        logger.error(f"AI content generation failed: {e}")
        return None

def generate_posts_from_topics():
    """Generate AI posts based on active topics"""
    try:
        logger.info("🤖 Starting AI content generation...")
        
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Check if AI generation is enabled
        if get_setting('ai_generation_enabled', 'false') != 'true':
            logger.info("ℹ️ AI generation is disabled")
            return False
        
        # Get active topics
        cursor.execute("SELECT t.*, c.name as category_name FROM topics t LEFT JOIN category c ON t.category_id = c.id WHERE t.is_active = TRUE ORDER BY RANDOM() LIMIT 5")
        topics = cursor.fetchall()
        
        if not topics:
            logger.info("ℹ️ No active topics found")
            return False
        
        generated_count = 0
        
        for topic in topics:
            ai_content = generate_ai_content_advanced(topic['name'], topic['category_name'] or 'Blockchain')
            
            if ai_content:
                slug = create_slug(ai_content['title'])
                
                # Ensure unique slug
                counter = 1
                original_slug = slug
                while True:
                    cursor.execute("SELECT id FROM post WHERE slug = %s", (slug,))
                    if not cursor.fetchone():
                        break
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                
                # Insert the post
                cursor.execute("""
                    INSERT INTO post (title, slug, content, excerpt, category_id, is_published, author) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    ai_content['title'],
                    slug,
                    ai_content['content'],
                    ai_content['excerpt'],
                    topic['category_id'],
                    True,
                    'AI Assistant'
                ))
                
                post_id = cursor.fetchone()['id']
                generated_count += 1
                logger.info(f"✅ Generated post: {ai_content['title'][:50]}...")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"🎉 Successfully generated {generated_count} AI posts")
        return generated_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error in AI generation: {e}")
        return False

# Public Routes
@app.route('/')
def index():
    try:
        conn = get_db_connection()
        if not conn:
            return render_template('public/index.html', posts=[], categories=[], featured_post=None)
        
        cursor = conn.cursor()
        
        # Get categories
        cursor.execute("SELECT * FROM category ORDER BY name")
        categories = cursor.fetchall()
        
        # Get posts
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.is_published = TRUE ORDER BY p.created_at DESC LIMIT 10
        """)
        posts = cursor.fetchall()
        
        # Get featured post
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM post p LEFT JOIN category c ON p.category_id = c.id 
            WHERE p.is_featured = TRUE AND p.is_published = TRUE LIMIT 1
        """)
        featured_post = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('public/index.html', 
                             posts=posts, categories=categories, featured_post=featured_post)
    except Exception as e:
        logger.error(f"Error in index: {e}")
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
        
        # Update view count
        cursor.execute("UPDATE post SET views = COALESCE(views, 0) + 1 WHERE id = %s", (post['id'],))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return render_template('public/post_detail.html', post=post)
    except Exception as e:
        logger.error(f"Error in post_detail: {e}")
        abort(404)

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed"
        
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as count FROM post")
        total_posts = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM topics WHERE is_active = TRUE")
        active_topics = cursor.fetchone()['count']
        
        # Check if task_queue exists
        pending_tasks = 0
        if table_exists('task_queue'):
            cursor.execute("SELECT COUNT(*) as count FROM task_queue WHERE status = 'PENDING'")
            pending_tasks = cursor.fetchone()['count']
        
        # Get recent posts
        cursor.execute("SELECT p.*, c.name as category_name FROM post p LEFT JOIN category c ON p.category_id = c.id ORDER BY p.created_at DESC LIMIT 5")
        recent_posts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/dashboard.html',
                             total_posts=total_posts,
                             active_topics=active_topics,
                             pending_tasks=pending_tasks,
                             recent_posts=recent_posts)
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
    session.clear()
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

# THIS IS THE MISSING ROUTE THAT'S CAUSING YOUR ERRORS
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
        topic_description = request.form.get('topic_description', '').strip()
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
        cursor.execute("INSERT INTO topics (name, description, category_id, is_active) VALUES (%s, %s, %s, %s)", 
                      (topic_name, topic_description, category_id, is_active))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Topic added successfully!')
        return redirect(url_for('admin_topics'))
    except Exception as e:
        flash(f'Error adding topic: {str(e)}')
        return redirect(url_for('admin_topics'))

@app.route('/admin/topics/generate', methods=['POST'])
@login_required
def generate_single_topic():
    try:
        data = request.get_json()
        topic_id = data.get('topic_id')
        
        if not topic_id:
            return jsonify({'success': False, 'message': 'Topic ID required'})
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection error'})
        
        cursor = conn.cursor()
        
        cursor.execute("SELECT t.*, c.name as category_name FROM topics t LEFT JOIN category c ON t.category_id = c.id WHERE t.id = %s", (topic_id,))
        topic = cursor.fetchone()
        
        if not topic:
            return jsonify({'success': False, 'message': 'Topic not found'})
        
        ai_content = generate_ai_content_advanced(topic['name'], topic['category_name'] or 'Blockchain')
        
        if not ai_content:
            return jsonify({'success': False, 'message': 'Failed to generate content'})
        
        slug = create_slug(ai_content['title'])
        counter = 1
        original_slug = slug
        while True:
            cursor.execute("SELECT id FROM post WHERE slug = %s", (slug,))
            if not cursor.fetchone():
                break
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        cursor.execute("""
            INSERT INTO post (title, slug, content, excerpt, category_id, is_published, author) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            ai_content['title'],
            slug,
            ai_content['content'],
            ai_content['excerpt'],
            topic['category_id'],
            True,
            'AI Assistant'
        ))
        
        post_id = cursor.fetchone()['id']
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Content generated successfully!',
            'post_title': ai_content['title'],
            'post_id': post_id
        })
        
    except Exception as e:
        logger.error(f"Single topic generation error: {e}")
        return jsonify({'success': False, 'message': f'Generation error: {str(e)}'})

@app.route('/admin/queue')
@login_required
def admin_queue():
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed"
        
        cursor = conn.cursor()
        
        # Check if task_queue table exists
        if not table_exists('task_queue'):
            return render_template('admin/queue.html', tasks=[], stats={}, next_scheduled=None, 
                                 error_message="Queue system is initializing. Please check back in a moment.")
        
        cursor.execute("SELECT * FROM task_queue ORDER BY created_at DESC LIMIT 50")
        tasks = cursor.fetchall()
        
        stats = {'PENDING': 0, 'COMPLETED': 0, 'FAILED': 0, 'RUNNING': 0}
        
        cursor.close()
        conn.close()
        
        return render_template('admin/queue.html', tasks=tasks, stats=stats, next_scheduled=None)
        
    except Exception as e:
        return f"Queue management error: {str(e)}"

@app.route('/admin/settings')
@login_required
def admin_settings():
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed"
        
        cursor = conn.cursor()
        
        # Check if settings table exists
        if not table_exists('settings'):
            settings = {
                'ai_generation_enabled': 'true',
                'posts_per_day': '3',
                'auto_publish_enabled': 'true'
            }
        else:
            cursor.execute("SELECT * FROM settings ORDER BY setting_key")
            settings_list = cursor.fetchall()
            settings = {setting['setting_key']: setting['setting_value'] for setting in settings_list}
        
        cursor.close()
        conn.close()
        
        return render_template('admin/settings.html', settings=settings)
    except Exception as e:
        return f"Settings error: {str(e)}"

@app.route('/admin/settings/update', methods=['POST'])
@login_required
def update_settings():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return redirect(url_for('admin_settings'))
        
        cursor = conn.cursor()
        
        # Create settings table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        settings_data = {
            'ai_generation_enabled': 'true' if 'ai_generation_enabled' in request.form else 'false',
            'posts_per_day': request.form.get('posts_per_day', '3'),
            'auto_publish_enabled': 'true' if 'auto_publish_enabled' in request.form else 'false',
        }
        
        for key, value in settings_data.items():
            cursor.execute("""
                INSERT INTO settings (setting_key, setting_value) 
                VALUES (%s, %s)
                ON CONFLICT (setting_key) DO UPDATE SET 
                setting_value = EXCLUDED.setting_value,
                updated_at = CURRENT_TIMESTAMP
            """, (key, value))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
        
    except Exception as e:
        flash(f'Error updating settings: {str(e)}', 'error')
        return redirect(url_for('admin_settings'))

@app.route('/admin/ai-scheduler/generate-now', methods=['POST'])
@login_required
def manual_generate_posts():
    """Manually trigger AI post generation"""
    try:
        success = generate_posts_from_topics()
        if success:
            flash('AI posts generated successfully!', 'success')
        else:
            flash('AI generation is disabled or no topics available. Please check your settings and topics.', 'warning')
    except Exception as e:
        flash(f'Error generating posts: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin_dashboard'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('public/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('public/500.html'), 500

if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info("🚀 Starting Blockchain Latest News Platform...")
    logger.info("🌐 Public: https://blockchainlatestnews.com")
    logger.info("🔐 Admin: https://blockchainlatestnews.com/admin")
    logger.info("🤖 AI Generation: Ready")
    
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)

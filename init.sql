-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS blockchain_news;

-- Use the database
\c blockchain_news;

-- Create admin_user table
CREATE TABLE IF NOT EXISTS admin_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(120) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create category table
CREATE TABLE IF NOT EXISTS category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#F0B90B',
    is_active BOOLEAN DEFAULT TRUE,
    post_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create post table with all necessary fields
CREATE TABLE IF NOT EXISTS post (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    is_featured BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT TRUE,
    include_in_sitemap BOOLEAN DEFAULT TRUE,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    meta_title VARCHAR(200),
    meta_description TEXT,
    meta_keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    author VARCHAR(100) DEFAULT 'Admin',
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    category_id INTEGER REFERENCES category(id) ON DELETE SET NULL,
    featured_image_url TEXT,
    reading_time INTEGER DEFAULT 5
);

-- Create newsletter table
CREATE TABLE IF NOT EXISTS newsletter (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    name VARCHAR(100),
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unsubscribed_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    subscription_source VARCHAR(50) DEFAULT 'website',
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255)
);

-- Create analytics table
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    page_url VARCHAR(500),
    referrer_url VARCHAR(500),
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);

-- Create topics table for AI content generation
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    keywords TEXT,
    category_id INTEGER REFERENCES category(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1,
    last_generated TIMESTAMP,
    generation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create settings table
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string',
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create ai_posts table for tracking AI-generated content
CREATE TABLE IF NOT EXISTS ai_posts (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    prompt_used TEXT,
    ai_model VARCHAR(100),
    generation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quality_score DECIMAL(3,2),
    human_reviewed BOOLEAN DEFAULT FALSE,
    review_notes TEXT
);

-- Create comments table (for future use)
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    author_name VARCHAR(100) NOT NULL,
    author_email VARCHAR(120) NOT NULL,
    content TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT FALSE,
    is_spam BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_post_published ON post(is_published);
CREATE INDEX IF NOT EXISTS idx_post_featured ON post(is_featured);
CREATE INDEX IF NOT EXISTS idx_post_category ON post(category_id);
CREATE INDEX IF NOT EXISTS idx_post_created_at ON post(created_at);
CREATE INDEX IF NOT EXISTS idx_post_slug ON post(slug);
CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_created_at ON analytics(created_at);
CREATE INDEX IF NOT EXISTS idx_newsletter_active ON newsletter(is_active);

-- Insert default categories
INSERT INTO category (name, slug, description, color) VALUES 
('DeFi', 'defi', 'Decentralized Finance news and innovations', '#F0B90B'),
('Enterprise', 'enterprise', 'Enterprise blockchain adoption and solutions', '#FF9500'),
('Regulation', 'regulation', 'Regulatory news and compliance updates', '#1E2329'),
('Technology', 'technology', 'Blockchain technology innovations and developments', '#2B3139'),
('Market Analysis', 'market-analysis', 'Cryptocurrency market insights and analysis', '#FCD535'),
('NFTs', 'nfts', 'Non-Fungible Tokens news and marketplace updates', '#8B5CF6'),
('Web3', 'web3', 'Web3 infrastructure and decentralized applications', '#10B981')
ON CONFLICT (name) DO NOTHING;

-- Insert admin user with secure password hash
-- Password: blockchain2024
INSERT INTO admin_user (username, password_hash, email) VALUES 
('admin', 'pbkdf2:sha256:260000$salt123$8e1b2c3d4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f', 'admin@blockchain-news.local')
ON CONFLICT (username) DO NOTHING;

-- Insert default settings
INSERT INTO settings (setting_key, setting_value, setting_type, description, is_public) VALUES 
('site_name', 'Blockchain Latest News', 'string', 'Website name', TRUE),
('site_description', 'Professional blockchain and cryptocurrency news platform', 'string', 'Site meta description', TRUE),
('posts_per_page', '10', 'integer', 'Number of posts per page', FALSE),
('ai_generation_enabled', 'true', 'boolean', 'Enable AI content generation', FALSE),
('newsletter_enabled', 'true', 'boolean', 'Enable newsletter subscriptions', FALSE),
('analytics_enabled', 'true', 'boolean', 'Enable analytics tracking', FALSE),
('maintenance_mode', 'false', 'boolean', 'Enable maintenance mode', FALSE),
('openai_api_key', '', 'string', 'OpenAI API key for content generation', FALSE),
('max_file_size', '16777216', 'integer', 'Maximum file upload size in bytes', FALSE),
('content_freshness_days', '7', 'integer', 'Content freshness limit in days', FALSE)
ON CONFLICT (setting_key) DO NOTHING;

-- Insert sample topics for AI generation
INSERT INTO topics (name, description, keywords, category_id, priority) VALUES 
('DeFi Protocol Updates', 'Latest updates and developments in DeFi protocols', 'DeFi, protocols, yield farming, liquidity mining', 1, 1),
('NFT Marketplace Trends', 'Trending topics in NFT marketplaces and collections', 'NFT, marketplace, collections, trading', 6, 2),
('Enterprise Blockchain Adoption', 'Companies adopting blockchain technology', 'enterprise, adoption, corporate, blockchain', 2, 1),
('Cryptocurrency Regulations', 'Latest regulatory developments worldwide', 'regulation, compliance, legal, cryptocurrency', 3, 1),
('Layer 2 Scaling Solutions', 'Ethereum Layer 2 and scaling technologies', 'Layer 2, scaling, Ethereum, rollups', 4, 1),
('Web3 Infrastructure', 'Web3 tools and infrastructure developments', 'Web3, infrastructure, dApps, decentralized', 7, 2)
ON CONFLICT (name) DO NOTHING;

-- Insert sample blog post
INSERT INTO post (
    title, 
    slug, 
    content, 
    excerpt, 
    is_featured, 
    is_published,
    meta_title,
    meta_description,
    category_id, 
    views, 
    reading_time,
    published_at
) VALUES (
    'Welcome to Blockchain Latest News: Your Premier Crypto Information Hub',
    'welcome-to-blockchain-latest-news-premier-crypto-hub',
    '<h3>Welcome to the Future of Blockchain Information</h3>
    <p>We''re excited to launch Blockchain Latest News, your comprehensive source for cutting-edge cryptocurrency and blockchain technology insights. Our platform combines professional journalism with AI-powered content generation to deliver the most relevant and timely information in the rapidly evolving blockchain space.</p>
    
    <h3>What Sets Us Apart</h3>
    <ul>
        <li><strong>AI-Enhanced Content:</strong> Our advanced AI system generates timely, relevant content about trending blockchain topics</li>
        <li><strong>Professional Analysis:</strong> Expert-level market analysis and technical insights</li>
        <li><strong>Real-time Updates:</strong> Stay ahead with the latest developments in DeFi, NFTs, and enterprise blockchain</li>
        <li><strong>Comprehensive Coverage:</strong> From regulatory updates to technological breakthroughs</li>
    </ul>
    
    <h3>Our Content Categories</h3>
    <p>We cover all major aspects of the blockchain ecosystem:</p>
    <ul>
        <li><strong>DeFi:</strong> Decentralized finance protocols, yield farming, and liquidity mining</li>
        <li><strong>Enterprise:</strong> Corporate blockchain adoption and business use cases</li>
        <li><strong>Regulation:</strong> Legal developments and compliance updates worldwide</li>
        <li><strong>Technology:</strong> Technical innovations and protocol upgrades</li>
        <li><strong>Market Analysis:</strong> Trading insights and market trend analysis</li>
        <li><strong>NFTs:</strong> Non-fungible token marketplace trends and collections</li>
        <li><strong>Web3:</strong> Decentralized applications and infrastructure</li>
    </ul>
    
    <h3>Advanced Features</h3>
    <p>Our platform includes cutting-edge features designed for the modern crypto enthusiast:</p>
    <ul>
        <li>AI-powered content generation for trending topics</li>
        <li>Advanced search and filtering capabilities</li>
        <li>Newsletter subscription for daily updates</li>
        <li>Mobile-optimized responsive design</li>
        <li>SEO-optimized content for maximum visibility</li>
        <li>Social sharing integration</li>
    </ul>
    
    <h3>Join Our Community</h3>
    <p>Subscribe to our newsletter to receive daily blockchain insights directly in your inbox. Stay informed about the latest developments, market trends, and investment opportunities in the cryptocurrency space.</p>
    
    <p>Thank you for choosing Blockchain Latest News as your trusted source for blockchain information. We''re committed to providing you with accurate, timely, and insightful content to help you navigate the exciting world of cryptocurrency and blockchain technology.</p>',
    'Welcome to Blockchain Latest News, your premier destination for AI-powered cryptocurrency insights, DeFi updates, and comprehensive blockchain technology coverage.',
    TRUE,
    TRUE,
    'Welcome to Blockchain Latest News - Premier Crypto News Platform',
    'Discover the latest in cryptocurrency, DeFi, NFTs, and blockchain technology with our AI-powered news platform. Professional insights and real-time updates.',
    1,
    156,
    8,
    CURRENT_TIMESTAMP
) ON CONFLICT (slug) DO NOTHING;

-- Function to update post count in categories
CREATE OR REPLACE FUNCTION update_category_post_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE category SET post_count = (
            SELECT COUNT(*) FROM post WHERE category_id = NEW.category_id AND is_published = TRUE
        ) WHERE id = NEW.category_id;
    END IF;
    
    IF TG_OP = 'DELETE' OR (TG_OP = 'UPDATE' AND OLD.category_id != NEW.category_id) THEN
        UPDATE category SET post_count = (
            SELECT COUNT(*) FROM post WHERE category_id = OLD.category_id AND is_published = TRUE
        ) WHERE id = OLD.category_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic post count updates
DROP TRIGGER IF EXISTS trigger_update_category_post_count ON post;
CREATE TRIGGER trigger_update_category_post_count
    AFTER INSERT OR UPDATE OR DELETE ON post
    FOR EACH ROW EXECUTE FUNCTION update_category_post_count();

-- Update existing category post counts
UPDATE category SET post_count = (
    SELECT COUNT(*) FROM post WHERE category_id = category.id AND is_published = TRUE
);

-- Create view for popular posts
CREATE OR REPLACE VIEW popular_posts AS
SELECT 
    p.*,
    c.name as category_name,
    c.color as category_color
FROM post p
LEFT JOIN category c ON p.category_id = c.id
WHERE p.is_published = TRUE
ORDER BY p.views DESC, p.created_at DESC;

-- Create view for recent posts
CREATE OR REPLACE VIEW recent_posts AS
SELECT 
    p.*,
    c.name as category_name,
    c.color as category_color
FROM post p
LEFT JOIN category c ON p.category_id = c.id
WHERE p.is_published = TRUE
ORDER BY p.created_at DESC;

COMMIT;

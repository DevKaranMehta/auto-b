-- Create admin_user table
CREATE TABLE IF NOT EXISTS admin_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create category table
CREATE TABLE IF NOT EXISTS category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#F0B90B',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create post table
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    author VARCHAR(100) DEFAULT 'Admin',
    views INTEGER DEFAULT 0,
    category_id INTEGER REFERENCES category(id)
);

-- Create newsletter table
CREATE TABLE IF NOT EXISTS newsletter (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create analytics table
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    page_url VARCHAR(200),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create topics table
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER REFERENCES category(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create settings table
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default data
INSERT INTO category (name, slug, description, color) VALUES 
('DeFi', 'defi', 'Decentralized Finance news', '#F0B90B'),
('Enterprise', 'enterprise', 'Enterprise blockchain adoption', '#FF9500'),
('Regulation', 'regulation', 'Regulatory news and compliance', '#1E2329'),
('Technology', 'technology', 'Blockchain technology innovations', '#2B3139'),
('Market Analysis', 'market-analysis', 'Crypto market insights', '#FCD535')
ON CONFLICT (name) DO NOTHING;

-- Insert admin user (password: blockchain2024)
INSERT INTO admin_user (username, password_hash) VALUES 
('admin', 'pbkdf2:sha256:260000$salt$d5c7f2a3b8e9f1a4c6d8e2b5c9f3a7d1e4b8c2f6a9d3e7b1c5f8a2d6e9c4b7f1a5')
ON CONFLICT (username) DO NOTHING;

-- Insert sample post
INSERT INTO post (title, slug, content, excerpt, is_featured, category_id, views) VALUES 
(
    'Welcome to Blockchain Latest News',
    'welcome-to-blockchain-latest-news',
    '<h3>Welcome to Your Professional Blockchain News Platform</h3><p>This platform provides the latest insights into blockchain technology, cryptocurrency markets, and decentralized finance innovations.</p><h3>Key Features</h3><ul><li>AI-powered content generation</li><li>Professional admin dashboard</li><li>SEO optimization</li><li>Newsletter system</li><li>Mobile responsive design</li></ul>',
    'Your professional blockchain news platform is ready! Discover the latest in cryptocurrency, DeFi, and blockchain technology.',
    TRUE,
    1,
    100
) ON CONFLICT (slug) DO NOTHING;

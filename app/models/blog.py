from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Blog(Base):
    __tablename__ = "blogs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    meta_description = Column(String(160))
    meta_keywords = Column(String(255))
    slug = Column(String(255), unique=True, index=True)
    category = Column(String(100))
    tags = Column(ARRAY(String))
    author = Column(String(100), default="BlockchainLatestNews Editorial")
    featured_image_url = Column(String(500))
    is_published = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    is_ai_generated = Column(Boolean, default=True)
    ai_prompt = Column(Text)
    trending_score = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    scheduled_publish_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TrendingTopic(Base):
    __tablename__ = "trending_topics"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255), nullable=False)
    search_volume = Column(Integer, default=0)
    relevance_score = Column(Integer, default=0)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

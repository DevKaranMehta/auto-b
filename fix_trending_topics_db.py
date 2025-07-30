import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models.blog import TrendingTopic, Blog
from sqlalchemy import text, inspect
import random
from datetime import datetime

def fix_trending_topics_database():
    """Fix and populate trending topics database for PostgreSQL"""
    try:
        db = SessionLocal()
        
        # FIXED: Use PostgreSQL-specific table existence check
        # Use SQLAlchemy inspector instead of sqlite_master
        inspector = inspect(engine)
        table_exists = inspector.has_table('trending_topics')
        
        if not table_exists:
            print("❌ TrendingTopic table doesn't exist. Creating tables...")
            # Create all tables
            from app.models.blog import Base
            Base.metadata.create_all(bind=engine)
            print("✅ Tables created successfully")
        else:
            print("✅ TrendingTopic table exists")
        
        # Check current trending topics count
        count = db.query(TrendingTopic).count()
        print(f"📊 Current trending topics in database: {count}")
        
        if count == 0:
            print("🔄 Adding sample trending topics...")
            
            # Add sample trending topics based on current 2025 trends
            sample_topics = [
                "Bitcoin ETF Approval Impact on Cryptocurrency Markets",
                "Ethereum Layer 2 Scaling Solutions Adoption",
                "DeFi Protocol Security Improvements 2025",
                "NFT Utility Beyond Digital Art",
                "Central Bank Digital Currencies Global Implementation",
                "Blockchain Interoperability Solutions",
                "Real World Asset Tokenization Trends",
                "Zero Knowledge Proof Technology Applications",
                "AI Integration with Blockchain Technology",
                "Sustainable Blockchain Mining Solutions",
                "Web3 Gaming Market Expansion",
                "Cryptocurrency Regulation Updates",
                "Smart Contract Security Auditing",
                "Decentralized Autonomous Organizations Growth",
                "Metaverse Blockchain Infrastructure",
                "Cross-Chain Bridge Security",
                "Quantum-Resistant Blockchain Development",
                "Stablecoin Regulatory Framework",
                "Decentralized Identity Management",
                "Blockchain Carbon Credit Trading"
            ]
            
            for i, topic in enumerate(sample_topics):
                new_topic = TrendingTopic(
                    topic=topic,
                    relevance_score=random.randint(70, 100),
                    search_volume=random.randint(1000, 10000),
                    created_at=datetime.now()
                )
                db.add(new_topic)
                print(f"➕ Added: {topic}")
            
            db.commit()
            print("✅ Sample trending topics added successfully")
        else:
            print("✅ Trending topics already exist in database")
        
        # Verify the data was saved
        final_count = db.query(TrendingTopic).count()
        print(f"📈 Final trending topics count: {final_count}")
        
        # Show some sample topics
        topics = db.query(TrendingTopic).limit(5).all()
        print("\n🔥 Sample topics from database:")
        for topic in topics:
            print(f"   • {topic.topic} (Score: {topic.relevance_score})")
        
        # FIXED: Test database connection type
        db_engine_name = engine.dialect.name
        print(f"\n📊 Database engine: {db_engine_name}")
        
        if db_engine_name == 'postgresql':
            print("✅ PostgreSQL database detected - using correct queries")
        elif db_engine_name == 'sqlite':
            print("ℹ️ SQLite database detected")
        else:
            print(f"⚠️ Unknown database type: {db_engine_name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"   Cause: {e.__cause__}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_trending_topics_database()

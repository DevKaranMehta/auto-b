import sys
import os
sys.path.append('.')

try: 
    from app.database import SessionLocal
    from app.models.blog import TrendingTopic
    import random
    from datetime import datetime
    
    def add_trending_topics_safe():
        """Add trending topics safely without checking table existence"""
        db = SessionLocal()
        
        try:
            # Just try to add topics directly - if table doesn't exist, it will error clearly
            topics = [
                "Modular Blockchain Architecture 2025",
                "Zero-Knowledge Proofs Implementation", 
                "Real-World Asset Tokenization",
                "AI Blockchain Integration",
                "DeFi Protocol Evolution",
                "Cross-Chain Interoperability",
                "Enterprise Blockchain Adoption",
                "Cryptocurrency Regulatory Updates",
                "Sustainable Mining Technology",
                "Web3 Social Platform Development",
                "Decentralized Identity Solutions",
                "Smart Contract Security Audits",
                "Layer 2 Scaling Solutions",
                "NFT Utility Applications",
                "Central Bank Digital Currencies"
            ]
            
            count = 0
            for topic_text in topics:
                # Check if exists
                existing = db.query(TrendingTopic).filter(TrendingTopic.topic == topic_text).first()
                if not existing:
                    topic = TrendingTopic(
                        topic=topic_text,
                        relevance_score=random.randint(75, 100),
                        search_volume=random.randint(2000, 15000),
                        created_at=datetime.now()
                    )
                    db.add(topic)
                    count += 1
                    print(f"➕ Added: {topic_text}")
            
            db.commit()
            print(f"✅ Successfully added {count} trending topics!")
            
            # Verify
            total_count = db.query(TrendingTopic).count()
            print(f"📊 Total trending topics in database: {total_count}")
            
            return count
        
        except Exception as e:
            print(f"❌ Error: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    if __name__ == "__main__":
        add_trending_topics_safe()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project directory")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

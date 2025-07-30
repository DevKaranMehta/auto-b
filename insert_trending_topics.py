import sys
import os
sys.path.append('.')

try:
    from app.database import SessionLocal
    from app.models.blog import TrendingTopic
    import random
    from datetime import datetime
    
    def add_trending_topics():
        db = SessionLocal()
        
        # Current 2025 blockchain trending topics
        topics = [
            "Modular Blockchain Architecture Development",
            "Zero-Knowledge Proofs at Scale Implementation", 
            "Real-World Asset Tokenization Growth",
            "Blockchain Digital Identity Solutions",
            "AI and Blockchain Infrastructure Integration",
            "DeFi Evolution and Traditional Finance",
            "Sustainability in Blockchain Technology",
            "Cross-Chain Interoperability Solutions",
            "Enterprise Blockchain Adoption",
            "Regulatory Compliance in Cryptocurrency",
            "NFT Utility Beyond Digital Collectibles",
            "Central Bank Digital Currency Pilots",
            "Blockchain Gaming and Metaverse",
            "Decentralized Storage Solutions",
            "Web3 Social Media Platforms"
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
        db.close()
        print(f"✅ Successfully added {count} trending topics!")
        
        return count

    if __name__ == "__main__":
        add_trending_topics()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project directory and the app module exists")
except Exception as e:
    print(f"❌ Error: {e}")

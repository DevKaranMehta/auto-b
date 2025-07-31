from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import sys
import os
import random
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.blog import TrendingTopic
from app.services.advanced_scheduler import advanced_scheduler

router = APIRouter()

@router.post("/trending/update-now")
async def update_trending_now(db: Session = Depends(get_db)):
    """Manually trigger trending topics update"""
    try:
        print("🚀 Manual trending topics update triggered")
        
        # Use the scheduler's update function
        advanced_scheduler.update_trending_topics()
        message = "AI trending topics updated successfully"
        
        return RedirectResponse(url=f"/admin/trending-topics?success={message}", status_code=303)
        
    except Exception as e:
        error_message = f"Failed to update trending topics: {str(e)}"
        print(f"❌ {error_message}")
        return RedirectResponse(url=f"/admin/trending-topics?error={error_message}", status_code=303)

@router.post("/trending/add-sample")
async def add_sample_topics(db: Session = Depends(get_db)):
    """Add sample trending topics for testing"""
    try:
        # Current 2025 blockchain trending topics based on research
        sample_topics_2025 = [
            "Bitcoin ETF Market Impact Analysis",
            "Ethereum Layer 2 Scaling Adoption",
            "DeFi Protocol Security Enhancements", 
            "NFT Utility in Gaming and Metaverse",
            "Central Bank Digital Currency Updates",
            "Blockchain Interoperability Protocols",
            "Real-World Asset Tokenization Trends",
            "Zero-Knowledge Proof Applications",
            "AI-Blockchain Integration Solutions",
            "Sustainable Cryptocurrency Mining",
            "Web3 Infrastructure Development",
            "Regulatory Clarity in Digital Assets",
            "Smart Contract Audit Standards",
            "Decentralized Identity Management",
            "Cross-Border Blockchain Payments"
        ]
        
        added_count = 0
        for topic in sample_topics_2025:
            # Check if topic already exists
            existing = db.query(TrendingTopic).filter(
                TrendingTopic.topic == topic
            ).first()
            
            if not existing:
                new_topic = TrendingTopic(
                    topic=topic,
                    relevance_score=random.randint(80, 100),
                    search_volume=random.randint(3000, 12000),
                    created_at=datetime.now()
                )
                db.add(new_topic)
                added_count += 1
        
        db.commit()
        
        return RedirectResponse(
            url=f"/admin/trending-topics?success=Added {added_count} sample trending topics", 
            status_code=303
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/trending-topics?error={str(e)}", 
            status_code=303
        )

@router.post("/trending/add-topic")
async def add_topic(
    topic: str = Form(...),
    relevance_score: int = Form(...),
    search_volume: int = Form(...),
    db: Session = Depends(get_db)
):
    """Add a new trending topic"""
    try:
        # Check if topic already exists
        existing = db.query(TrendingTopic).filter(
            TrendingTopic.topic.ilike(f"%{topic}%")
        ).first()
        
        if existing:
            return RedirectResponse(
                url=f"/admin/trending-topics?error=Topic already exists or is similar to existing topic",
                status_code=303
            )
        
        new_topic = TrendingTopic(
            topic=topic,
            relevance_score=relevance_score,
            search_volume=search_volume,
            created_at=datetime.now()
        )
        
        db.add(new_topic)
        db.commit()
        
        return RedirectResponse(
            url=f"/admin/trending-topics?success=Topic '{topic}' added successfully",
            status_code=303
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/trending-topics?error=Failed to add topic: {str(e)}",
            status_code=303
        )

@router.post("/trending/edit-topic")
async def edit_topic(
    topic_id: int = Form(...),
    topic: str = Form(...),
    relevance_score: int = Form(...),
    search_volume: int = Form(...),
    db: Session = Depends(get_db)
):
    """Edit an existing trending topic"""
    try:
        existing_topic = db.query(TrendingTopic).filter(
            TrendingTopic.id == topic_id
        ).first()
        
        if not existing_topic:
            return RedirectResponse(
                url=f"/admin/trending-topics?error=Topic not found",
                status_code=303
            )
        
        existing_topic.topic = topic
        existing_topic.relevance_score = relevance_score
        existing_topic.search_volume = search_volume
        
        db.commit()
        
        return RedirectResponse(
            url=f"/admin/trending-topics?success=Topic updated successfully",
            status_code=303
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/trending-topics?error=Failed to update topic: {str(e)}",
            status_code=303
        )

@router.post("/trending/delete-topic")
async def delete_topic(
    topic_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Delete a trending topic"""
    try:
        topic = db.query(TrendingTopic).filter(
            TrendingTopic.id == topic_id
        ).first()
        
        if not topic:
            return RedirectResponse(
                url=f"/admin/trending-topics?error=Topic not found",
                status_code=303
            )
        
        topic_name = topic.topic
        db.delete(topic)
        db.commit()
        
        return RedirectResponse(
            url=f"/admin/trending-topics?success=Topic '{topic_name}' deleted successfully",
            status_code=303
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/trending-topics?error=Failed to delete topic: {str(e)}",
            status_code=303
        )

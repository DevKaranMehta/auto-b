from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class NewsletterSubscription(Base):
    __tablename__ = "newsletter_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=func.now())
    unsubscribed_at = Column(DateTime, nullable=True)

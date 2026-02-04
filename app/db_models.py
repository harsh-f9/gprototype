from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f"<User(email='{self.email}')>"

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Onboarding data
    category = Column(String)  # "green", "sll", "other"
    initial_data = Column(JSON)  # 7-question responses
    intake_data = Column(JSON)  # Detailed form data
    
    # Results
    score = Column(Integer)
    rating = Column(String)
    carbon_estimate = Column(Float)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, category='{self.category}')>"

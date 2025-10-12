from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), nullable=False)  # student|instructor|admin
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="user")
    interactions = relationship("Interaction", back_populates="user")
    aggregates = relationship("AggregateUser", back_populates="user")

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    # English content
    stem_en = Column(Text, nullable=False)
    options_en_json = Column(Text, nullable=False)  # JSON array of English options
    # Russian content
    stem_ru = Column(Text, nullable=True)
    options_ru_json = Column(Text, nullable=True)  # JSON array of Russian options
    # Common fields
    correct_option = Column(Integer, nullable=False)
    tags_en = Column(String(200), nullable=False)  # comma-separated English tags
    tags_ru = Column(String(200), nullable=True)  # comma-separated Russian tags
    difficulty_hint = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interactions = relationship("Interaction", back_populates="item")
    aggregates = relationship("AggregateItem", back_populates="item")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mode = Column(String(20), nullable=False)  # standard|self_confidence
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    interactions = relationship("Interaction", back_populates="session")

class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    chosen_option = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=True)  # 0.0-1.0
    response_time_ms = Column(Integer, nullable=False)
    attempts_count = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="interactions")
    user = relationship("User", back_populates="interactions")
    item = relationship("Item", back_populates="interactions")

class AggregateItem(Base):
    __tablename__ = "aggregates_items"
    
    item_id = Column(Integer, ForeignKey("items.id"), primary_key=True)
    avg_accuracy = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)
    avg_conf_gap = Column(Float, default=0.0)
    avg_time_ms = Column(Float, default=0.0)
    elo_difficulty = Column(Float, default=1000.0)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    item = relationship("Item", back_populates="aggregates")

class AggregateUser(Base):
    __tablename__ = "aggregates_users"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    ema_accuracy = Column(Float, default=0.0)
    ema_confidence = Column(Float, default=0.0)
    ema_conf_gap = Column(Float, default=0.0)
    avg_time_ms = Column(Float, default=0.0)
    elo_ability = Column(Float, default=1000.0)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="aggregates")

class ModelRegistry(Base):
    __tablename__ = "model_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow)
    params_json = Column(Text, nullable=False)  # JSON parameters
    calib_type = Column(String(20), nullable=False)  # platt|isotonic|none
    ece = Column(Float, nullable=True)
    brier = Column(Float, nullable=True)
    roc_auc = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

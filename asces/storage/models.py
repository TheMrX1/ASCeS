from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String) # INFO, WARN, CRIT
    window_size = Column(Integer)
    feature = Column(String)
    hurst_method = Column(String)
    current_h = Column(Float)
    baseline_mean = Column(Float)
    baseline_std = Column(Float)
    z_score = Column(Float)
    message = Column(Text)
    assessment = Column(String) # Short classification (e.g. "DDoS")
    metadata_json = Column(Text) # Stores JSON string of IPs, Cookies, etc.

class BaselineMeta(Base):
    __tablename__ = "baselines_metadata"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    name = Column(String)
    version = Column(String)
    path = Column(String)

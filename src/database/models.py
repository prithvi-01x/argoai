"""
Database models for ARGO data storage.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class ARGOFloat(Base):
    """Model for ARGO float metadata."""
    
    __tablename__ = 'argo_floats'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    float_id = Column(String(50), unique=True, nullable=False, index=True)
    wmo_id = Column(String(50), nullable=False)
    institution = Column(String(100), nullable=False)
    data_mode = Column(String(20), nullable=False)
    deployment_date = Column(DateTime)
    last_transmission = Column(DateTime)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ARGOProfile(Base):
    """Model for ARGO profile data."""
    
    __tablename__ = 'argo_profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    float_id = Column(String(50), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    profile_time = Column(DateTime, nullable=False)
    max_depth = Column(Float)
    min_depth = Column(Float)
    num_levels = Column(Integer)
    data_mode = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for efficient querying
    __table_args__ = (
        {'extend_existing': True}
    )

class ARGOMeasurement(Base):
    """Model for individual ARGO measurements."""
    
    __tablename__ = 'argo_measurements'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    float_id = Column(String(50), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    pressure = Column(Float)
    depth = Column(Float)
    temperature = Column(Float)
    salinity = Column(Float)
    oxygen = Column(Float)  # DOXY
    chlorophyll = Column(Float)  # CHLA
    backscatter = Column(Float)  # BBP700
    nitrate = Column(Float)  # NITRATE
    ph = Column(Float)  # PH_IN_SITU_TOTAL
    temperature_qc = Column(Integer)
    salinity_qc = Column(Integer)
    oxygen_qc = Column(Integer)
    chlorophyll_qc = Column(Integer)
    backscatter_qc = Column(Integer)
    nitrate_qc = Column(Integer)
    ph_qc = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class ARGOTrajectory(Base):
    """Model for ARGO float trajectory data."""
    
    __tablename__ = 'argo_trajectories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    float_id = Column(String(50), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    trajectory_time = Column(DateTime, nullable=False)
    cycle_number = Column(Integer)
    data_mode = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

class QueryLog(Base):
    """Model for logging user queries."""
    
    __tablename__ = 'query_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_query = Column(Text, nullable=False)
    processed_query = Column(Text)
    sql_query = Column(Text)
    response = Column(Text)
    execution_time = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class DataSummary(Base):
    """Model for storing data summaries and metadata."""
    
    __tablename__ = 'data_summaries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary_type = Column(String(50), nullable=False)  # 'float', 'region', 'parameter'
    summary_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

"""
Database manager for FloatChat application.
"""
import logging
from typing import List, Dict, Optional, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from datetime import datetime, timedelta

from .models import Base, ARGOFloat, ARGOProfile, ARGOMeasurement, ARGOTrajectory, QueryLog, DataSummary
from ..config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations for FloatChat."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=Config.DEBUG)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def store_float_metadata(self, float_data: Dict[str, Any]) -> str:
        """Store ARGO float metadata."""
        session = self.get_session()
        try:
            float_record = ARGOFloat(
                float_id=float_data['float_id'],
                wmo_id=float_data.get('wmo_id', ''),
                institution=float_data.get('institution', ''),
                data_mode=float_data.get('data_mode', 'R'),
                deployment_date=float_data.get('deployment_date'),
                last_transmission=float_data.get('last_transmission'),
                status=float_data.get('status', 'active')
            )
            session.add(float_record)
            session.commit()
            return str(float_record.id)
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing float metadata: {e}")
            raise
        finally:
            session.close()
    
    def store_profile_data(self, profile_data: Dict[str, Any]) -> str:
        """Store ARGO profile data."""
        session = self.get_session()
        try:
            profile_record = ARGOProfile(
                float_id=profile_data['float_id'],
                cycle_number=profile_data['cycle_number'],
                latitude=profile_data['latitude'],
                longitude=profile_data['longitude'],
                profile_time=profile_data['profile_time'],
                max_depth=profile_data.get('max_depth'),
                min_depth=profile_data.get('min_depth'),
                num_levels=profile_data.get('num_levels'),
                data_mode=profile_data.get('data_mode', 'R')
            )
            session.add(profile_record)
            session.commit()
            return str(profile_record.id)
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing profile data: {e}")
            raise
        finally:
            session.close()
    
    def store_measurements(self, measurements: List[Dict[str, Any]]) -> List[str]:
        """Store ARGO measurement data in bulk."""
        session = self.get_session()
        measurement_ids = []
        try:
            for measurement in measurements:
                measurement_record = ARGOMeasurement(
                    profile_id=measurement.get('profile_id'),
                    float_id=measurement['float_id'],
                    cycle_number=measurement['cycle_number'],
                    pressure=measurement.get('pressure'),
                    depth=measurement.get('depth'),
                    temperature=measurement.get('temperature'),
                    salinity=measurement.get('salinity'),
                    oxygen=measurement.get('oxygen'),
                    chlorophyll=measurement.get('chlorophyll'),
                    backscatter=measurement.get('backscatter'),
                    nitrate=measurement.get('nitrate'),
                    ph=measurement.get('ph'),
                    temperature_qc=measurement.get('temperature_qc'),
                    salinity_qc=measurement.get('salinity_qc'),
                    oxygen_qc=measurement.get('oxygen_qc'),
                    chlorophyll_qc=measurement.get('chlorophyll_qc'),
                    backscatter_qc=measurement.get('backscatter_qc'),
                    nitrate_qc=measurement.get('nitrate_qc'),
                    ph_qc=measurement.get('ph_qc')
                )
                session.add(measurement_record)
                measurement_ids.append(str(measurement_record.id))
            
            session.commit()
            return measurement_ids
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing measurements: {e}")
            raise
        finally:
            session.close()
    
    def store_trajectory_data(self, trajectory_data: List[Dict[str, Any]]) -> List[str]:
        """Store ARGO trajectory data."""
        session = self.get_session()
        trajectory_ids = []
        try:
            for point in trajectory_data:
                trajectory_record = ARGOTrajectory(
                    float_id=point['float_id'],
                    latitude=point['latitude'],
                    longitude=point['longitude'],
                    trajectory_time=point['trajectory_time'],
                    cycle_number=point.get('cycle_number'),
                    data_mode=point.get('data_mode', 'R')
                )
                session.add(trajectory_record)
                trajectory_ids.append(str(trajectory_record.id))
            
            session.commit()
            return trajectory_ids
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing trajectory data: {e}")
            raise
        finally:
            session.close()
    
    def log_query(self, user_query: str, processed_query: str = None, 
                  sql_query: str = None, response: str = None, 
                  execution_time: float = None, success: bool = True, 
                  error_message: str = None):
        """Log user queries for analytics."""
        session = self.get_session()
        try:
            query_log = QueryLog(
                user_query=user_query,
                processed_query=processed_query,
                sql_query=sql_query,
                response=response,
                execution_time=execution_time,
                success=success,
                error_message=error_message
            )
            session.add(query_log)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error logging query: {e}")
        finally:
            session.close()
    
    def get_floats_by_region(self, min_lat: float, max_lat: float, 
                            min_lon: float, max_lon: float) -> pd.DataFrame:
        """Get floats in a specific geographic region."""
        session = self.get_session()
        try:
            query = text("""
                SELECT DISTINCT af.float_id, af.wmo_id, af.institution, af.status,
                       ap.latitude, ap.longitude, ap.profile_time
                FROM argo_floats af
                JOIN argo_profiles ap ON af.float_id = ap.float_id
                WHERE ap.latitude BETWEEN :min_lat AND :max_lat
                AND ap.longitude BETWEEN :min_lon AND :max_lon
                ORDER BY ap.profile_time DESC
            """)
            
            result = session.execute(query, {
                'min_lat': min_lat,
                'max_lat': max_lat,
                'min_lon': min_lon,
                'max_lon': max_lon
            })
            
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        except SQLAlchemyError as e:
            logger.error(f"Error getting floats by region: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_profiles_by_parameter(self, parameter: str, min_lat: float = None, 
                                 max_lat: float = None, min_lon: float = None, 
                                 max_lon: float = None, start_date: datetime = None,
                                 end_date: datetime = None) -> pd.DataFrame:
        """Get profiles filtered by parameter and optional geographic/temporal constraints."""
        session = self.get_session()
        try:
            # Build dynamic query based on available constraints
            where_conditions = []
            params = {}
            
            if min_lat is not None and max_lat is not None:
                where_conditions.append("ap.latitude BETWEEN :min_lat AND :max_lat")
                params['min_lat'] = min_lat
                params['max_lat'] = max_lat
            
            if min_lon is not None and max_lon is not None:
                where_conditions.append("ap.longitude BETWEEN :min_lon AND :max_lon")
                params['min_lon'] = min_lon
                params['max_lon'] = max_lon
            
            if start_date is not None:
                where_conditions.append("ap.profile_time >= :start_date")
                params['start_date'] = start_date
            
            if end_date is not None:
                where_conditions.append("ap.profile_time <= :end_date")
                params['end_date'] = end_date
            
            # Check if parameter exists in measurements
            if parameter in ['temperature', 'salinity', 'oxygen', 'chlorophyll', 'backscatter', 'nitrate', 'ph']:
                where_conditions.append(f"am.{parameter} IS NOT NULL")
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            query = text(f"""
                SELECT DISTINCT ap.float_id, ap.cycle_number, ap.latitude, ap.longitude,
                       ap.profile_time, ap.max_depth, ap.num_levels
                FROM argo_profiles ap
                JOIN argo_measurements am ON ap.float_id = am.float_id AND ap.cycle_number = am.cycle_number
                WHERE {where_clause}
                ORDER BY ap.profile_time DESC
            """)
            
            result = session.execute(query, params)
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        except SQLAlchemyError as e:
            logger.error(f"Error getting profiles by parameter: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_measurements_by_profile(self, float_id: str, cycle_number: int) -> pd.DataFrame:
        """Get all measurements for a specific profile."""
        session = self.get_session()
        try:
            query = text("""
                SELECT pressure, depth, temperature, salinity, oxygen, chlorophyll,
                       backscatter, nitrate, ph, temperature_qc, salinity_qc
                FROM argo_measurements
                WHERE float_id = :float_id AND cycle_number = :cycle_number
                ORDER BY pressure ASC
            """)
            
            result = session.execute(query, {
                'float_id': float_id,
                'cycle_number': cycle_number
            })
            
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        except SQLAlchemyError as e:
            logger.error(f"Error getting measurements by profile: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_float_trajectory(self, float_id: str) -> pd.DataFrame:
        """Get trajectory data for a specific float."""
        session = self.get_session()
        try:
            query = text("""
                SELECT latitude, longitude, trajectory_time, cycle_number
                FROM argo_trajectories
                WHERE float_id = :float_id
                ORDER BY trajectory_time ASC
            """)
            
            result = session.execute(query, {'float_id': float_id})
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        except SQLAlchemyError as e:
            logger.error(f"Error getting float trajectory: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the database."""
        session = self.get_session()
        try:
            summary = {}
            
            # Count floats
            float_count = session.query(ARGOFloat).count()
            summary['total_floats'] = float_count
            
            # Count profiles
            profile_count = session.query(ARGOProfile).count()
            summary['total_profiles'] = profile_count
            
            # Count measurements
            measurement_count = session.query(ARGOMeasurement).count()
            summary['total_measurements'] = measurement_count
            
            # Geographic bounds
            bounds_query = text("""
                SELECT MIN(latitude) as min_lat, MAX(latitude) as max_lat,
                       MIN(longitude) as min_lon, MAX(longitude) as max_lon
                FROM argo_profiles
            """)
            bounds_result = session.execute(bounds_query).fetchone()
            if bounds_result:
                summary['geographic_bounds'] = {
                    'min_lat': float(bounds_result.min_lat) if bounds_result.min_lat else None,
                    'max_lat': float(bounds_result.max_lat) if bounds_result.max_lat else None,
                    'min_lon': float(bounds_result.min_lon) if bounds_result.min_lon else None,
                    'max_lon': float(bounds_result.max_lon) if bounds_result.max_lon else None
                }
            
            # Date range
            date_query = text("""
                SELECT MIN(profile_time) as start_date, MAX(profile_time) as end_date
                FROM argo_profiles
            """)
            date_result = session.execute(date_query).fetchone()
            if date_result:
                summary['date_range'] = {
                    'start_date': date_result.start_date,
                    'end_date': date_result.end_date
                }
            
            return summary
        except SQLAlchemyError as e:
            logger.error(f"Error getting data summary: {e}")
            return {}
        finally:
            session.close()

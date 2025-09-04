"""
Script to populate the database with sample ARGO data for demonstration.
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import Config
from src.database.database_manager import DatabaseManager
from src.ai.vector_store import ARGOVectorStore
from src.ingestion.argo_ingestion import ARGODataIngestion

logging.basicConfig(level=logging.INFO)  # Fixed typo: basicBasicConfig -> basicConfig
logger = logging.getLogger(__name__)

def create_sample_data():
    """Create sample ARGO data for demonstration."""
    # Sample float metadata
    sample_floats = [
        {
            'id': str(uuid.uuid4()),  # Generate unique UUID for id
            'float_id': '2902116',
            'wmo_id': '2902116',
            'institution': 'INCOIS',
            'data_mode': 'R',
            'deployment_date': datetime(2023, 1, 15),
            'last_transmission': datetime(2024, 1, 15),
            'status': 'active',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'float_id': '2902117',
            'wmo_id': '2902117',
            'institution': 'INCOIS',
            'data_mode': 'R',
            'deployment_date': datetime(2023, 2, 20),
            'last_transmission': datetime(2024, 1, 10),
            'status': 'active',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'float_id': '2902118',
            'wmo_id': '2902118',
            'institution': 'CSIR-NIO',
            'data_mode': 'R',
            'deployment_date': datetime(2023, 3, 10),
            'last_transmission': datetime(2024, 1, 5),
            'status': 'active',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    ]

    # Sample profile data
    sample_profiles = []
    sample_measurements = []
    sample_trajectories = []

    # Generate data for each float
    for float_data in sample_floats:
        float_id = float_data['float_id']

        # Generate 10 profiles per float
        for cycle in range(1, 11):
            # Random location in Indian Ocean
            lat = np.random.uniform(5, 25)
            lon = np.random.uniform(60, 90)

            # Random time within last year
            profile_time = datetime.now() - timedelta(days=np.random.randint(1, 365))

            # Create profile
            profile = {
                'float_id': float_id,
                'cycle_number': cycle,
                'latitude': lat,
                'longitude': lon,
                'profile_time': profile_time,
                'max_depth': np.random.uniform(1000, 2000),
                'min_depth': np.random.uniform(5, 20),
                'num_levels': np.random.randint(50, 200),
                'data_mode': 'R'
            }
            sample_profiles.append(profile)

            # Create trajectory point
            trajectory = {
                'float_id': float_id,
                'latitude': lat,
                'longitude': lon,
                'trajectory_time': profile_time,
                'cycle_number': cycle,
                'data_mode': 'R'
            }
            sample_trajectories.append(trajectory)

            # Generate measurements for this profile
            num_levels = profile['num_levels']
            pressures = np.linspace(profile['min_depth'], profile['max_depth'], num_levels)

            for i, pressure in enumerate(pressures):
                # Generate realistic oceanographic data
                temperature = 28 - (pressure / 100) * 0.1 + np.random.normal(0, 0.5)
                salinity = 35 + np.random.normal(0, 0.1)
                oxygen = 200 - (pressure / 100) * 2 + np.random.normal(0, 10)
                chlorophyll = max(0, 0.5 - (pressure / 100) * 0.01 + np.random.normal(0, 0.1))
                nitrate = 0.5 + (pressure / 100) * 0.02 + np.random.normal(0, 0.1)
                ph = 8.1 - (pressure / 100) * 0.001 + np.random.normal(0, 0.05)

                measurement = {
                    'float_id': float_id,
                    'cycle_number': cycle,
                    'pressure': pressure,
                    'depth': pressure * 1.02,  # Approximate depth from pressure
                    'temperature': temperature,
                    'salinity': salinity,
                    'oxygen': oxygen,
                    'chlorophyll': chlorophyll,
                    'nitrate': nitrate,
                    'ph': ph,
                    'temperature_qc': 1,
                    'salinity_qc': 1,
                    'oxygen_qc': 1,
                    'chlorophyll_qc': 1,
                    'nitrate_qc': 1,
                    'ph_qc': 1
                }
                sample_measurements.append(measurement)

    return sample_floats, sample_profiles, sample_measurements, sample_trajectories

def populate_database():
    """Populate the database with sample data."""
    try:
        # Initialize components
        db_manager = DatabaseManager()
        vector_store = ARGOVectorStore()

        # Create tables
        logger.info("Creating database tables...")
        db_manager.create_tables()

        # Generate sample data
        logger.info("Generating sample data...")
        floats, profiles, measurements, trajectories = create_sample_data()

        # Create a SQLAlchemy session
        # Assuming DatabaseManager has an engine attribute; adjust if different
        Session = sessionmaker(bind=db_manager.engine)  # Adjust if engine is accessed differently
        session = Session()

        # Store float metadata with upsert
        logger.info("Storing float metadata...")
        try:
            for float_data in floats:
                try:
                    stmt = insert(db_manager.ArgoFloat).values(float_data).on_conflict_do_update(
                        index_elements=['float_id'],  # Unique constraint column
                        set_={  # Fields to update if conflict occurs
                            'wmo_id': float_data['wmo_id'],
                            'institution': float_data['institution'],
                            'data_mode': float_data['data_mode'],
                            'deployment_date': float_data['deployment_date'],
                            'last_transmission': float_data['last_transmission'],
                            'status': float_data['status'],
                            'updated_at': float_data['updated_at']
                        }
                    )
                    session.execute(stmt)
                    logger.info(f"Inserted or updated float with float_id {float_data['float_id']}.")
                except IntegrityError as e:
                    session.rollback()
                    logger.error(f"Error storing float_id {float_data['float_id']}: {e}")
                    continue
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error during float metadata storage: {e}")
            raise
        finally:
            session.close()

        # Store profile data
        logger.info("Storing profile data...")
        for profile in profiles:
            db_manager.store_profile_data(profile)

        # Store measurements
        logger.info("Storing measurements...")
        db_manager.store_measurements(measurements)

        # Store trajectories
        logger.info("Storing trajectory data...")
        db_manager.store_trajectory_data(trajectories)

        # Create vector store documents
        logger.info("Creating vector store documents...")

        # Create profile documents for vector store
        profile_docs = []
        for profile in profiles:
            # Find corresponding float data
            float_data = next(f for f in floats if f['float_id'] == profile['float_id'])

            # Get measurements for this profile
            profile_measurements = [m for m in measurements
                                  if m['float_id'] == profile['float_id'] and m['cycle_number'] == profile['cycle_number']]

            # Determine available parameters
            available_params = []
            if any(m['temperature'] is not None for m in profile_measurements):
                available_params.append('temperature')
            if any(m['salinity'] is not None for m in profile_measurements):
                available_params.append('salinity')
            if any(m['oxygen'] is not None for m in profile_measurements):
                available_params.append('oxygen')
            if any(m['chlorophyll'] is not None for m in profile_measurements):
                available_params.append('chlorophyll')
            if any(m['nitrate'] is not None for m in profile_measurements):
                available_params.append('nitrate')
            if any(m['ph'] is not None for m in profile_measurements):
                available_params.append('ph')

            profile_doc = {
                'float_id': profile['float_id'],
                'cycle_number': profile['cycle_number'],
                'latitude': profile['latitude'],
                'longitude': profile['longitude'],
                'profile_time': profile['profile_time'],
                'max_depth': profile['max_depth'],
                'num_levels': profile['num_levels'],
                'parameters': available_params
            }
            profile_docs.append(profile_doc)

        # Add to vector store
        vector_store.add_profile_documents(profile_docs)

        # Create float documents for vector store
        float_docs = []
        for float_data in floats:
            # Count profiles for this float
            profile_count = len([p for p in profiles if p['float_id'] == float_data['float_id']])

            # Get latest profile
            latest_profile = next((p for p in profiles if p['float_id'] == float_data['float_id']), None)

            float_doc = {
                'float_id': float_data['float_id'],
                'wmo_id': float_data['wmo_id'],
                'institution': float_data['institution'],
                'status': float_data['status'],
                'deployment_date': float_data['deployment_date'],
                'last_transmission': float_data['last_transmission'],
                'total_profiles': profile_count,
                'latitude': latest_profile['latitude'] if latest_profile else 0,
                'longitude': latest_profile['longitude'] if latest_profile else 0
            }
            float_docs.append(float_doc)

        # Add to vector store
        vector_store.add_float_documents(float_docs)

        logger.info("Database population completed successfully!")

        # Print summary
        summary = db_manager.get_data_summary()
        print(f"\nDatabase Summary:")
        print(f"Total Floats: {summary.get('total_floats', 0)}")
        print(f"Total Profiles: {summary.get('total_profiles', 0)}")
        print(f"Total Measurements: {summary.get('total_measurements', 0)}")

        vector_stats = vector_store.get_collection_stats()
        print(f"\nVector Store Summary:")
        print(f"Profile Documents: {vector_stats.get('profiles', {}).get('count', 0)}")
        print(f"Float Documents: {vector_stats.get('floats', {}).get('count', 0)}")

    except Exception as e:
        logger.error(f"Error populating database: {e}")
        raise

if __name__ == "__main__":
    populate_database()

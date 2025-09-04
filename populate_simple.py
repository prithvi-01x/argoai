#!/usr/bin/env python
"""
Simple script to populate the database with sample ARGO data.
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.database_manager import DatabaseManager
from src.ai.vector_store import ARGOVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_data():
    """Create sample ARGO data for demonstration."""
    # Sample float metadata
    sample_floats = [
        {
            'float_id': '2902116',
            'wmo_id': '2902116',
            'institution': 'INCOIS',
            'data_mode': 'R',
            'deployment_date': datetime(2023, 1, 15),
            'last_transmission': datetime(2024, 1, 15),
            'status': 'active'
        },
        {
            'float_id': '2902117',
            'wmo_id': '2902117',
            'institution': 'INCOIS',
            'data_mode': 'R',
            'deployment_date': datetime(2023, 2, 20),
            'last_transmission': datetime(2024, 1, 10),
            'status': 'active'
        },
        {
            'float_id': '2902118',
            'wmo_id': '2902118',
            'institution': 'CSIR-NIO',
            'data_mode': 'R',
            'deployment_date': datetime(2023, 3, 10),
            'last_transmission': datetime(2024, 1, 5),
            'status': 'active'
        }
    ]

    # Sample profile data
    sample_profiles = []
    sample_measurements = []
    sample_trajectories = []

    # Generate data for each float
    for float_data in sample_floats:
        float_id = float_data['float_id']

        # Generate 5 profiles per float
        for cycle in range(1, 6):
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
                'num_levels': np.random.randint(50, 100),
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

                # Convert NumPy types to Python native types to avoid PostgreSQL serialization issues
                measurement = {
                    'float_id': float_id,
                    'cycle_number': cycle,
                    'pressure': float(pressure),
                    'depth': float(pressure * 1.02),  # Approximate depth from pressure
                    'temperature': float(temperature),
                    'salinity': float(salinity),
                    'oxygen': float(oxygen),
                    'chlorophyll': float(chlorophyll),
                    'nitrate': float(nitrate),
                    'ph': float(ph),
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

        # Create tables
        logger.info("Creating database tables...")
        db_manager.create_tables()

        # Generate sample data
        logger.info("Generating sample data...")
        floats, profiles, measurements, trajectories = create_sample_data()

        # Store float metadata
        logger.info("Storing float metadata...")
        for float_data in floats:
            try:
                float_id = db_manager.store_float_metadata(float_data)
                logger.info(f"Stored float {float_data['float_id']} with ID: {float_id}")
            except Exception as e:
                logger.error(f"Error storing float {float_data['float_id']}: {e}")

        # Store profile data and link measurements
        logger.info("Storing profile data...")
        profile_id_map = {}  # Map (float_id, cycle_number) to profile_id
        for profile in profiles:
            try:
                profile_id = db_manager.store_profile_data(profile)
                profile_id_map[(profile['float_id'], profile['cycle_number'])] = profile_id
                logger.info(f"Stored profile for float {profile['float_id']}, cycle {profile['cycle_number']} with ID: {profile_id}")
            except Exception as e:
                logger.error(f"Error storing profile: {e}")

        # Update measurements with profile_ids
        logger.info("Linking measurements to profiles...")
        for measurement in measurements:
            key = (measurement['float_id'], measurement['cycle_number'])
            if key in profile_id_map:
                measurement['profile_id'] = profile_id_map[key]
            else:
                logger.warning(f"No profile found for float {measurement['float_id']}, cycle {measurement['cycle_number']}")

        # Store measurements
        logger.info("Storing measurements...")
        try:
            measurement_ids = db_manager.store_measurements(measurements)
            logger.info(f"Stored {len(measurement_ids)} measurements")
        except Exception as e:
            logger.error(f"Error storing measurements: {e}")

        # Store trajectories
        logger.info("Storing trajectory data...")
        try:
            trajectory_ids = db_manager.store_trajectory_data(trajectories)
            logger.info(f"Stored {len(trajectory_ids)} trajectory points")
        except Exception as e:
            logger.error(f"Error storing trajectories: {e}")

        logger.info("Database population completed successfully!")

        # Print summary
        try:
            summary = db_manager.get_data_summary()
            print(f"\nDatabase Summary:")
            print(f"Total Floats: {summary.get('total_floats', 0)}")
            print(f"Total Profiles: {summary.get('total_profiles', 0)}")
            print(f"Total Measurements: {summary.get('total_measurements', 0)}")
        except Exception as e:
            print(f"Could not get summary: {e}")

    except Exception as e:
        logger.error(f"Error populating database: {e}")
        raise

if __name__ == "__main__":
    populate_database()

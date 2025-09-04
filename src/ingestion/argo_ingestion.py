"""
ARGO data ingestion pipeline for processing NetCDF files.
"""
import os
import ftplib
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ARGODataIngestion:
    """Handles ingestion of ARGO NetCDF data from various sources."""
    
    def __init__(self, data_dir: str = "./data/argo_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # ARGO data sources
        self.argo_ftp_url = "ftp.ifremer.fr"
        self.argo_ftp_path = "/ifremer/argo"
        self.indian_argo_url = "https://incois.gov.in/OON/index.jsp"
        
    def download_argo_data(self, region: str = "indian_ocean", 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[str]:
        """
        Download ARGO data from FTP server.
        
        Args:
            region: Region to download data for
            start_date: Start date for data download
            end_date: End date for data download
            
        Returns:
            List of downloaded file paths
        """
        downloaded_files = []
        
        try:
            # Connect to ARGO FTP server
            ftp = ftplib.FTP(self.argo_ftp_url)
            ftp.login()  # Anonymous login
            
            # Navigate to ARGO data directory
            ftp.cwd(self.argo_ftp_path)
            
            # Get list of available data
            files = []
            ftp.retrlines('LIST', files.append)
            
            # Filter for NetCDF files in the specified region
            nc_files = [f for f in files if f.endswith('.nc') and region in f.lower()]
            
            logger.info(f"Found {len(nc_files)} NetCDF files for {region}")
            
            # Download files
            for file_info in nc_files[:10]:  # Limit to first 10 files for demo
                filename = file_info.split()[-1]
                local_path = self.data_dir / filename
                
                if not local_path.exists():
                    with open(local_path, 'wb') as f:
                        ftp.retrbinary(f'RETR {filename}', f.write)
                    downloaded_files.append(str(local_path))
                    logger.info(f"Downloaded: {filename}")
                else:
                    logger.info(f"File already exists: {filename}")
            
            ftp.quit()
            
        except Exception as e:
            logger.error(f"Error downloading ARGO data: {e}")
            
        return downloaded_files
    
    def process_netcdf_file(self, file_path: str) -> Dict:
        """
        Process a single NetCDF file and extract relevant data.
        
        Args:
            file_path: Path to NetCDF file
            
        Returns:
            Dictionary containing processed data
        """
        try:
            # Open NetCDF file
            ds = xr.open_dataset(file_path)
            
            # Extract basic metadata
            metadata = {
                'file_path': file_path,
                'float_id': ds.attrs.get('PLATFORM_NUMBER', 'unknown'),
                'wmo_id': ds.attrs.get('WMO_INST_TYPE', 'unknown'),
                'institution': ds.attrs.get('institution', 'unknown'),
                'data_mode': ds.attrs.get('DATA_MODE', 'unknown'),
                'date_created': ds.attrs.get('DATE_CREATION', 'unknown'),
                'latitude': float(ds.LATITUDE.values[0]) if 'LATITUDE' in ds else None,
                'longitude': float(ds.LONGITUDE.values[0]) if 'LONGITUDE' in ds else None,
                'time': pd.to_datetime(ds.JULD.values[0]) if 'JULD' in ds else None,
            }
            
            # Extract profile data
            profile_data = {}
            
            # Temperature and salinity profiles
            if 'TEMP' in ds and 'PSAL' in ds:
                profile_data['temperature'] = ds.TEMP.values
                profile_data['salinity'] = ds.PSAL.values
                profile_data['pressure'] = ds.PRES.values if 'PRES' in ds else None
                profile_data['depth'] = ds.DEPTH.values if 'DEPTH' in ds else None
                
            # BGC parameters if available
            bgc_params = ['DOXY', 'CHLA', 'BBP700', 'NITRATE', 'PH_IN_SITU_TOTAL']
            for param in bgc_params:
                if param in ds:
                    profile_data[param.lower()] = ds[param].values
            
            # Quality flags
            quality_flags = {}
            for var in ds.data_vars:
                if 'QC' in var:
                    quality_flags[var] = ds[var].values
            
            return {
                'metadata': metadata,
                'profile_data': profile_data,
                'quality_flags': quality_flags,
                'raw_dataset': ds
            }
            
        except Exception as e:
            logger.error(f"Error processing NetCDF file {file_path}: {e}")
            return None
    
    def extract_float_trajectory(self, file_path: str) -> pd.DataFrame:
        """
        Extract float trajectory data from NetCDF file.
        
        Args:
            file_path: Path to NetCDF file
            
        Returns:
            DataFrame with trajectory data
        """
        try:
            ds = xr.open_dataset(file_path)
            
            trajectory_data = []
            
            if 'LATITUDE' in ds and 'LONGITUDE' in ds and 'JULD' in ds:
                for i in range(len(ds.LATITUDE)):
                    trajectory_data.append({
                        'float_id': ds.attrs.get('PLATFORM_NUMBER', 'unknown'),
                        'latitude': float(ds.LATITUDE.values[i]),
                        'longitude': float(ds.LONGITUDE.values[i]),
                        'time': pd.to_datetime(ds.JULD.values[i]),
                        'cycle_number': int(ds.CYCLE_NUMBER.values[i]) if 'CYCLE_NUMBER' in ds else i
                    })
            
            return pd.DataFrame(trajectory_data)
            
        except Exception as e:
            logger.error(f"Error extracting trajectory from {file_path}: {e}")
            return pd.DataFrame()
    
    def get_indian_ocean_floats(self) -> List[Dict]:
        """
        Get information about Indian Ocean ARGO floats from INCOIS.
        
        Returns:
            List of float information dictionaries
        """
        floats_info = []
        
        try:
            # This is a placeholder - in practice, you'd need to scrape or use API
            # from the Indian Argo project website
            
            # For demo purposes, return some sample data
            sample_floats = [
                {
                    'float_id': '2902116',
                    'wmo_id': '2902116',
                    'institution': 'INCOIS',
                    'deployment_date': '2023-01-15',
                    'last_transmission': '2024-01-15',
                    'latitude': 15.5,
                    'longitude': 73.5,
                    'status': 'active'
                },
                {
                    'float_id': '2902117',
                    'wmo_id': '2902117',
                    'institution': 'INCOIS',
                    'deployment_date': '2023-02-20',
                    'last_transmission': '2024-01-10',
                    'latitude': 12.0,
                    'longitude': 80.0,
                    'status': 'active'
                }
            ]
            
            floats_info.extend(sample_floats)
            
        except Exception as e:
            logger.error(f"Error getting Indian Ocean floats: {e}")
            
        return floats_info
    
    def create_data_summary(self, processed_data: List[Dict]) -> Dict:
        """
        Create a summary of processed ARGO data.
        
        Args:
            processed_data: List of processed data dictionaries
            
        Returns:
            Summary dictionary
        """
        if not processed_data:
            return {}
        
        summary = {
            'total_floats': len(processed_data),
            'date_range': {
                'start': min([d['metadata']['time'] for d in processed_data if d['metadata']['time']]),
                'end': max([d['metadata']['time'] for d in processed_data if d['metadata']['time']])
            },
            'geographic_bounds': {
                'min_lat': min([d['metadata']['latitude'] for d in processed_data if d['metadata']['latitude']]),
                'max_lat': max([d['metadata']['latitude'] for d in processed_data if d['metadata']['latitude']]),
                'min_lon': min([d['metadata']['longitude'] for d in processed_data if d['metadata']['longitude']]),
                'max_lon': max([d['metadata']['longitude'] for d in processed_data if d['metadata']['longitude']])
            },
            'parameters_available': set(),
            'institutions': set()
        }
        
        for data in processed_data:
            summary['parameters_available'].update(data['profile_data'].keys())
            summary['institutions'].add(data['metadata']['institution'])
        
        summary['parameters_available'] = list(summary['parameters_available'])
        summary['institutions'] = list(summary['institutions'])
        
        return summary

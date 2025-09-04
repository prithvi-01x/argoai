"""
Vector store implementation for ARGO data using ChromaDB.
"""
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import pandas as pd
from sentence_transformers import SentenceTransformer
import json

from ..config import Config

logger = logging.getLogger(__name__)

class ARGOVectorStore:
    """Vector store for ARGO data using ChromaDB."""
    
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or Config.CHROMA_PERSIST_DIRECTORY
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collections
        self.profiles_collection = self.client.get_or_create_collection(
            name="argo_profiles",
            metadata={"description": "ARGO profile metadata and summaries"}
        )
        
        self.floats_collection = self.client.get_or_create_collection(
            name="argo_floats",
            metadata={"description": "ARGO float information and trajectories"}
        )
        
        self.measurements_collection = self.client.get_or_create_collection(
            name="argo_measurements",
            metadata={"description": "ARGO measurement data summaries"}
        )
    
    def add_profile_documents(self, profiles: List[Dict[str, Any]]):
        """Add ARGO profile documents to the vector store."""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for profile in profiles:
                # Create document text
                doc_text = self._create_profile_document(profile)
                documents.append(doc_text)
                
                # Create metadata
                metadata = {
                    'float_id': profile.get('float_id', ''),
                    'cycle_number': profile.get('cycle_number', 0),
                    'latitude': profile.get('latitude', 0.0),
                    'longitude': profile.get('longitude', 0.0),
                    'profile_time': profile.get('profile_time', '').isoformat() if profile.get('profile_time') else '',
                    'max_depth': profile.get('max_depth', 0.0),
                    'num_levels': profile.get('num_levels', 0),
                    'parameters': json.dumps(profile.get('parameters', [])),
                    'region': self._get_region_name(profile.get('latitude', 0), profile.get('longitude', 0))
                }
                metadatas.append(metadata)
                
                # Create unique ID
                profile_id = f"{profile.get('float_id', '')}_{profile.get('cycle_number', 0)}"
                ids.append(profile_id)
            
            # Add to collection
            self.profiles_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(profiles)} profile documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding profile documents: {e}")
            raise
    
    def add_float_documents(self, floats: List[Dict[str, Any]]):
        """Add ARGO float documents to the vector store."""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for float_data in floats:
                # Create document text
                doc_text = self._create_float_document(float_data)
                documents.append(doc_text)
                
                # Create metadata
                metadata = {
                    'float_id': float_data.get('float_id', ''),
                    'wmo_id': float_data.get('wmo_id', ''),
                    'institution': float_data.get('institution', ''),
                    'status': float_data.get('status', ''),
                    'deployment_date': float_data.get('deployment_date', '').isoformat() if float_data.get('deployment_date') else '',
                    'last_transmission': float_data.get('last_transmission', '').isoformat() if float_data.get('last_transmission') else '',
                    'total_profiles': float_data.get('total_profiles', 0),
                    'region': self._get_region_name(float_data.get('latitude', 0), float_data.get('longitude', 0))
                }
                metadatas.append(metadata)
                
                ids.append(float_data.get('float_id', ''))
            
            # Add to collection
            self.floats_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(floats)} float documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding float documents: {e}")
            raise
    
    def search_profiles(self, query: str, n_results: int = 10, 
                       filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for ARGO profiles using semantic similarity."""
        try:
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if key in ['float_id', 'institution', 'status', 'region']:
                        where_clause[key] = value
                    elif key == 'latitude_range':
                        where_clause['latitude'] = {"$gte": value[0], "$lte": value[1]}
                    elif key == 'longitude_range':
                        where_clause['longitude'] = {"$gte": value[0], "$lte": value[1]}
            
            results = self.profiles_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'document': doc,
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'id': results['ids'][0][i]
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching profiles: {e}")
            return []
    
    def search_floats(self, query: str, n_results: int = 10, 
                     filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for ARGO floats using semantic similarity."""
        try:
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if key in ['float_id', 'institution', 'status', 'region']:
                        where_clause[key] = value
            
            results = self.floats_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'document': doc,
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'id': results['ids'][0][i]
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching floats: {e}")
            return []
    
    def _create_profile_document(self, profile: Dict[str, Any]) -> str:
        """Create a text document from profile data for embedding."""
        doc_parts = []
        
        # Basic information
        doc_parts.append(f"ARGO float {profile.get('float_id', 'unknown')}")
        doc_parts.append(f"Cycle number {profile.get('cycle_number', 0)}")
        
        # Location
        lat = profile.get('latitude', 0)
        lon = profile.get('longitude', 0)
        doc_parts.append(f"Located at {lat:.2f}°N, {lon:.2f}°E")
        
        # Region
        region = self._get_region_name(lat, lon)
        doc_parts.append(f"in the {region}")
        
        # Time
        if profile.get('profile_time'):
            doc_parts.append(f"Profile collected on {profile.get('profile_time')}")
        
        # Depth information
        if profile.get('max_depth'):
            doc_parts.append(f"Maximum depth {profile.get('max_depth')} meters")
        
        if profile.get('num_levels'):
            doc_parts.append(f"with {profile.get('num_levels')} measurement levels")
        
        # Parameters
        parameters = profile.get('parameters', [])
        if parameters:
            doc_parts.append(f"Parameters measured: {', '.join(parameters)}")
        
        return ". ".join(doc_parts) + "."
    
    def _create_float_document(self, float_data: Dict[str, Any]) -> str:
        """Create a text document from float data for embedding."""
        doc_parts = []
        
        # Basic information
        doc_parts.append(f"ARGO float {float_data.get('float_id', 'unknown')}")
        doc_parts.append(f"WMO ID {float_data.get('wmo_id', 'unknown')}")
        
        # Institution
        if float_data.get('institution'):
            doc_parts.append(f"Deployed by {float_data.get('institution')}")
        
        # Status
        if float_data.get('status'):
            doc_parts.append(f"Status: {float_data.get('status')}")
        
        # Location
        lat = float_data.get('latitude', 0)
        lon = float_data.get('longitude', 0)
        if lat and lon:
            doc_parts.append(f"Located at {lat:.2f}°N, {lon:.2f}°E")
            region = self._get_region_name(lat, lon)
            doc_parts.append(f"in the {region}")
        
        # Deployment information
        if float_data.get('deployment_date'):
            doc_parts.append(f"Deployed on {float_data.get('deployment_date')}")
        
        if float_data.get('last_transmission'):
            doc_parts.append(f"Last transmission on {float_data.get('last_transmission')}")
        
        # Profile count
        if float_data.get('total_profiles'):
            doc_parts.append(f"Has collected {float_data.get('total_profiles')} profiles")
        
        return ". ".join(doc_parts) + "."
    
    def _get_region_name(self, latitude: float, longitude: float) -> str:
        """Get region name based on coordinates."""
        if -10 <= latitude <= 30 and 40 <= longitude <= 100:
            return "Indian Ocean"
        elif 30 <= latitude <= 60 and -80 <= longitude <= -40:
            return "North Atlantic"
        elif -60 <= latitude <= -30 and -80 <= longitude <= -40:
            return "South Atlantic"
        elif 30 <= latitude <= 60 and 120 <= longitude <= 180:
            return "North Pacific"
        elif -60 <= latitude <= -30 and 120 <= longitude <= 180:
            return "South Pacific"
        elif -80 <= latitude <= -60:
            return "Southern Ocean"
        elif 60 <= latitude <= 80:
            return "Arctic Ocean"
        else:
            return "Global Ocean"
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collections."""
        try:
            stats = {}
            
            # Profile collection stats
            profile_count = self.profiles_collection.count()
            stats['profiles'] = {
                'count': profile_count,
                'collection_name': 'argo_profiles'
            }
            
            # Float collection stats
            float_count = self.floats_collection.count()
            stats['floats'] = {
                'count': float_count,
                'collection_name': 'argo_floats'
            }
            
            # Measurement collection stats
            measurement_count = self.measurements_collection.count()
            stats['measurements'] = {
                'count': measurement_count,
                'collection_name': 'argo_measurements'
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}

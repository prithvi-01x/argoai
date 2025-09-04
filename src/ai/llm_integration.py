"""
LLM integration using Google Gemini for natural language processing.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import google.generativeai as genai
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
import json
import re
import pandas as pd
from datetime import datetime, timedelta

from ..config import Config

logger = logging.getLogger(__name__)

class GeminiLLM:
    """Simple Gemini LLM wrapper for query processing."""
    
    def __init__(self, model_name: str = "gemini-pro"):
        self.model_name = model_name
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(model_name)
    
    def generate(self, prompt: str) -> str:
        """Generate response from Gemini model."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=Config.TEMPERATURE,
                    max_output_tokens=Config.MAX_TOKENS
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini model: {e}")
            return f"Error: {str(e)}"

class ARGOQueryProcessor:
    """Processes natural language queries about ARGO data."""
    
    def __init__(self):
        self.llm = GeminiLLM()
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for ARGO data query processing."""
        return """
You are an expert oceanographer and data analyst specializing in ARGO float data. 
Your task is to interpret natural language queries about oceanographic data and convert them into structured database queries.

ARGO Data Context:
- ARGO floats are autonomous profiling instruments that measure ocean properties
- Key parameters: temperature, salinity, pressure, depth, oxygen (DOXY), chlorophyll (CHLA), backscatter (BBP700), nitrate (NITRATE), pH
- Geographic regions: Indian Ocean, Atlantic, Pacific, Southern Ocean, Arctic
- Data includes float trajectories, profile measurements, and quality flags
- Time ranges typically span from deployment date to present

Query Processing Rules:
1. Identify the main oceanographic parameter(s) of interest
2. Extract geographic constraints (latitude/longitude ranges, region names)
3. Identify temporal constraints (date ranges, seasons, months)
4. Determine the type of analysis requested (profiles, trajectories, comparisons)
5. Map natural language to SQL query components

Common Query Patterns:
- "Show me salinity profiles near the equator" → parameter=salinity, lat_range=[-5,5]
- "Compare temperature in Arabian Sea" → parameter=temperature, region=Arabian Sea
- "ARGO floats in Indian Ocean last 6 months" → region=Indian Ocean, time_range=last 6 months
- "Nearest floats to this location" → geographic proximity search

Always respond with a JSON object containing:
{
    "intent": "profile_analysis|trajectory_analysis|float_search|comparison|summary",
    "parameters": ["list", "of", "parameters"],
    "geographic_constraints": {
        "min_lat": float,
        "max_lat": float,
        "min_lon": float,
        "max_lon": float,
        "region": "string"
    },
    "temporal_constraints": {
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "time_period": "string"
    },
    "analysis_type": "profiles|trajectories|measurements|comparison",
    "sql_components": {
        "select": "string",
        "from": "string", 
        "where": "string",
        "order_by": "string"
    },
    "confidence": float
}
"""
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process a natural language query and return structured information."""
        try:
            prompt = f"""
{self.system_prompt}

User Query: "{user_query}"

Please analyze this query and provide the structured response as JSON.
"""
            
            response = self.llm.generate(prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result['original_query'] = user_query
                result['processed_at'] = datetime.utcnow().isoformat()
                return result
            else:
                # Fallback parsing
                return self._fallback_parsing(user_query)
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return self._fallback_parsing(user_query)
    
    def _fallback_parsing(self, user_query: str) -> Dict[str, Any]:
        """Fallback parsing when LLM response is not in expected format."""
        query_lower = user_query.lower()
        
        # Basic parameter detection
        parameters = []
        if any(word in query_lower for word in ['temperature', 'temp']):
            parameters.append('temperature')
        if any(word in query_lower for word in ['salinity', 'salt']):
            parameters.append('salinity')
        if any(word in query_lower for word in ['oxygen', 'doxy']):
            parameters.append('oxygen')
        if any(word in query_lower for word in ['chlorophyll', 'chla']):
            parameters.append('chlorophyll')
        if any(word in query_lower for word in ['nitrate']):
            parameters.append('nitrate')
        if any(word in query_lower for word in ['ph', 'ph_in_situ']):
            parameters.append('ph')
        
        # Geographic region detection
        region = None
        if 'indian ocean' in query_lower:
            region = 'Indian Ocean'
        elif 'arabian sea' in query_lower:
            region = 'Arabian Sea'
        elif 'bay of bengal' in query_lower:
            region = 'Bay of Bengal'
        elif 'equator' in query_lower:
            region = 'Equatorial'
        
        # Intent detection
        intent = 'profile_analysis'
        if any(word in query_lower for word in ['trajectory', 'path', 'route']):
            intent = 'trajectory_analysis'
        elif any(word in query_lower for word in ['compare', 'comparison']):
            intent = 'comparison'
        elif any(word in query_lower for word in ['nearest', 'near', 'close']):
            intent = 'float_search'
        elif any(word in query_lower for word in ['summary', 'overview', 'statistics']):
            intent = 'summary'
        
        return {
            'intent': intent,
            'parameters': parameters,
            'geographic_constraints': {
                'region': region,
                'min_lat': None,
                'max_lat': None,
                'min_lon': None,
                'max_lon': None
            },
            'temporal_constraints': {
                'start_date': None,
                'end_date': None,
                'time_period': None
            },
            'analysis_type': 'profiles',
            'sql_components': {
                'select': '*',
                'from': 'argo_profiles',
                'where': '1=1',
                'order_by': 'profile_time DESC'
            },
            'confidence': 0.5,
            'original_query': user_query,
            'processed_at': datetime.utcnow().isoformat()
        }
    
    def generate_sql_query(self, processed_query: Dict[str, Any]) -> str:
        """Generate SQL query from processed query information."""
        try:
            intent = processed_query.get('intent', 'profile_analysis')
            parameters = processed_query.get('parameters', [])
            geo_constraints = processed_query.get('geographic_constraints', {})
            temp_constraints = processed_query.get('temporal_constraints', {})
            
            # Base query structure
            if intent == 'profile_analysis':
                base_query = """
                SELECT DISTINCT ap.float_id, ap.cycle_number, ap.latitude, ap.longitude,
                       ap.profile_time, ap.max_depth, ap.num_levels
                FROM argo_profiles ap
                """
                
                # Add parameter filtering if needed
                if parameters:
                    base_query += """
                    JOIN argo_measurements am ON ap.float_id = am.float_id 
                        AND ap.cycle_number = am.cycle_number
                    """
                
            elif intent == 'trajectory_analysis':
                base_query = """
                SELECT at.float_id, at.latitude, at.longitude, at.trajectory_time, at.cycle_number
                FROM argo_trajectories at
                """
                
            elif intent == 'float_search':
                base_query = """
                SELECT DISTINCT af.float_id, af.wmo_id, af.institution, af.status,
                       ap.latitude, ap.longitude, ap.profile_time
                FROM argo_floats af
                JOIN argo_profiles ap ON af.float_id = ap.float_id
                """
            
            else:
                base_query = """
                SELECT ap.float_id, ap.cycle_number, ap.latitude, ap.longitude, ap.profile_time
                FROM argo_profiles ap
                """
            
            # Build WHERE clause
            where_conditions = []
            
            # Geographic constraints
            if geo_constraints.get('min_lat') and geo_constraints.get('max_lat'):
                where_conditions.append(f"ap.latitude BETWEEN {geo_constraints['min_lat']} AND {geo_constraints['max_lat']}")
            
            if geo_constraints.get('min_lon') and geo_constraints.get('max_lon'):
                where_conditions.append(f"ap.longitude BETWEEN {geo_constraints['min_lon']} AND {geo_constraints['max_lon']}")
            
            # Temporal constraints
            if temp_constraints.get('start_date'):
                where_conditions.append(f"ap.profile_time >= '{temp_constraints['start_date']}'")
            
            if temp_constraints.get('end_date'):
                where_conditions.append(f"ap.profile_time <= '{temp_constraints['end_date']}'")
            
            # Parameter constraints
            if parameters and intent == 'profile_analysis':
                param_conditions = []
                for param in parameters:
                    if param == 'temperature':
                        param_conditions.append("am.temperature IS NOT NULL")
                    elif param == 'salinity':
                        param_conditions.append("am.salinity IS NOT NULL")
                    elif param == 'oxygen':
                        param_conditions.append("am.oxygen IS NOT NULL")
                    elif param == 'chlorophyll':
                        param_conditions.append("am.chlorophyll IS NOT NULL")
                    elif param == 'nitrate':
                        param_conditions.append("am.nitrate IS NOT NULL")
                    elif param == 'ph':
                        param_conditions.append("am.ph IS NOT NULL")
                
                if param_conditions:
                    where_conditions.append(f"({' OR '.join(param_conditions)})")
            
            # Combine WHERE clause
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            # Add ORDER BY
            base_query += " ORDER BY ap.profile_time DESC LIMIT 100"
            
            return base_query
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            return "SELECT * FROM argo_profiles LIMIT 10"
    
    def generate_response(self, query_result: pd.DataFrame, original_query: str, 
                         processed_query: Dict[str, Any]) -> str:
        """Generate natural language response from query results."""
        try:
            if query_result.empty:
                return "No ARGO data found matching your query criteria."
            
            # Create response prompt
            response_prompt = f"""
Based on the following ARGO data query results, provide a clear and informative response to the user's question.

Original Query: "{original_query}"

Query Results Summary:
- Number of records: {len(query_result)}
- Columns: {list(query_result.columns)}
- Sample data: {query_result.head(3).to_dict('records')}

Please provide a natural language response that:
1. Answers the user's question directly
2. Highlights key findings from the data
3. Mentions relevant statistics (number of profiles, geographic coverage, etc.)
4. Suggests follow-up questions if appropriate

Keep the response concise but informative, suitable for both scientists and general users.
"""
            
            response = self.llm.generate(response_prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Found {len(query_result)} ARGO profiles matching your query. Please refer to the data table for details."

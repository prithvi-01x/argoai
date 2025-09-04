"""
FloatChat - AI-Powered Conversational Interface for ARGO Ocean Data
Main Streamlit Application
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.database.database_manager import DatabaseManager
from src.ai.vector_store import ARGOVectorStore
from src.ai.rag_pipeline import ARGORAGPipeline
from src.visualization.argo_plots import ARGOVisualizer
from src.ingestion.argo_ingestion import ARGODataIngestion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="FloatChat - ARGO Ocean Data Explorer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_components():
    """Initialize database and AI components."""
    try:
        # Validate configuration
        Config.validate()
        
        # Initialize components
        db_manager = DatabaseManager()
        vector_store = ARGOVectorStore()
        rag_pipeline = ARGORAGPipeline(db_manager, vector_store)
        visualizer = ARGOVisualizer()
        data_ingestion = ARGODataIngestion()
        
        return db_manager, vector_store, rag_pipeline, visualizer, data_ingestion
    except Exception as e:
        st.error(f"Error initializing components: {e}")
        return None, None, None, None, None

def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">🌊 FloatChat</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-Powered Conversational Interface for ARGO Ocean Data Discovery and Visualization</p>', unsafe_allow_html=True)
    
    # Initialize components
    db_manager, vector_store, rag_pipeline, visualizer, data_ingestion = initialize_components()
    
    if not all([db_manager, vector_store, rag_pipeline, visualizer, data_ingestion]):
        st.error("Failed to initialize application components. Please check your configuration.")
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["🏠 Home", "💬 Chat Interface", "📊 Data Explorer", "🗺️ Map View", "📈 Profile Analysis", "⚙️ Settings"]
        )
        
        st.markdown("---")
        st.markdown("## 📊 Data Summary")
        
        # Get data summary
        try:
            summary = rag_pipeline.get_data_summary()
            if summary:
                db_summary = summary.get('database', {})
                st.metric("Total Floats", db_summary.get('total_floats', 0))
                st.metric("Total Profiles", db_summary.get('total_profiles', 0))
                st.metric("Total Measurements", db_summary.get('total_measurements', 0))
        except Exception as e:
            st.error(f"Error loading data summary: {e}")
    
    # Main content based on selected page
    if page == "🏠 Home":
        show_home_page(rag_pipeline, visualizer)
    elif page == "💬 Chat Interface":
        show_chat_interface(rag_pipeline, visualizer)
    elif page == "📊 Data Explorer":
        show_data_explorer(db_manager, visualizer)
    elif page == "🗺️ Map View":
        show_map_view(db_manager, visualizer)
    elif page == "📈 Profile Analysis":
        show_profile_analysis(db_manager, visualizer)
    elif page == "⚙️ Settings":
        show_settings_page(data_ingestion, db_manager)

def show_home_page(rag_pipeline, visualizer):
    """Display the home page."""
    st.markdown('<h2 class="sub-header">Welcome to FloatChat</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="info-box">
        <h3>🌊 About FloatChat</h3>
        <p>FloatChat is an AI-powered conversational interface that makes ARGO ocean data accessible through natural language queries. 
        Ask questions about oceanographic data in plain English and get instant insights with interactive visualizations.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <h3>🚀 Key Features</h3>
        <ul>
        <li><strong>Natural Language Queries:</strong> Ask questions like "Show me salinity profiles near the equator"</li>
        <li><strong>Interactive Maps:</strong> Visualize ARGO float locations and trajectories</li>
        <li><strong>Profile Analysis:</strong> Explore depth profiles of temperature, salinity, and other parameters</li>
        <li><strong>Real-time Data:</strong> Access the latest ARGO data from global repositories</li>
        <li><strong>AI-Powered Insights:</strong> Get intelligent responses and data summaries</li>
        </ul>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🎯 Quick Start")
        
        # Example queries
        example_queries = [
            "Show me temperature profiles in the Indian Ocean",
            "Find ARGO floats near the Arabian Sea",
            "Compare salinity data from different regions",
            "What are the latest measurements from active floats?",
            "Show me the trajectory of float 2902116"
        ]
        
        for query in example_queries:
            if st.button(f"💡 {query}", key=f"example_{query}"):
                st.session_state.example_query = query
                st.rerun()
        
        # Data ingestion status
        st.markdown("### 📥 Data Status")
        try:
            summary = rag_pipeline.get_data_summary()
            if summary and summary.get('database'):
                st.success("✅ Database connected")
                st.success("✅ Vector store ready")
                st.success("✅ AI pipeline active")
            else:
                st.warning("⚠️ No data available")
        except Exception as e:
            st.error(f"❌ Error: {e}")

def show_chat_interface(rag_pipeline, visualizer):
    """Display the chat interface."""
    st.markdown('<h2 class="sub-header">💬 Chat with FloatChat</h2>', unsafe_allow_html=True)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display data if available
            if "data" in message and message["data"]:
                st.dataframe(pd.DataFrame(message["data"]))
            
            # Display visualizations if available
            if "visualization" in message and message["visualization"]:
                st.plotly_chart(message["visualization"], use_container_width=True)
    
    # Chat input
    if prompt := st.chat_input("Ask me about ARGO ocean data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("Processing your query..."):
                try:
                    result = rag_pipeline.process_query(prompt)
                    
                    if result['success']:
                        # Display response
                        st.markdown(result['response'])
                        
                        # Display data if available
                        if result['data']:
                            st.markdown("### 📊 Query Results")
                            df = pd.DataFrame(result['data'])
                            st.dataframe(df)
                            
                            # Create visualizations based on query type
                            if len(df) > 0:
                                create_query_visualizations(df, result, visualizer)
                        
                        # Add assistant message to chat history
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": result['response'],
                            "data": result['data']
                        })
                        
                    else:
                        st.error(result['response'])
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": result['response']
                        })
                        
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

def create_query_visualizations(df, result, visualizer):
    """Create visualizations based on query results."""
    try:
        processed_query = result.get('processed_query', {})
        intent = processed_query.get('intent', '')
        
        if intent == 'profile_analysis' and len(df) > 0:
            # Create map of profile locations
            if 'latitude' in df.columns and 'longitude' in df.columns:
                st.markdown("### 🗺️ Profile Locations")
                map_fig = visualizer.create_float_map(df)
                st.components.v1.html(map_fig._repr_html_(), height=400)
        
        elif intent == 'trajectory_analysis' and len(df) > 0:
            # Create trajectory map
            if 'latitude' in df.columns and 'longitude' in df.columns:
                st.markdown("### 🗺️ Float Trajectory")
                map_fig = visualizer.create_trajectory_map(df)
                st.components.v1.html(map_fig._repr_html_(), height=400)
        
        elif intent == 'float_search' and len(df) > 0:
            # Create float map
            if 'latitude' in df.columns and 'longitude' in df.columns:
                st.markdown("### 🗺️ Float Locations")
                map_fig = visualizer.create_float_map(df)
                st.components.v1.html(map_fig._repr_html_(), height=400)
        
    except Exception as e:
        logger.error(f"Error creating visualizations: {e}")

def show_data_explorer(db_manager, visualizer):
    """Display the data explorer page."""
    st.markdown('<h2 class="sub-header">📊 Data Explorer</h2>', unsafe_allow_html=True)
    
    # Data summary
    try:
        summary = db_manager.get_data_summary()
        if summary:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Floats", summary.get('total_floats', 0))
            with col2:
                st.metric("Total Profiles", summary.get('total_profiles', 0))
            with col3:
                st.metric("Total Measurements", summary.get('total_measurements', 0))
            with col4:
                if summary.get('date_range'):
                    date_range = summary['date_range']
                    st.metric("Date Range", f"{date_range['start_date']} to {date_range['end_date']}")
    except Exception as e:
        st.error(f"Error loading data summary: {e}")
    
    # Data filters
    st.markdown("### 🔍 Filter Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Geographic filters
        st.markdown("#### Geographic Region")
        use_region = st.checkbox("Filter by region")
        
        if use_region:
            min_lat = st.slider("Min Latitude", -90.0, 90.0, -10.0)
            max_lat = st.slider("Max Latitude", -90.0, 90.0, 30.0)
            min_lon = st.slider("Min Longitude", -180.0, 180.0, 40.0)
            max_lon = st.slider("Max Longitude", -180.0, 180.0, 100.0)
        else:
            min_lat = max_lat = min_lon = max_lon = None
    
    with col2:
        # Parameter filters
        st.markdown("#### Parameters")
        parameters = st.multiselect(
            "Select parameters:",
            ["temperature", "salinity", "oxygen", "chlorophyll", "nitrate", "ph"],
            default=["temperature", "salinity"]
        )
        
        # Time filters
        st.markdown("#### Time Range")
        use_time = st.checkbox("Filter by time")
        
        if use_time:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=365))
            end_date = st.date_input("End Date", value=datetime.now())
        else:
            start_date = end_date = None
    
    # Query data
    if st.button("🔍 Query Data"):
        try:
            with st.spinner("Querying data..."):
                # Get profiles by parameter
                if parameters:
                    result = db_manager.get_profiles_by_parameter(
                        parameter=parameters[0],
                        min_lat=min_lat,
                        max_lat=max_lat,
                        min_lon=min_lon,
                        max_lon=max_lon,
                        start_date=datetime.combine(start_date, datetime.min.time()) if start_date else None,
                        end_date=datetime.combine(end_date, datetime.max.time()) if end_date else None
                    )
                    
                    if not result.empty:
                        st.markdown("### 📊 Query Results")
                        st.dataframe(result)
                        
                        # Create visualizations
                        if 'latitude' in result.columns and 'longitude' in result.columns:
                            st.markdown("### 🗺️ Geographic Distribution")
                            map_fig = visualizer.create_float_map(result)
                            st.components.v1.html(map_fig._repr_html_(), height=400)
                    else:
                        st.warning("No data found matching the criteria.")
        except Exception as e:
            st.error(f"Error querying data: {e}")

def show_map_view(db_manager, visualizer):
    """Display the map view page."""
    st.markdown('<h2 class="sub-header">🗺️ Map View</h2>', unsafe_allow_html=True)
    
    # Map options
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### 🎛️ Map Controls")
        
        map_type = st.selectbox(
            "Map Type:",
            ["Float Locations", "Trajectories", "Parameter Distribution"]
        )
        
        if map_type == "Float Locations":
            show_trajectories = st.checkbox("Show Trajectories")
            show_parameters = st.checkbox("Color by Parameter")
            
            if show_parameters:
                parameter = st.selectbox(
                    "Parameter:",
                    ["temperature", "salinity", "oxygen", "chlorophyll"]
                )
        
        elif map_type == "Trajectories":
            float_id = st.text_input("Float ID (optional):")
        
        elif map_type == "Parameter Distribution":
            parameter = st.selectbox(
                "Parameter:",
                ["temperature", "salinity", "oxygen", "chlorophyll"]
            )
            depth_level = st.slider("Depth Level (dbar)", 0, 2000, 100)
    
    with col2:
        try:
            if map_type == "Float Locations":
                # Get float data
                result = db_manager.get_floats_by_region(-90, 90, -180, 180)
                
                if not result.empty:
                    map_fig = visualizer.create_float_map(result)
                    st.components.v1.html(map_fig._repr_html_(), height=600)
                else:
                    st.warning("No float data available.")
            
            elif map_type == "Trajectories":
                if float_id:
                    # Get trajectory for specific float
                    trajectory = db_manager.get_float_trajectory(float_id)
                    
                    if not trajectory.empty:
                        map_fig = visualizer.create_trajectory_map(trajectory, float_id)
                        st.components.v1.html(map_fig._repr_html_(), height=600)
                    else:
                        st.warning(f"No trajectory data found for float {float_id}.")
                else:
                    st.info("Please enter a Float ID to view trajectory.")
            
            elif map_type == "Parameter Distribution":
                st.info("Parameter distribution visualization coming soon!")
        
        except Exception as e:
            st.error(f"Error creating map: {e}")

def show_profile_analysis(db_manager, visualizer):
    """Display the profile analysis page."""
    st.markdown('<h2 class="sub-header">📈 Profile Analysis</h2>', unsafe_allow_html=True)
    
    # Profile selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🎯 Select Profile")
        
        # Get available profiles
        try:
            profiles = db_manager.get_profiles_by_parameter('temperature')
            
            if not profiles.empty:
                # Create profile options
                profile_options = []
                for _, row in profiles.head(20).iterrows():  # Limit to first 20
                    option = f"Float {row['float_id']} - Cycle {row['cycle_number']} ({row['profile_time']})"
                    profile_options.append((option, row))
                
                selected_option = st.selectbox(
                    "Choose a profile:",
                    [opt[0] for opt in profile_options]
                )
                
                if selected_option:
                    selected_profile = next(opt[1] for opt in profile_options if opt[0] == selected_option)
                    
                    # Get measurements for this profile
                    measurements = db_manager.get_measurements_by_profile(
                        selected_profile['float_id'],
                        selected_profile['cycle_number']
                    )
                    
                    if not measurements.empty:
                        # Parameter selection
                        available_params = [col for col in measurements.columns 
                                          if col not in ['pressure', 'depth'] and measurements[col].notna().any()]
                        
                        selected_params = st.multiselect(
                            "Select parameters to plot:",
                            available_params,
                            default=available_params[:2] if len(available_params) >= 2 else available_params
                        )
                        
                        # Create plots
                        if selected_params:
                            for param in selected_params:
                                st.markdown(f"### {param.title()} Profile")
                                fig = visualizer.create_profile_plot(
                                    measurements, param,
                                    selected_profile['float_id'],
                                    selected_profile['cycle_number']
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        
                        # T-S diagram if both temperature and salinity available
                        if 'temperature' in measurements.columns and 'salinity' in measurements.columns:
                            st.markdown("### Temperature-Salinity Diagram")
                            ts_fig = visualizer.create_ts_diagram(
                                measurements, selected_profile['float_id']
                            )
                            st.plotly_chart(ts_fig, use_container_width=True)
                    
                    else:
                        st.warning("No measurement data available for this profile.")
            else:
                st.warning("No profile data available.")
        
        except Exception as e:
            st.error(f"Error loading profiles: {e}")
    
    with col2:
        st.markdown("### 📊 Profile Information")
        
        if 'selected_profile' in locals():
            st.json({
                "Float ID": selected_profile['float_id'],
                "Cycle Number": selected_profile['cycle_number'],
                "Location": f"{selected_profile['latitude']:.2f}°N, {selected_profile['longitude']:.2f}°E",
                "Profile Time": str(selected_profile['profile_time']),
                "Max Depth": f"{selected_profile.get('max_depth', 'N/A')} dbar",
                "Number of Levels": selected_profile.get('num_levels', 'N/A')
            })

def show_settings_page(data_ingestion, db_manager):
    """Display the settings page."""
    st.markdown('<h2 class="sub-header">⚙️ Settings</h2>', unsafe_allow_html=True)
    
    # Data ingestion section
    st.markdown("### 📥 Data Ingestion")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Download ARGO Data")
        
        region = st.selectbox(
            "Select region:",
            ["indian_ocean", "global", "atlantic", "pacific"]
        )
        
        if st.button("📥 Download Data"):
            with st.spinner("Downloading ARGO data..."):
                try:
                    downloaded_files = data_ingestion.download_argo_data(region)
                    
                    if downloaded_files:
                        st.success(f"Downloaded {len(downloaded_files)} files")
                        
                        # Process files
                        processed_data = []
                        for file_path in downloaded_files:
                            processed = data_ingestion.process_netcdf_file(file_path)
                            if processed:
                                processed_data.append(processed)
                        
                        if processed_data:
                            st.success(f"Processed {len(processed_data)} files")
                            
                            # Store in database
                            for data in processed_data:
                                try:
                                    # Store float metadata
                                    float_id = data['metadata']['float_id']
                                    db_manager.store_float_metadata({
                                        'float_id': float_id,
                                        'wmo_id': data['metadata'].get('wmo_id', ''),
                                        'institution': data['metadata'].get('institution', ''),
                                        'data_mode': data['metadata'].get('data_mode', 'R'),
                                        'status': 'active'
                                    })
                                    
                                    # Store profile data
                                    profile_id = db_manager.store_profile_data({
                                        'float_id': float_id,
                                        'cycle_number': 1,  # Default cycle
                                        'latitude': data['metadata']['latitude'],
                                        'longitude': data['metadata']['longitude'],
                                        'profile_time': data['metadata']['time'],
                                        'max_depth': 2000,  # Default
                                        'num_levels': len(data['profile_data'].get('temperature', [])),
                                        'data_mode': data['metadata'].get('data_mode', 'R')
                                    })
                                    
                                    st.success(f"Stored data for float {float_id}")
                                    
                                except Exception as e:
                                    st.error(f"Error storing data: {e}")
                    else:
                        st.warning("No files downloaded")
                        
                except Exception as e:
                    st.error(f"Error downloading data: {e}")
    
    with col2:
        st.markdown("#### Database Management")
        
        if st.button("🗄️ Create Tables"):
            try:
                db_manager.create_tables()
                st.success("Database tables created successfully")
            except Exception as e:
                st.error(f"Error creating tables: {e}")
        
        if st.button("📊 Get Data Summary"):
            try:
                summary = db_manager.get_data_summary()
                st.json(summary)
            except Exception as e:
                st.error(f"Error getting summary: {e}")
    
    # Configuration section
    st.markdown("### ⚙️ Configuration")
    
    st.markdown("""
    <div class="info-box">
    <h4>Configuration Status</h4>
    <ul>
    <li><strong>Google API Key:</strong> {'✅ Configured' if Config.GOOGLE_API_KEY else '❌ Not configured'}</li>
    <li><strong>Database URL:</strong> {Config.DATABASE_URL}</li>
    <li><strong>Vector Store:</strong> {Config.CHROMA_PERSIST_DIRECTORY}</li>
    <li><strong>ARGO FTP:</strong> {Config.ARGO_FTP_URL}</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

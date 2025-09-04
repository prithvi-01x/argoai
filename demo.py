"""
Demo script for FloatChat - AI-Powered Conversational Interface for ARGO Ocean Data
"""
import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.database.database_manager import DatabaseManager
from src.ai.vector_store import ARGOVectorStore
from src.ai.rag_pipeline import ARGORAGPipeline
from src.visualization.argo_plots import ARGOVisualizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_argo_queries():
    """Demonstrate ARGO data queries using the RAG pipeline."""
    
    print("🌊 FloatChat Demo - ARGO Ocean Data Explorer")
    print("=" * 50)
    
    try:
        # Initialize components
        print("Initializing components...")
        db_manager = DatabaseManager()
        vector_store = ARGOVectorStore()
        rag_pipeline = ARGORAGPipeline(db_manager, vector_store)
        visualizer = ARGOVisualizer()
        
        print("✅ Components initialized successfully!")
        
        # Demo queries
        demo_queries = [
            "Show me temperature profiles in the Indian Ocean",
            "Find ARGO floats near the Arabian Sea",
            "What are the latest salinity measurements?",
            "Compare temperature data from different regions",
            "Show me the trajectory of float 2902116"
        ]
        
        print("\n🤖 Demo Queries:")
        print("-" * 30)
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n{i}. Query: {query}")
            print("Processing...")
            
            try:
                result = rag_pipeline.process_query(query)
                
                if result['success']:
                    print(f"✅ Response: {result['response']}")
                    
                    if result['data']:
                        print(f"📊 Found {len(result['data'])} records")
                        
                        # Show sample data
                        if len(result['data']) > 0:
                            print("Sample data:")
                            sample = result['data'][0]
                            for key, value in sample.items():
                                print(f"  {key}: {value}")
                    else:
                        print("📊 No data records found")
                else:
                    print(f"❌ Error: {result['response']}")
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
            
            print("-" * 30)
        
        # Data summary
        print("\n📊 Data Summary:")
        try:
            summary = rag_pipeline.get_data_summary()
            if summary:
                db_summary = summary.get('database', {})
                print(f"Total Floats: {db_summary.get('total_floats', 0)}")
                print(f"Total Profiles: {db_summary.get('total_profiles', 0)}")
                print(f"Total Measurements: {db_summary.get('total_measurements', 0)}")
                
                if db_summary.get('geographic_bounds'):
                    bounds = db_summary['geographic_bounds']
                    print(f"Geographic Coverage:")
                    print(f"  Latitude: {bounds.get('min_lat', 'N/A')} to {bounds.get('max_lat', 'N/A')}")
                    print(f"  Longitude: {bounds.get('min_lon', 'N/A')} to {bounds.get('max_lon', 'N/A')}")
                
                if db_summary.get('date_range'):
                    date_range = db_summary['date_range']
                    print(f"Date Range: {date_range.get('start_date', 'N/A')} to {date_range.get('end_date', 'N/A')}")
        except Exception as e:
            print(f"Error getting data summary: {e}")
        
        print("\n🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}")

def interactive_demo():
    """Interactive demo where user can ask questions."""
    
    print("\n🎮 Interactive Demo Mode")
    print("Type 'quit' to exit, 'help' for examples")
    print("-" * 40)
    
    try:
        # Initialize components
        db_manager = DatabaseManager()
        vector_store = ARGOVectorStore()
        rag_pipeline = ARGORAGPipeline(db_manager, vector_store)
        
        while True:
            query = input("\n🌊 Ask about ARGO data: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if query.lower() == 'help':
                print("\nExample queries:")
                print("- Show me temperature profiles in the Indian Ocean")
                print("- Find ARGO floats near the Arabian Sea")
                print("- What are the latest salinity measurements?")
                print("- Compare temperature data from different regions")
                continue
            
            if not query:
                continue
            
            print("Processing...")
            try:
                result = rag_pipeline.process_query(query)
                
                if result['success']:
                    print(f"\n🤖 {result['response']}")
                    
                    if result['data']:
                        print(f"\n📊 Found {len(result['data'])} records")
                        # Show first few records
                        for i, record in enumerate(result['data'][:3]):
                            print(f"  {i+1}. {record}")
                        if len(result['data']) > 3:
                            print(f"  ... and {len(result['data']) - 3} more")
                else:
                    print(f"\n❌ {result['response']}")
                    
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Interactive demo failed: {e}")

def main():
    """Main demo function."""
    print("FloatChat Demo - AI-Powered ARGO Ocean Data Explorer")
    print("=" * 60)
    
    # Check configuration
    try:
        Config.validate()
        print("✅ Configuration validated")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file and API keys")
        return
    
    # Run demo
    demo_argo_queries()
    
    # Ask if user wants interactive demo
    try:
        response = input("\n🎮 Would you like to try the interactive demo? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_demo()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()

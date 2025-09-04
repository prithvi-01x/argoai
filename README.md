# FloatChat - AI-Powered Conversational Interface for ARGO Ocean Data

FloatChat is an intelligent system that enables natural language querying and visualization of ARGO oceanographic data through an AI-powered conversational interface. Built with Google Gemini LLM and modern data processing tools, it democratizes access to complex oceanographic datasets.

## 🌊 Features

- **Natural Language Queries**: Ask questions about ocean data in plain English
- **ARGO Data Integration**: Processes NetCDF files from ARGO floats
- **Interactive Visualizations**: Geospatial maps, depth-time plots, and profile comparisons
- **RAG-Powered AI**: Uses Google Gemini with retrieval-augmented generation
- **Real-time Data**: Connects to latest ARGO data from ftp.ifremer.fr
- **Multi-modal Interface**: Chat interface, data explorer, and map views

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key
- PostgreSQL (optional, SQLite will be used by default)

### Installation

1. **Clone and setup**:
```bash
git clone <repository-url>
cd floatchat
python setup.py
```

2. **Configure environment**:
```bash
# Edit .env file with your API keys
GOOGLE_API_KEY=your_google_gemini_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/floatchat
```

3. **Populate with sample data**:
```bash
python scripts/populate_database.py
```

4. **Run the application**:
```bash
streamlit run app.py
```

5. **Try the demo**:
```bash
python demo.py
```

## 📁 Project Structure

```
floatchat/
├── data/                   # Data storage and processing
│   ├── chroma_db/         # Vector database storage
│   └── argo_data/         # ARGO NetCDF files
├── src/                    # Source code
│   ├── ingestion/         # Data ingestion pipeline
│   │   └── argo_ingestion.py
│   ├── database/          # Database models and operations
│   │   ├── models.py
│   │   └── database_manager.py
│   ├── ai/               # AI/LLM integration
│   │   ├── vector_store.py
│   │   ├── llm_integration.py
│   │   └── rag_pipeline.py
│   └── visualization/    # Plotting and visualization
│       └── argo_plots.py
├── scripts/              # Utility scripts
│   └── populate_database.py
├── app.py                # Main Streamlit application
├── demo.py              # Demo script
├── setup.py             # Setup script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🗄️ Data Sources

- **ARGO Global Data Repository**: ftp://ftp.ifremer.fr/ifremer/argo
- **Indian Argo Project**: https://incois.gov.in/OON/index.jsp

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: SQLAlchemy, FastAPI
- **Database**: PostgreSQL + ChromaDB
- **AI**: Google Gemini + LangChain
- **Visualization**: Plotly, Folium, Matplotlib
- **Data Processing**: xarray, pandas, netCDF4

## 💬 Example Queries

Try these natural language queries:

- "Show me salinity profiles near the equator in March 2023"
- "Compare BGC parameters in the Arabian Sea for the last 6 months"
- "What are the nearest ARGO floats to this location?"
- "Find temperature anomalies in the Indian Ocean"
- "Show me the trajectory of float 2902116"

## 🎯 Key Components

### 1. Data Ingestion Pipeline
- Downloads ARGO NetCDF files from FTP servers
- Processes and converts to structured formats
- Extracts metadata, profiles, and measurements

### 2. Vector Database
- Stores document embeddings using ChromaDB
- Enables semantic search of ARGO data
- Supports retrieval-augmented generation

### 3. RAG Pipeline
- Processes natural language queries
- Retrieves relevant context from vector store
- Generates SQL queries and responses using Google Gemini

### 4. Visualization Engine
- Interactive maps with Folium
- Profile plots with Plotly
- Time series and comparison charts

## 🔧 Configuration

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Optional
DATABASE_URL=postgresql://username:password@localhost:5432/floatchat
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
ARGO_FTP_URL=ftp://ftp.ifremer.fr/ifremer/argo
DEBUG=True
```

### Database Setup
The application supports both PostgreSQL and SQLite:
- **PostgreSQL**: For production use with better performance
- **SQLite**: For development and testing (default)

## 📊 Usage Examples

### Chat Interface
```python
# Ask natural language questions
"Show me temperature profiles in the Indian Ocean"
"Find floats with salinity data near the Arabian Sea"
"Compare oxygen levels across different regions"
```

### Data Explorer
- Filter by geographic region, time period, or parameters
- View tabular data with sorting and filtering
- Export results to CSV or other formats

### Map Visualization
- Interactive maps showing float locations
- Trajectory visualization for individual floats
- Parameter distribution heatmaps

## 🧪 Testing

Run the demo script to test functionality:
```bash
python demo.py
```

This will:
1. Initialize all components
2. Run sample queries
3. Display results and visualizations
4. Provide an interactive mode for testing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- ARGO Program for providing oceanographic data
- Google for Gemini AI capabilities
- Streamlit team for the excellent web framework
- The oceanographic research community

## 📞 Support

For questions or issues:
1. Check the documentation
2. Run the demo script
3. Review the example queries
4. Open an issue on GitHub

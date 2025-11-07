# Overview

This is a Streamlit-based web application for analyzing electricity consumption data from E3DC solar/battery systems. The application allows users to upload CSV files containing energy data (solar direct consumption, battery discharge, grid consumption, and household consumption), stores the data in a database, and provides analytical visualizations of the energy usage patterns. The primary focus is analyzing "Netzbezug" (grid consumption) to understand when and how much electricity is drawn from the power grid, with automatic conversion to kWh and cost calculation in Euros based on configurable electricity prices for different time intervals.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

**Technology**: Streamlit web framework
- **Decision**: Streamlit was chosen for rapid development of data-centric applications
- **Rationale**: Provides built-in UI components for file uploads, data visualization, and tabbed interfaces without requiring separate frontend/backend development
- **Key Features**: 
  - Tab-based navigation separating data upload from analysis
  - Responsive layout using Streamlit's column system
  - Integration with Plotly for interactive visualizations

## Backend Architecture

**Data Processing Pipeline**:
- **CSV Parser** (`parse_csv_file`): Handles E3DC-specific CSV format with semicolon delimiters and comma decimal separators
- **Column Normalization**: Maps German column names to standardized English database field names
- **Data Validation**: Checks for data quality issues (e.g., excessive NaN values in critical columns)
- **Timestamp Handling**: Converts German date format (DD.MM.YYYY HH:MM:SS) to Python datetime objects
- **Unit Conversion**: Automatically converts Watt-hour (Wh) values to Kilowatt-hours (kWh) by dividing by 1000
- **Cost Calculation**: Calculates electricity costs in Euros based on user-defined prices per kWh for different time intervals

**Architecture Pattern**: Service layer pattern
- `app.py`: Presentation layer (Streamlit UI)
- `data_processor.py`: Business logic layer (data transformation and calculations)
- `database.py`: Data access layer (ORM models and session management)

## Data Storage

**Technology**: SQLAlchemy ORM with relational database (PostgreSQL expected)

**Schema Design**:
- Single table `energy_data` with timestamp-indexed records
- Unique constraint on `zeitstempel` to prevent duplicate time entries
- Nullable numeric fields to handle incomplete data gracefully
- Auto-incrementing primary key for row identity

**Design Decision**: 
- **Upsert Strategy**: Delete existing records by timestamp before inserting new ones (prevents duplicates when re-uploading overlapping data)
- **Indexing**: Timestamp field indexed for efficient time-range queries

## External Dependencies

**Data Visualization**:
- **Plotly Express & Plotly Graph Objects**: Interactive charting library for time-series visualization
- Used for rendering energy consumption graphs and analysis dashboards

**Data Processing**:
- **Pandas**: Core data manipulation library
- Handles CSV parsing, datetime conversion, numeric type coercion, and data cleaning

**Web Framework**:
- **Streamlit**: Python-based web application framework
- Features used: file uploaders, tabs, columns, metrics, expanders, spinners, caching

**Database**:
- **SQLAlchemy**: SQL toolkit and ORM
- Provides database-agnostic interface (currently expects PostgreSQL via DATABASE_URL environment variable)
- Session management with connection pooling

**Environment Configuration**:
- Relies on `DATABASE_URL` environment variable for database connection
- Application fails gracefully if DATABASE_URL is not configured

**Key Integration Points**:
- CSV file upload expects E3DC export format (semicolon-separated, comma decimals, German date format)
- Database expects standard SQL database accessible via SQLAlchemy connection string
- Streamlit's caching decorator (`@st.cache_resource`) used for database engine singleton pattern
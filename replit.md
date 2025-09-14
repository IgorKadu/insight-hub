# Insight Hub - Fleet Monitoring System

## Overview

Insight Hub is a comprehensive fleet monitoring and analysis platform for municipal vehicles that processes real-time telematics data to provide intelligent insights about vehicle performance, compliance, and operational efficiency. The system processes CSV data uploads containing vehicle telemetry information and generates interactive dashboards, automated insights, and comparative analytics for fleet management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit-based multi-page web application
- **Structure**: Page-based navigation with modular components
- **Pages**: Dashboard, CSV Upload, Detailed Analysis, Vehicle Comparison, Automatic Insights
- **Visualization**: Plotly for interactive charts and graphs
- **Styling**: Custom CSS with responsive design

### Data Processing Pipeline
- **CSV Processor**: Handles upload and validation of telematics data files
- **Field Validation**: 25 required fields including vehicle data, GPS coordinates, driver info, and operational metrics
- **Data Storage**: Local CSV file storage in `/data/processed_data.csv`
- **Analysis Engine**: Real-time data analysis with filtering capabilities

### Core Components
- **DataAnalyzer**: Central class for data filtering, KPI calculations, and statistical analysis
- **InsightsGenerator**: Automated insight generation for performance, compliance, efficiency, and predictive analytics
- **FleetVisualizations**: Chart and graph generation using Plotly
- **CSVProcessor**: File upload validation and data structure verification

### Data Model
- **Vehicle Data**: License plate, asset ID, client information
- **Telemetry**: GPS coordinates, speed, ignition status, odometer readings
- **Operational**: Driver information, event types, battery levels, system status
- **Temporal**: Date/time stamps for GPS and GPRS communications

### Analytics Features
- **KPI Dashboard**: Real-time metrics for fleet performance
- **Filtering System**: Multi-dimensional filtering by client, vehicle, date range
- **Comparative Analysis**: Vehicle-to-vehicle performance comparison
- **Automated Insights**: Pattern recognition and recommendation generation
- **Compliance Monitoring**: Speed limits, operational hours, GPS coverage analysis

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive visualization library
- **numpy**: Numerical computing support

### Data Processing
- **datetime**: Date and time handling for temporal analysis
- **os**: File system operations for data storage
- **re**: Regular expressions for data validation

### File Storage
- **Local CSV Storage**: Processed data stored in local filesystem
- **Upload Directory**: Temporary file handling for CSV uploads
- **Data Persistence**: File-based data storage without external database

Note: The system currently uses local file storage but could be extended to integrate with PostgreSQL or other database systems for enhanced data persistence and multi-user support.
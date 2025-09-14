"""
Database models for fleet monitoring system
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class Client(Base):
    """Client/Customer table"""
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    vehicles = relationship("Vehicle", back_populates="client")
    telematics_data = relationship("TelematicsData", back_populates="client")

class Vehicle(Base):
    """Vehicle information table"""
    __tablename__ = 'vehicles'
    
    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String(20), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    asset_id = Column(String(50))  # ID do ativo
    driver_name = Column(String(255))  # Nome do motorista padrão
    vehicle_type = Column(String(100))  # Tipo de veículo
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="vehicles")
    telematics_data = relationship("TelematicsData", back_populates="vehicle")

class TelematicsData(Base):
    """Main telematics data table - stores all GPS and sensor data"""
    __tablename__ = 'telematics_data'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic identification
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False, index=True)
    plate = Column(String(20), nullable=False, index=True)
    asset_id = Column(String(50))
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    gprs_timestamp = Column(DateTime(timezone=True))
    
    # Location and GPS data
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(String(255))  # Localização formatted
    address = Column(Text)  # Endereço completo
    gps_quality = Column(Boolean, default=False)  # GPS signal quality
    gprs_quality = Column(Boolean, default=False)  # GPRS signal quality
    
    # Vehicle status
    speed_kmh = Column(Float, default=0.0)  # Velocidade em km/h
    ignition = Column(String(10))  # D=Dirigindo, L=Ligado, etc.
    driver_name = Column(String(255))  # Motorista
    blocked = Column(Boolean, default=False)  # Bloqueado
    
    # Event information
    event_type = Column(String(100))  # Tipo do Evento
    geofence = Column(String(255))  # Cerca eletrônica
    entry = Column(Boolean, default=False)  # Entrada
    exit = Column(Boolean, default=False)  # Saída
    
    # Technical data
    packet_id = Column(String(50))  # ID do pacote
    odometer_period_km = Column(Float, default=0.0)  # Odômetro do período
    engine_hours_period = Column(String(20))  # Horímetro do período
    engine_hours_total = Column(String(20))  # Horímetro embarcado
    odometer_total_km = Column(Float, default=0.0)  # Odômetro embarcado
    battery_level = Column(String(10))  # Nível da bateria
    voltage = Column(Float)  # Tensão
    image_url = Column(String(500))  # URL da imagem se disponível
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="telematics_data")
    vehicle = relationship("Vehicle", back_populates="telematics_data")

class ProcessingHistory(Base):
    """Track CSV file processing history"""
    __tablename__ = 'processing_history'
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    unique_vehicles = Column(Integer, default=0)
    unique_clients = Column(Integer, default=0)
    date_range_start = Column(DateTime(timezone=True))
    date_range_end = Column(DateTime(timezone=True))
    processing_status = Column(String(50), default='completed')  # completed, failed, processing
    error_message = Column(Text)
    file_size_bytes = Column(Integer)

class InsightData(Base):
    """Store generated insights and analysis results"""
    __tablename__ = 'insights'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=True)
    
    # Insight content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text)
    insight_type = Column(String(50), nullable=False)  # error, warning, info, success
    priority = Column(Integer, default=3)  # 1=alta, 2=média, 3=baixa, 4=info
    category = Column(String(100))  # compliance, efficiency, maintenance, etc.
    
    # Analysis metadata
    analysis_period_start = Column(DateTime(timezone=True))
    analysis_period_end = Column(DateTime(timezone=True))
    confidence_score = Column(Float)  # For ML-generated insights
    data_source = Column(String(100))  # manual, automated, ml_model
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Status tracking
    is_active = Column(Boolean, default=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(255))

class AlertConfiguration(Base):
    """Configuration for real-time alerts"""
    __tablename__ = 'alert_configurations'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=True)
    
    # Alert configuration
    alert_type = Column(String(100), nullable=False)  # speed_limit, geofence, maintenance
    threshold_value = Column(Float)
    threshold_operator = Column(String(10))  # >, <, =, >=, <=
    is_active = Column(Boolean, default=True)
    
    # Notification settings
    notification_channels = Column(Text)  # JSON array of notification methods
    cooldown_minutes = Column(Integer, default=15)  # Prevent spam
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))
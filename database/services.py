"""
Database service layer for fleet monitoring operations
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, Integer
from database.connection import get_db_session, close_db_session, initialize_database
from database.models import (
    Client, Vehicle, TelematicsData, ProcessingHistory, 
    InsightData, AlertConfiguration
)

class FleetDatabaseService:
    """Service class for all fleet monitoring database operations"""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self):
        if not initialize_database():
            raise Exception("Falha ao conectar com a base de dados")
        self.session = get_db_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            close_db_session(self.session)
    
    # Client operations
    def get_or_create_client(self, client_name: str) -> Client:
        """Get existing client or create new one"""
        client = self.session.query(Client).filter(Client.name == client_name).first()
        if not client:
            client = Client(name=client_name)
            self.session.add(client)
            self.session.flush()  # Get the ID
        return client
    
    def get_all_clients(self) -> List[Client]:
        """Get all clients"""
        return self.session.query(Client).all()
    
    # Vehicle operations
    def get_or_create_vehicle(self, plate: str, client_id: int, asset_id: str = None) -> Vehicle:
        """Get existing vehicle or create new one"""
        vehicle = self.session.query(Vehicle).filter(Vehicle.plate == plate).first()
        if not vehicle:
            vehicle = Vehicle(
                plate=plate,
                client_id=client_id,
                asset_id=asset_id
            )
            self.session.add(vehicle)
            self.session.flush()
        return vehicle
    
    def get_vehicles_by_client(self, client_id: int) -> List[Vehicle]:
        """Get all vehicles for a client"""
        return self.session.query(Vehicle).filter(Vehicle.client_id == client_id).all()
    
    def get_all_vehicles(self) -> List[Vehicle]:
        """Get all vehicles"""
        return self.session.query(Vehicle).all()
    
    # Telematics data operations
    def save_telematics_data_with_progress(self, data_records: List[Dict[str, Any]], progress_callback=None) -> int:
        """Save multiple telematics data records with progress callback"""
        records_saved = 0
        records_failed = 0
        total_records = len(data_records)
        
        # Process in batches to avoid memory issues
        batch_size = 50  # Smaller batch for more frequent progress updates
        for i in range(0, total_records, batch_size):
            batch = data_records[i:i + batch_size]
            batch_saved = 0
            
            try:
                for record in batch:
                    try:
                        # Validate timestamp before processing
                        timestamp = record.get('data')
                        if timestamp is None or pd.isna(timestamp):
                            records_failed += 1
                            continue
                        
                        # Get or create client and vehicle
                        client = self.get_or_create_client(record['cliente'])
                        vehicle = self.get_or_create_vehicle(
                            record['placa'], 
                            client.id, 
                            record.get('ativo')
                        )
                        
                        # Create telematics data record
                        telematics = TelematicsData(
                            client_id=client.id,
                            vehicle_id=vehicle.id,
                            plate=record['placa'],
                            asset_id=record.get('ativo'),
                            timestamp=timestamp,
                            gprs_timestamp=record.get('data_gprs'),
                            latitude=record.get('latitude'),
                            longitude=record.get('longitude'),
                            location=record.get('localizacao'),
                            address=record.get('endereco'),
                            gps_quality=record.get('gps', 0) == 1,
                            gprs_quality=record.get('gprs', 0) == 1,
                            speed_kmh=record.get('velocidade_km', 0.0),
                            ignition=record.get('ignicao'),
                            driver_name=record.get('motorista'),
                            blocked=record.get('bloqueado', 0) == 1,
                            event_type=record.get('tipo_evento'),
                            geofence=record.get('cerca'),
                            entry=record.get('entrada', 0) == 1,
                            exit=record.get('saida', 0) == 1,
                            packet_id=record.get('pacote'),
                            odometer_period_km=record.get('odometro_periodo_km', 0.0),
                            odometer_embedded_km=record.get('odometro_embarcado_km', 0.0),
                            hourmeter_period=record.get('horimetro_periodo'),
                            hourmeter_embedded=record.get('horimetro_embarcado'),
                            battery_voltage=record.get('bateria'),
                            voltage=record.get('tensao'),
                            image_url=record.get('imagem')
                        )
                        
                        self.session.add(telematics)
                        batch_saved += 1
                        records_saved += 1
                        
                        # Report progress every 10 records within batch
                        if progress_callback and records_saved % 10 == 0:
                            progress_callback(records_saved, total_records, "inserindo")
                        
                    except Exception as record_error:
                        records_failed += 1
                        print(f"Failed to save record: {str(record_error)[:200]}")
                        continue
                
                # Commit the batch
                self.session.commit()
                
                # Report progress after each batch
                if progress_callback:
                    progress_callback(records_saved, total_records, "inserindo")
                
            except Exception as batch_error:
                self.session.rollback()
                records_failed += batch_size
                print(f"Batch failed: {str(batch_error)[:200]}")
                continue
        
        print(f"Batch insertion completed: {records_saved} saved, {records_failed} failed")
        return records_saved
    
    def save_telematics_data(self, data_records: List[Dict[str, Any]]) -> int:
        """Save multiple telematics data records with proper error handling"""
        records_saved = 0
        records_failed = 0
        
        # Process in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(data_records), batch_size):
            batch = data_records[i:i + batch_size]
            batch_saved = 0
            
            try:
                for record in batch:
                    try:
                        # Validate timestamp before processing
                        timestamp = record.get('data')
                        if timestamp is None or pd.isna(timestamp):
                            records_failed += 1
                            continue
                        
                        # Get or create client and vehicle
                        client = self.get_or_create_client(record['cliente'])
                        vehicle = self.get_or_create_vehicle(
                            record['placa'], 
                            client.id, 
                            record.get('ativo')
                        )
                        
                        # Create telematics data record
                        telematics = TelematicsData(
                            client_id=client.id,
                            vehicle_id=vehicle.id,
                            plate=record['placa'],
                            asset_id=record.get('ativo'),
                            timestamp=timestamp,
                            gprs_timestamp=record.get('data_gprs'),
                            latitude=record.get('latitude'),
                            longitude=record.get('longitude'),
                            location=record.get('localizacao'),
                            address=record.get('endereco'),
                            gps_quality=record.get('gps', 0) == 1,
                            gprs_quality=record.get('gprs', 0) == 1,
                            speed_kmh=record.get('velocidade_km', 0.0),
                            ignition=record.get('ignicao'),
                            driver_name=record.get('motorista'),
                            blocked=record.get('bloqueado', 0) == 1,
                            event_type=record.get('tipo_evento'),
                            geofence=record.get('cerca'),
                            entry=record.get('entrada', 0) == 1,
                            exit=record.get('saida', 0) == 1,
                            packet_id=record.get('pacote'),
                            odometer_period_km=record.get('odometro_periodo_km', 0.0),
                            engine_hours_period=record.get('horimetro_periodo'),
                            engine_hours_total=record.get('horimetro_embarcado'),
                            odometer_total_km=record.get('odometro_embarcado_km', 0.0),
                            battery_level=record.get('bateria'),
                            voltage=record.get('tensao'),
                            image_url=record.get('imagem')
                        )
                        
                        self.session.add(telematics)
                        batch_saved += 1
                        
                    except Exception as e:
                        # Log individual record error but continue processing
                        print(f"Error processing record {record.get('placa', 'unknown')}: {str(e)}")
                        records_failed += 1
                        continue
                
                # Commit the batch
                self.session.commit()
                records_saved += batch_saved
                
            except Exception as e:
                # If batch commit fails, rollback and mark all batch records as failed
                print(f"Error committing batch {i//batch_size + 1}: {str(e)}")
                self.session.rollback()
                records_failed += len(batch)
        
        print(f"Migration complete: {records_saved} saved, {records_failed} failed")
        return records_saved
    
    def get_telematics_data(self, 
                           client_id: Optional[int] = None,
                           vehicle_id: Optional[int] = None,
                           plate: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           limit: Optional[int] = None) -> List[TelematicsData]:
        """Get telematics data with filters"""
        query = self.session.query(TelematicsData)
        
        if client_id:
            query = query.filter(TelematicsData.client_id == client_id)
        if vehicle_id:
            query = query.filter(TelematicsData.vehicle_id == vehicle_id)
        if plate:
            query = query.filter(TelematicsData.plate == plate)
        if start_date:
            query = query.filter(TelematicsData.timestamp >= start_date)
        if end_date:
            query = query.filter(TelematicsData.timestamp <= end_date)
        
        query = query.order_by(TelematicsData.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_telematics_dataframe(self, **filters) -> pd.DataFrame:
        """Get telematics data as pandas DataFrame"""
        data = self.get_telematics_data(**filters)
        
        if not data:
            return pd.DataFrame()
        
        # Convert to DataFrame with original column names for compatibility
        records = []
        for record in data:
            records.append({
                'cliente': record.client.name,
                'placa': record.plate,
                'ativo': record.asset_id,
                'data': record.timestamp,
                'data_gprs': record.gprs_timestamp,
                'velocidade_km': record.speed_kmh,
                'ignicao': record.ignition,
                'motorista': record.driver_name,
                'gps': 1 if record.gps_quality else 0,
                'gprs': 1 if record.gprs_quality else 0,
                'localizacao': record.location,
                'endereco': record.address,
                'tipo_evento': record.event_type,
                'cerca': record.geofence,
                'saida': 1 if record.exit else 0,
                'entrada': 1 if record.entry else 0,
                'pacote': record.packet_id,
                'odometro_periodo_km': record.odometer_period_km,
                'horimetro_periodo': record.engine_hours_period,
                'horimetro_embarcado': record.engine_hours_total,
                'odometro_embarcado_km': record.odometer_total_km,
                'bateria': record.battery_level,
                'imagem': record.image_url,
                'tensao': record.voltage,
                'bloqueado': 1 if record.blocked else 0,
                'latitude': record.latitude,
                'longitude': record.longitude
            })
        
        return pd.DataFrame(records)
    
    # Analytics and KPI methods
    def get_fleet_summary(self) -> Dict[str, Any]:
        """Get overall fleet summary statistics"""
        total_vehicles = self.session.query(Vehicle).count()
        total_clients = self.session.query(Client).count()
        
        # Get latest data period
        latest_data = self.session.query(
            func.min(TelematicsData.timestamp).label('start_date'),
            func.max(TelematicsData.timestamp).label('end_date'),
            func.count(TelematicsData.id).label('total_records')
        ).first()
        
        # Calculate average speed and total distance
        speed_stats = self.session.query(
            func.avg(TelematicsData.speed_kmh).label('avg_speed'),
            func.max(TelematicsData.speed_kmh).label('max_speed'),
            func.sum(TelematicsData.odometer_period_km).label('total_distance')
        ).first()
        
        # GPS coverage - simplified approach
        gps_coverage = self.session.query(
            func.avg(TelematicsData.gps_quality.cast(Integer)).label('gps_coverage')
        ).first()
        
        return {
            'total_vehicles': total_vehicles,
            'total_clients': total_clients,
            'total_records': latest_data.total_records if latest_data.total_records else 0,
            'start_date': latest_data.start_date,
            'end_date': latest_data.end_date,
            'avg_speed': round(speed_stats.avg_speed, 1) if speed_stats.avg_speed else 0,
            'max_speed': speed_stats.max_speed if speed_stats.max_speed else 0,
            'total_distance': round(speed_stats.total_distance, 1) if speed_stats.total_distance else 0,
            'gps_coverage': round(gps_coverage.gps_coverage * 100, 1) if gps_coverage.gps_coverage else 0
        }
    
    # Processing history operations
    def save_processing_history(self, 
                               filename: str,
                               records_processed: int,
                               records_failed: int = 0,
                               unique_vehicles: int = 0,
                               unique_clients: int = 0,
                               date_range_start: Optional[datetime] = None,
                               date_range_end: Optional[datetime] = None,
                               processing_status: str = 'completed',
                               error_message: Optional[str] = None,
                               file_size_bytes: Optional[int] = None) -> ProcessingHistory:
        """Save processing history record"""
        history = ProcessingHistory(
            filename=filename,
            records_processed=records_processed,
            records_failed=records_failed,
            unique_vehicles=unique_vehicles,
            unique_clients=unique_clients,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            processing_status=processing_status,
            error_message=error_message,
            file_size_bytes=file_size_bytes
        )
        
        self.session.add(history)
        self.session.flush()
        return history
    
    def get_processing_history(self, limit: int = 10) -> List[ProcessingHistory]:
        """Get recent processing history"""
        return (self.session.query(ProcessingHistory)
                .order_by(ProcessingHistory.upload_timestamp.desc())
                .limit(limit)
                .all())
    
    def clear_processing_history(self) -> int:
        """Clear all processing history"""
        count = self.session.query(ProcessingHistory).count()
        self.session.query(ProcessingHistory).delete()
        return count
    
    def clear_all_data(self) -> Dict[str, int]:
        """Clear all telematics data and processing history"""
        telematics_count = self.session.query(TelematicsData).count()
        history_count = self.session.query(ProcessingHistory).count()
        insights_count = self.session.query(InsightData).count()
        
        self.session.query(TelematicsData).delete()
        self.session.query(ProcessingHistory).delete()
        self.session.query(InsightData).delete()
        
        return {
            'telematics_records': telematics_count,
            'processing_history': history_count,
            'insights': insights_count
        }
    
    # Insights operations
    def save_insight(self, 
                    title: str,
                    description: str,
                    insight_type: str,
                    priority: int = 3,
                    recommendation: Optional[str] = None,
                    category: Optional[str] = None,
                    client_id: Optional[int] = None,
                    vehicle_id: Optional[int] = None,
                    confidence_score: Optional[float] = None,
                    data_source: str = 'automated') -> InsightData:
        """Save a new insight"""
        insight = InsightData(
            title=title,
            description=description,
            recommendation=recommendation,
            insight_type=insight_type,
            priority=priority,
            category=category,
            client_id=client_id,
            vehicle_id=vehicle_id,
            confidence_score=confidence_score,
            data_source=data_source
        )
        
        self.session.add(insight)
        self.session.flush()
        return insight
    
    def get_insights(self, 
                    category: Optional[str] = None,
                    client_id: Optional[int] = None,
                    vehicle_id: Optional[int] = None,
                    is_active: bool = True,
                    limit: int = 50) -> List[InsightData]:
        """Get insights with filters"""
        query = self.session.query(InsightData)
        
        if category:
            query = query.filter(InsightData.category == category)
        if client_id:
            query = query.filter(InsightData.client_id == client_id)
        if vehicle_id:
            query = query.filter(InsightData.vehicle_id == vehicle_id)
        if is_active is not None:
            query = query.filter(InsightData.is_active == is_active)
        
        return query.order_by(InsightData.created_at.desc()).limit(limit).all()
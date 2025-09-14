"""
Database manager for integrating with existing CSV processing workflow
"""
import os
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime
from database.services import FleetDatabaseService
from database.connection import initialize_database

class DatabaseManager:
    """Manager to integrate database operations with existing workflow"""
    
    @staticmethod
    def _safe_int_convert(value):
        """Safely convert value to int, handling special cases"""
        if pd.isna(value) or value is None or str(value).strip() == '':
            return 0
        try:
            # Handle special values like 'X, X, X, X'
            val_str = str(value).strip()
            if 'x' in val_str.lower() or ',' in val_str:
                return 0
            return int(float(val_str))  # float first to handle '1.0'
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def _safe_float_convert(value):
        """Safely convert value to float, handling special cases"""
        if pd.isna(value) or value is None or str(value).strip() == '':
            return 0.0
        try:
            # Handle special values like 'X, X, X, X'
            val_str = str(value).strip()
            if 'x' in val_str.lower() or val_str == '-':
                return 0.0
            # Remove any non-numeric characters except . and -
            val_str = ''.join(c for c in val_str if c.isdigit() or c in '.-')
            if not val_str or val_str == '.' or val_str == '-':
                return 0.0
            return float(val_str)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def migrate_csv_to_database(csv_file_path: str) -> Dict[str, Any]:
        """Migrate existing CSV data to database"""
        if not os.path.exists(csv_file_path):
            return {'success': False, 'error': f'File not found: {csv_file_path}'}
        
        try:
            # Try different separators and encodings with proper validation
            df = None
            separators = [',', ';']
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']
            
            for sep in separators:
                for enc in encodings:
                    try:
                        test_df = pd.read_csv(csv_file_path, sep=sep, encoding=enc)
                        # Validate that we have multiple columns (not just one big column)
                        if test_df.shape[1] > 1:
                            df = test_df
                            print(f"Successfully read CSV with separator='{sep}' and encoding='{enc}' - Shape: {df.shape}")
                            break
                        else:
                            print(f"Separator '{sep}' with encoding '{enc}' resulted in only {test_df.shape[1]} column(s) - trying next combination")
                    except Exception as e:
                        print(f"Failed with separator='{sep}' and encoding='{enc}': {str(e)[:100]}")
                        continue
                if df is not None:
                    break
            
            if df is None:
                return {'success': False, 'error': 'Could not read CSV file with any encoding/separator combination that produces multiple columns'}
            
            return DatabaseManager.migrate_csv_to_database_from_df(df, os.path.basename(csv_file_path))
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def migrate_csv_to_database_from_df(df: pd.DataFrame, filename: str = "uploaded_data.csv") -> Dict[str, Any]:
        """Migrate DataFrame to database"""
        try:
            # Normalize column names first - handle double spaces and irregular spacing
            df.columns = [' '.join(col.strip().split()) for col in df.columns]
            
            # Convert to database format
            records = []
            for _, row in df.iterrows():
                # Get client name with fallback
                cliente_name = row.get('cliente') or row.get('Cliente')
                if pd.isna(cliente_name) or cliente_name is None or str(cliente_name).strip() == '':
                    cliente_name = 'Cliente Desconhecido'  # Fallback
                
                # Get plate with fallback
                placa_value = row.get('placa') or row.get('Placa')
                if pd.isna(placa_value) or placa_value is None or str(placa_value).strip() == '':
                    continue  # Skip records without plate
                
                record = {
                    'cliente': str(cliente_name).strip(),
                    'placa': str(placa_value).strip(),
                    'ativo': row.get('ativo') or row.get('Ativo'),
                    'data': pd.to_datetime(row.get('data') or row.get('Data'), errors='coerce', dayfirst=True),
                    'data_gprs': pd.to_datetime(row.get('data_gprs') or row.get('Data (GPRS)'), errors='coerce', dayfirst=True),
                    'velocidade_km': DatabaseManager._safe_float_convert(row.get('velocidade_km') or row.get('Velocidade (Km)')),
                    'ignicao': row.get('ignicao') or row.get('Ignição'),
                    'motorista': row.get('motorista') or row.get('Motorista'),
                    'gps': DatabaseManager._safe_int_convert(row.get('gps') or row.get('GPS')),
                    'gprs': DatabaseManager._safe_int_convert(row.get('gprs') or row.get('Gprs')),
                    'localizacao': row.get('localizacao') or row.get('Localização'),
                    'endereco': row.get('endereco') or row.get('Endereço'),
                    'tipo_evento': row.get('tipo_evento') or row.get('Tipo do Evento'),
                    'cerca': row.get('cerca') or row.get('Cerca'),
                    'saida': DatabaseManager._safe_int_convert(row.get('saida') or row.get('Saida')),
                    'entrada': DatabaseManager._safe_int_convert(row.get('entrada') or row.get('Entrada')),
                    'pacote': row.get('pacote') or row.get('Pacote'),
                    'odometro_periodo_km': DatabaseManager._safe_float_convert(row.get('odometro_periodo_km') or row.get('Odômetro do período (Km)') or row.get('Odômetro do período  (Km)')),
                    'horimetro_periodo': row.get('horimetro_periodo') or row.get('Horímetro do período'),
                    'horimetro_embarcado': row.get('horimetro_embarcado') or row.get('Horímetro embarcado'),
                    'odometro_embarcado_km': DatabaseManager._safe_float_convert(row.get('odometro_embarcado_km') or row.get('Odômetro embarcado (Km)')),
                    'bateria': row.get('bateria') or row.get('Bateria'),
                    'imagem': row.get('imagem') or row.get('Imagem'),
                    'tensao': DatabaseManager._safe_float_convert(row.get('tensao') or row.get('Tensão')),
                    'bloqueado': DatabaseManager._safe_int_convert(row.get('bloqueado') or row.get('Bloqueado'))
                }
                
                # Add derived location data if available
                location_field = row.get('localizacao') or row.get('Localização')
                if pd.notna(location_field):
                    try:
                        location = str(location_field)
                        if ',' in location:
                            lat_str, lon_str = location.split(',')
                            record['latitude'] = float(lat_str.strip())
                            record['longitude'] = float(lon_str.strip())
                    except:
                        pass
                
                records.append(record)
            
            # Save to database
            with FleetDatabaseService() as db:
                records_saved = db.save_telematics_data(records)
                
                # Save processing history
                unique_vehicles = df[df.columns[df.columns.str.contains('placa|Placa', case=False)].tolist()[0]].nunique()
                unique_clients = df[df.columns[df.columns.str.contains('cliente|Cliente', case=False)].tolist()[0]].nunique()
                
                # Find date column
                date_col = None
                for col in df.columns:
                    if 'data' in col.lower() and 'gprs' not in col.lower():
                        date_col = col
                        break
                
                date_range = (None, None)
                if date_col and not df[date_col].isna().all():
                    # Parse dates with Brazilian format
                    date_series = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
                    date_range = (date_series.min(), date_series.max())
                
                db.save_processing_history(
                    filename=filename,
                    records_processed=records_saved,
                    unique_vehicles=unique_vehicles,
                    unique_clients=unique_clients,
                    date_range_start=pd.to_datetime(date_range[0]) if date_range[0] else None,
                    date_range_end=pd.to_datetime(date_range[1]) if date_range[1] else None,
                    file_size_bytes=len(str(df)) if df is not None else 0
                )
            
            return {
                'success': True,
                'records_processed': records_saved,
                'unique_vehicles': unique_vehicles,
                'unique_clients': unique_clients
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_dashboard_data(client_filter: Optional[str] = None,
                          vehicle_filter: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Get dashboard data with filters"""
        with FleetDatabaseService() as db:
            # Convert filter values to IDs if needed
            client_id = None
            vehicle_id = None
            
            if client_filter:
                clients = db.get_all_clients()
                for client in clients:
                    if client.name == client_filter:
                        client_id = client.id
                        break
            
            if vehicle_filter:
                vehicles = db.get_all_vehicles()
                for vehicle in vehicles:
                    if vehicle.plate == vehicle_filter:
                        vehicle_id = vehicle.id
                        break
            
            return db.get_telematics_dataframe(
                client_id=client_id,
                vehicle_id=vehicle_id,
                start_date=start_date,
                end_date=end_date
            )
    
    @staticmethod
    def get_fleet_summary() -> Dict[str, Any]:
        """Get fleet summary statistics"""
        with FleetDatabaseService() as db:
            return db.get_fleet_summary()
    
    @staticmethod
    def get_processing_history() -> List[Dict[str, Any]]:
        """Get processing history for display"""
        with FleetDatabaseService() as db:
            history = db.get_processing_history()
            return [
                {
                    'filename': h.filename,
                    'upload_timestamp': h.upload_timestamp,
                    'records_processed': h.records_processed,
                    'unique_vehicles': h.unique_vehicles,
                    'unique_clients': h.unique_clients,
                    'processing_status': h.processing_status,
                    'file_size_bytes': h.file_size_bytes
                }
                for h in history
            ]
    
    @staticmethod
    def clear_all_data() -> Dict[str, int]:
        """Clear all data from database"""
        with FleetDatabaseService() as db:
            return db.clear_all_data()
    
    @staticmethod
    def has_data() -> bool:
        """Check if database has any telematics data"""
        try:
            if not initialize_database():
                return False
            with FleetDatabaseService() as db:
                summary = db.get_fleet_summary()
                return summary['total_records'] > 0
        except:
            return False
    
    @staticmethod
    def get_client_list() -> List[str]:
        """Get list of all client names"""
        with FleetDatabaseService() as db:
            clients = db.get_all_clients()
            return [client.name for client in clients]
    
    @staticmethod
    def get_vehicle_list() -> List[str]:
        """Get list of all vehicle plates"""
        with FleetDatabaseService() as db:
            vehicles = db.get_all_vehicles()
            return [vehicle.plate for vehicle in vehicles]
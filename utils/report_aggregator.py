"""
Report Data Aggregator - Consolida dados filtrados de todos os painéis
"""
import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from utils.data_analyzer import DataAnalyzer
from utils.insights_generator import InsightsGenerator
import os
import sys

class ReportDataAggregator:
    """Agregador de dados para relatórios consolidados"""
    
    @staticmethod
    def capture_filter_state() -> Dict[str, Any]:
        """Captura estado de filtros dos painéis via session_state"""
        filters = {
            'client_filter': st.session_state.get('report_client_filter'),
            'vehicle_filter': st.session_state.get('report_vehicle_filter'),
            'start_date': st.session_state.get('report_start_date'),
            'end_date': st.session_state.get('report_end_date'),
            'period_days': st.session_state.get('report_period_days')
        }
        return filters
    
    @staticmethod
    def get_filtered_df(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Aplica filtros no DataFrame e normaliza datas"""
        if df.empty:
            return df
        
        df_filtered = df.copy()
        
        # Normalizar e converter coluna de data
        if 'data' in df_filtered.columns:
            df_filtered['data'] = pd.to_datetime(df_filtered['data'], errors='coerce')
            df_filtered = df_filtered.dropna(subset=['data'])
        
        # Aplicar filtro de cliente
        if filters.get('client_filter'):
            df_filtered = df_filtered[df_filtered['cliente'] == filters['client_filter']]
        
        # Aplicar filtro de veículo
        if filters.get('vehicle_filter'):
            df_filtered = df_filtered[df_filtered['placa'] == filters['vehicle_filter']]
        
        # Aplicar filtros de período
        if filters.get('period_days'):
            cutoff_date = datetime.now() - timedelta(days=filters['period_days'])
            if 'data' in df_filtered.columns and not df_filtered.empty:
                # Garantir compatibilidade timezone
                if hasattr(df_filtered['data'].dtype, 'tz') and df_filtered['data'].dtype.tz is not None:
                    from datetime import timezone
                    cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)
                else:
                    cutoff_date = cutoff_date.replace(tzinfo=None)
                df_filtered = df_filtered[df_filtered['data'] >= cutoff_date]
        
        # Aplicar filtros de data específicos
        if filters.get('start_date') and 'data' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['data'].dt.date >= filters['start_date']]
        
        if filters.get('end_date') and 'data' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['data'].dt.date <= filters['end_date']]
        
        return df_filtered
    
    @staticmethod
    def build_contexts(filtered_df: pd.DataFrame) -> Dict[str, Any]:
        """Produz contextos consolidados de todos os painéis"""
        contexts = {
            'kpis': {},
            'insights': [],
            'predictive': {'status': 'skipped', 'reason': 'Não aplicável'},
            'routes': {},
            'operational': {},
            'compliance': {}
        }
        
        if filtered_df.empty:
            return contexts
        
        try:
            # 1. KPIs e Métricas Principais (Análise Detalhada)
            analyzer = DataAnalyzer(filtered_df)
            contexts['kpis'] = analyzer.get_kpis() or {}
            
            # 2. Insights Automáticos 
            try:
                insights_generator = InsightsGenerator(analyzer)
                contexts['insights'] = insights_generator.generate_all_insights() or []
            except Exception as e:
                print(f"Erro ao gerar insights: {e}")
                contexts['insights'] = []
            
            # 3. Análise Preditiva (apenas se houver dados suficientes)
            if len(filtered_df) >= 50:
                try:
                    # Importação lazy para evitar falhas se scikit-learn não estiver disponível
                    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                    from utils.ml_predictive import PredictiveMaintenanceAnalyzer
                    
                    predictive_analyzer = PredictiveMaintenanceAnalyzer()
                    predictive_results = predictive_analyzer.analyze_vehicle_health(filtered_df)
                    contexts['predictive'] = predictive_results
                    
                except ImportError:
                    contexts['predictive'] = {
                        'status': 'skipped', 
                        'reason': 'Bibliotecas de ML não disponíveis'
                    }
                except Exception as e:
                    contexts['predictive'] = {
                        'status': 'error', 
                        'reason': f'Erro na análise: {str(e)[:100]}'
                    }
            else:
                contexts['predictive'] = {
                    'status': 'skipped', 
                    'reason': f'Dados insuficientes ({len(filtered_df)} registros, mínimo 50)'
                }
            
            # 4. Análise de Rotas (Mapa de Rotas)
            contexts['routes'] = ReportDataAggregator._build_routes_context(filtered_df)
            
            # 5. Controle Operacional
            contexts['operational'] = ReportDataAggregator._build_operational_context(filtered_df)
            
            # 6. Análise de Conformidade
            contexts['compliance'] = ReportDataAggregator._build_compliance_context(filtered_df)
            
        except Exception as e:
            print(f"Erro ao construir contextos: {e}")
        
        return contexts
    
    @staticmethod
    def _build_routes_context(df: pd.DataFrame) -> Dict[str, Any]:
        """Contexto de análise de rotas"""
        routes_context = {
            'total_valid_coords': 0,
            'geographic_center': None,
            'coverage_area': 0,
            'speed_violations_geo': 0
        }
        
        if 'latitude' in df.columns and 'longitude' in df.columns:
            valid_coords = df.dropna(subset=['latitude', 'longitude'])
            valid_coords = valid_coords[
                (valid_coords['latitude'] != 0) & 
                (valid_coords['longitude'] != 0) &
                (valid_coords['latitude'].between(-90, 90)) &
                (valid_coords['longitude'].between(-180, 180))
            ]
            
            if not valid_coords.empty:
                routes_context['total_valid_coords'] = len(valid_coords)
                routes_context['geographic_center'] = {
                    'lat': valid_coords['latitude'].mean(),
                    'lon': valid_coords['longitude'].mean()
                }
                
                # Calcular área de cobertura (aproximada)
                lat_range = valid_coords['latitude'].max() - valid_coords['latitude'].min()
                lon_range = valid_coords['longitude'].max() - valid_coords['longitude'].min()
                routes_context['coverage_area'] = lat_range * lon_range
                
                # Violações de velocidade geo-referenciadas
                speed_violations = valid_coords[valid_coords['velocidade_km'] > 80]
                routes_context['speed_violations_geo'] = len(speed_violations)
        
        return routes_context
    
    @staticmethod
    def _build_operational_context(df: pd.DataFrame) -> Dict[str, Any]:
        """Contexto de controle operacional"""
        operational = {
            'ignition_stats': {},
            'blocked_stats': {},
            'peak_activity': {},
            'battery_alerts': 0,
            'gps_quality': 0
        }
        
        # Status de ignição
        if 'ignicao' in df.columns:
            operational['ignition_stats'] = df['ignicao'].value_counts().to_dict()
        
        # Status de bloqueio
        if 'bloqueado' in df.columns:
            operational['blocked_stats'] = df['bloqueado'].value_counts().to_dict()
        
        # Análise temporal de atividade
        if 'data' in df.columns:
            df['hora'] = df['data'].dt.hour
            hourly_activity = df.groupby('hora').size()
            operational['peak_activity'] = {
                'hour': hourly_activity.idxmax(),
                'count': hourly_activity.max()
            }
        
        # Alertas de bateria
        if 'bateria' in df.columns:
            operational['battery_alerts'] = len(df[df['bateria'] < 12.0])
        
        # Qualidade GPS
        if 'gps' in df.columns:
            operational['gps_quality'] = (df['gps'].sum() / len(df)) * 100 if len(df) > 0 else 0
        
        return operational
    
    @staticmethod
    def _build_compliance_context(df: pd.DataFrame) -> Dict[str, Any]:
        """Contexto de análise de conformidade"""
        compliance = {
            'total_violations': 0,
            'critical_violations': 0,
            'compliance_rate': 100,
            'worst_vehicles': [],
            'speed_distribution': {}
        }
        
        if 'velocidade_km' in df.columns:
            # Violações de velocidade
            violations = df[df['velocidade_km'] > 80]
            critical_violations = df[df['velocidade_km'] > 100]
            
            compliance['total_violations'] = len(violations)
            compliance['critical_violations'] = len(critical_violations)
            compliance['compliance_rate'] = (1 - len(violations) / len(df)) * 100 if len(df) > 0 else 100
            
            # Piores veículos em compliance
            if not violations.empty:
                vehicle_violations = violations.groupby('placa').size().reset_index(name='violations')
                worst_vehicles = vehicle_violations.nlargest(5, 'violations')
                compliance['worst_vehicles'] = worst_vehicles.to_dict('records')
            
            # Distribuição de velocidades
            compliance['speed_distribution'] = {
                '0-30 km/h': len(df[df['velocidade_km'] <= 30]),
                '31-60 km/h': len(df[(df['velocidade_km'] > 30) & (df['velocidade_km'] <= 60)]),
                '61-80 km/h': len(df[(df['velocidade_km'] > 60) & (df['velocidade_km'] <= 80)]),
                '81-100 km/h': len(df[(df['velocidade_km'] > 80) & (df['velocidade_km'] <= 100)]),
                'Acima de 100 km/h': len(df[df['velocidade_km'] > 100])
            }
        
        return compliance
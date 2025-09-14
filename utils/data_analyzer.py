import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
sys.path.append('.')
from database.db_manager import DatabaseManager

class DataAnalyzer:
    """Classe para análise de dados de frota"""
    
    def __init__(self, df):
        """Inicializa o analisador com DataFrame"""
        self.df = df
        self.filtered_df = df.copy()
    
    @classmethod
    def from_database(cls, cliente=None, placa=None, data_inicio=None, data_fim=None):
        """Cria uma instância do analisador usando dados da base de dados"""
        try:
            # Verificar se há dados na base de dados
            if not DatabaseManager.has_data():
                # Fall back para dados em arquivo se disponível
                import os
                if os.path.exists('data/processed_data.csv'):
                    df = pd.read_csv('data/processed_data.csv')
                    # Converter data se necessário
                    if 'data' in df.columns:
                        df['data'] = pd.to_datetime(df['data'], errors='coerce')
                else:
                    # Criar DataFrame vazio com estrutura esperada
                    df = pd.DataFrame(columns=[
                        'cliente', 'placa', 'data', 'velocidade_km', 'odometro_periodo_km',
                        'gps', 'bloqueado', 'horimetro_periodo_horas'
                    ])
            else:
                # Buscar dados da base de dados com filtros
                df = DatabaseManager.get_dashboard_data(
                    client_filter=cliente if cliente != "Todos" else None,
                    vehicle_filter=placa if placa != "Todos" else None,
                    start_date=data_inicio,
                    end_date=data_fim
                )
            
            return cls(df)
        except Exception as e:
            # Em caso de erro, retornar analisador com DataFrame vazio
            empty_df = pd.DataFrame(columns=[
                'cliente', 'placa', 'data', 'velocidade_km', 'odometro_periodo_km',
                'gps', 'bloqueado', 'horimetro_periodo_horas'
            ])
            return cls(empty_df)
    
    def apply_filters(self, cliente=None, placa=None, data_inicio=None, data_fim=None):
        """Aplica filtros aos dados"""
        filtered = self.df.copy()
        
        if cliente and cliente != "Todos":
            filtered = filtered[filtered['cliente'] == cliente]
        
        if placa and placa != "Todos":
            filtered = filtered[filtered['placa'] == placa]
        
        if data_inicio:
            filtered = filtered[filtered['data'] >= pd.Timestamp(data_inicio)]
        
        if data_fim:
            filtered = filtered[filtered['data'] <= pd.Timestamp(data_fim)]
        
        self.filtered_df = filtered
        return filtered
    
    def get_kpis(self):
        """Calcula KPIs principais"""
        if self.filtered_df.empty:
            return {}
        
        df = self.filtered_df
        
        kpis = {
            'total_veiculos': df['placa'].nunique(),
            'total_registros': len(df),
            'velocidade_media': df['velocidade_km'].mean(),
            'velocidade_maxima': df['velocidade_km'].max(),
            'distancia_total': df['odometro_periodo_km'].sum(),
            'tempo_ativo_horas': df['horimetro_periodo_horas'].sum() if 'horimetro_periodo_horas' in df.columns else 0,
            'cobertura_gps': (df['gps'].sum() / len(df)) * 100,
            'veiculos_bloqueados': df['bloqueado'].sum(),
            'periodo_dias': (df['data'].max() - df['data'].min()).days + 1 if len(df) > 0 else 0
        }
        
        return kpis
    
    def get_speed_analysis(self):
        """Análise de velocidade"""
        df = self.filtered_df
        
        if df.empty:
            return {}
        
        # Definir faixas de velocidade
        conditions = [
            (df['velocidade_km'] == 0),
            (df['velocidade_km'] > 0) & (df['velocidade_km'] <= 40),
            (df['velocidade_km'] > 40) & (df['velocidade_km'] <= 60),
            (df['velocidade_km'] > 60) & (df['velocidade_km'] <= 80),
            (df['velocidade_km'] > 80)
        ]
        choices = ['Parado', 'Baixa (1-40)', 'Moderada (41-60)', 'Alta (61-80)', 'Muito Alta (80+)']
        
        df['faixa_velocidade'] = np.select(conditions, choices, default='Indefinido')
        
        speed_dist = df['faixa_velocidade'].value_counts()
        
        return {
            'distribuicao': speed_dist,
            'velocidade_media_por_veiculo': df.groupby('placa')['velocidade_km'].mean().sort_values(ascending=False),
            'velocidade_maxima_por_veiculo': df.groupby('placa')['velocidade_km'].max().sort_values(ascending=False),
            'velocidade_por_hora': df.groupby(df['data'].dt.hour)['velocidade_km'].mean()
        }
    
    def get_operational_analysis(self):
        """Análise operacional"""
        df = self.filtered_df
        
        if df.empty:
            return {}
        
        # Análise por veículo
        vehicle_stats = df.groupby('placa').agg({
            'velocidade_km': ['mean', 'max', 'count'],
            'odometro_periodo_km': 'sum',
            'horimetro_periodo_horas': 'sum' if 'horimetro_periodo_horas' in df.columns else lambda x: 0,
            'gps': 'mean',
            'bloqueado': 'any'
        }).round(2)
        
        # Achatamento do MultiIndex
        vehicle_stats.columns = ['_'.join(col) for col in vehicle_stats.columns]
        vehicle_stats = vehicle_stats.reset_index()
        
        # Análise temporal
        daily_stats = df.groupby(df['data'].dt.date).agg({
            'placa': 'nunique',
            'velocidade_km': 'mean',
            'odometro_periodo_km': 'sum'
        }).reset_index()
        
        # Análise de utilização por hora
        hourly_usage = df.groupby(df['data'].dt.hour).agg({
            'placa': 'nunique',
            'velocidade_km': 'mean'
        }).reset_index()
        
        return {
            'estatisticas_por_veiculo': vehicle_stats,
            'estatisticas_diarias': daily_stats,
            'utilizacao_por_hora': hourly_usage,
            'total_km_por_veiculo': df.groupby('placa')['odometro_periodo_km'].sum().sort_values(ascending=False)
        }
    
    def get_compliance_analysis(self):
        """Análise de compliance/conformidade"""
        df = self.filtered_df
        
        if df.empty:
            return {}
        
        # Definir limites de compliance
        SPEED_LIMIT = 80  # km/h
        MIN_GPS_COVERAGE = 95  # %
        
        # Análise de excesso de velocidade
        speed_violations = df[df['velocidade_km'] > SPEED_LIMIT]
        
        # Análise de cobertura GPS
        gps_coverage_by_vehicle = df.groupby('placa')['gps'].mean() * 100
        low_gps_vehicles = gps_coverage_by_vehicle[gps_coverage_by_vehicle < MIN_GPS_COVERAGE]
        
        # Veículos com problemas
        blocked_vehicles = df[df['bloqueado'] == True]['placa'].unique()
        
        # Score de compliance por veículo
        compliance_scores = {}
        for placa in df['placa'].unique():
            vehicle_data = df[df['placa'] == placa]
            
            # Pontuação baseada em critérios
            speed_score = 100 - (len(vehicle_data[vehicle_data['velocidade_km'] > SPEED_LIMIT]) / len(vehicle_data)) * 100
            gps_score = (vehicle_data['gps'].mean() * 100)
            block_score = 100 if not vehicle_data['bloqueado'].any() else 0
            
            overall_score = (speed_score * 0.4 + gps_score * 0.4 + block_score * 0.2)
            compliance_scores[placa] = round(overall_score, 2)
        
        return {
            'violacoes_velocidade': len(speed_violations),
            'veiculos_baixo_gps': len(low_gps_vehicles),
            'veiculos_bloqueados': len(blocked_vehicles),
            'score_compliance': compliance_scores,
            'detalhes_violacoes': speed_violations.groupby('placa').size().sort_values(ascending=False),
            'cobertura_gps_por_veiculo': gps_coverage_by_vehicle.sort_values(ascending=True)
        }
    
    def compare_vehicles(self, placas_list):
        """Compara múltiplos veículos"""
        if not placas_list or len(placas_list) < 2:
            return {}
        
        comparison_data = {}
        
        for placa in placas_list:
            vehicle_data = self.filtered_df[self.filtered_df['placa'] == placa]
            
            if not vehicle_data.empty:
                comparison_data[placa] = {
                    'total_registros': len(vehicle_data),
                    'velocidade_media': vehicle_data['velocidade_km'].mean(),
                    'velocidade_maxima': vehicle_data['velocidade_km'].max(),
                    'distancia_total': vehicle_data['odometro_periodo_km'].sum(),
                    'tempo_ativo': vehicle_data['horimetro_periodo_horas'].sum() if 'horimetro_periodo_horas' in vehicle_data.columns else 0,
                    'cobertura_gps': (vehicle_data['gps'].mean() * 100),
                    'violacoes_velocidade': len(vehicle_data[vehicle_data['velocidade_km'] > 80]),
                    'bloqueios': vehicle_data['bloqueado'].sum()
                }
        
        return comparison_data
    
    def get_temporal_patterns(self):
        """Análise de padrões temporais"""
        df = self.filtered_df
        
        if df.empty:
            return {}
        
        # Padrões por dia da semana
        df['dia_semana'] = df['data'].dt.day_name()
        weekly_patterns = df.groupby('dia_semana').agg({
            'velocidade_km': 'mean',
            'placa': 'nunique',
            'odometro_periodo_km': 'sum'
        })
        
        # Padrões por hora do dia
        hourly_patterns = df.groupby(df['data'].dt.hour).agg({
            'velocidade_km': 'mean',
            'placa': 'nunique',
            'odometro_periodo_km': 'sum'
        })
        
        # Padrões mensais
        monthly_patterns = df.groupby(df['data'].dt.to_period('M')).agg({
            'velocidade_km': 'mean',
            'placa': 'nunique',
            'odometro_periodo_km': 'sum'
        })
        
        return {
            'padroes_semanais': weekly_patterns,
            'padroes_por_hora': hourly_patterns,
            'padroes_mensais': monthly_patterns
        }
    
    def get_efficiency_metrics(self):
        """Métricas de eficiência"""
        df = self.filtered_df
        
        if df.empty:
            return {}
        
        # Eficiência por veículo
        vehicle_efficiency = df.groupby('placa').apply(
            lambda x: {
                'km_por_dia': x['odometro_periodo_km'].sum() / max(1, (x['data'].max() - x['data'].min()).days + 1),
                'utilizacao_diaria': len(x) / max(1, (x['data'].max() - x['data'].min()).days + 1),
                'velocidade_media': x['velocidade_km'].mean(),
                'tempo_parado_pct': (len(x[x['velocidade_km'] == 0]) / len(x)) * 100
            }
        )
        
        return {
            'eficiencia_por_veiculo': vehicle_efficiency,
            'top_veiculos_km': df.groupby('placa')['odometro_periodo_km'].sum().sort_values(ascending=False).head(10),
            'veiculos_mais_utilizados': df.groupby('placa').size().sort_values(ascending=False).head(10)
        }

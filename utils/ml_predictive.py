"""
Análise de Manutenção Preditiva usando Machine Learning
Detecta anomalias e prevê necessidades de manutenção
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

class PredictiveMaintenanceAnalyzer:
    """Análise de manutenção preditiva para frota"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.clusterer = DBSCAN(eps=0.5, min_samples=5)
        
    def analyze_vehicle_health(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análise completa de saúde do veículo"""
        if df.empty:
            return {'status': 'error', 'message': 'Sem dados disponíveis'}
            
        # Preparar features para ML
        features = self._prepare_features(df)
        if features.empty:
            return {'status': 'error', 'message': 'Dados insuficientes para análise'}
            
        # Detectar anomalias
        anomalies = self._detect_anomalies(features)
        
        # Análise de padrões
        patterns = self._analyze_patterns(df)
        
        # Previsões de manutenção
        maintenance_alerts = self._predict_maintenance_needs(df, anomalies)
        
        # Scores de saúde
        health_scores = self._calculate_health_scores(df, anomalies)
        
        return {
            'status': 'success',
            'health_scores': health_scores,
            'anomalies': anomalies,
            'patterns': patterns,
            'maintenance_alerts': maintenance_alerts,
            'recommendations': self._generate_recommendations(health_scores, maintenance_alerts)
        }
    
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preparar features para análise ML"""
        try:
            features_data = []
            
            # Converter campos numéricos primeiro
            numeric_columns = ['velocidade_km', 'bateria', 'tensao', 'odometro_periodo_km', 'horimetro_periodo']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Agrupar por hora para análise temporal
            df_hourly = df.groupby(df['data'].dt.floor('H')).agg({
                'velocidade_km': ['mean', 'max', 'std'],
                'bateria': 'mean',
                'tensao': 'mean',
                'odometro_periodo_km': 'sum',
                'horimetro_periodo': 'sum',
                'ignicao': lambda x: (x == 'Ligada').sum() / len(x) if len(x) > 0 else 0
            }).reset_index()
            
            # Flatten column names
            df_hourly.columns = ['timestamp', 'vel_media', 'vel_max', 'vel_std', 
                                'bateria_media', 'tensao_media', 'km_periodo', 
                                'horimetro_periodo', 'ignicao_ratio']
            
            # Adicionar features temporais
            df_hourly['hora'] = df_hourly['timestamp'].dt.hour
            df_hourly['dia_semana'] = df_hourly['timestamp'].dt.dayofweek
            
            # Preencher NaNs
            numeric_cols = ['vel_media', 'vel_max', 'vel_std', 'bateria_media', 
                           'tensao_media', 'km_periodo', 'horimetro_periodo', 'ignicao_ratio']
            for col in numeric_cols:
                if col in df_hourly.columns:
                    df_hourly[col] = pd.to_numeric(df_hourly[col], errors='coerce').fillna(0)
            
            return df_hourly[numeric_cols + ['hora', 'dia_semana']].dropna()
            
        except Exception as e:
            print(f"Erro ao preparar features: {e}")
            return pd.DataFrame()
    
    def _detect_anomalies(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Detectar anomalias usando Isolation Forest"""
        try:
            if len(features) < 10:
                return {'count': 0, 'indices': [], 'scores': []}
            
            # Normalizar dados
            features_scaled = self.scaler.fit_transform(features)
            
            # Detectar anomalias
            outliers = self.anomaly_detector.fit_predict(features_scaled)
            anomaly_scores = self.anomaly_detector.score_samples(features_scaled)
            
            anomaly_indices = np.where(outliers == -1)[0]
            
            return {
                'count': len(anomaly_indices),
                'indices': anomaly_indices.tolist(),
                'scores': anomaly_scores.tolist(),
                'severity': self._classify_anomaly_severity(anomaly_scores[anomaly_indices])
            }
            
        except Exception as e:
            print(f"Erro na detecção de anomalias: {e}")
            return {'count': 0, 'indices': [], 'scores': []}
    
    def _analyze_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análise de padrões de uso"""
        try:
            patterns = {}
            
            # Padrões de velocidade
            vel_stats = df['velocidade_km'].describe()
            patterns['velocidade'] = {
                'media': round(vel_stats['mean'], 1),
                'maxima': round(vel_stats['max'], 1),
                'excessos': len(df[df['velocidade_km'] > 80]),  # Velocidade excessiva
                'paradas': len(df[df['velocidade_km'] == 0])
            }
            
            # Padrões temporais
            df['hora'] = df['data'].dt.hour
            uso_por_hora = df.groupby('hora').size()
            patterns['uso_temporal'] = {
                'horario_pico': uso_por_hora.idxmax(),
                'horario_baixo': uso_por_hora.idxmin(),
                'uso_noturno': len(df[(df['hora'] >= 22) | (df['hora'] <= 6)])
            }
            
            # Padrões de manutenção
            bateria_baixa = df[pd.to_numeric(df['bateria'], errors='coerce') < 12].shape[0] if 'bateria' in df.columns else 0
            patterns['manutencao'] = {
                'bateria_baixa_count': bateria_baixa,
                'tensao_problemas': len(df[pd.to_numeric(df['tensao'], errors='coerce') < 11]) if 'tensao' in df.columns else 0
            }
            
            return patterns
            
        except Exception as e:
            print(f"Erro na análise de padrões: {e}")
            return {}
    
    def _predict_maintenance_needs(self, df: pd.DataFrame, anomalies: Dict) -> List[Dict]:
        """Prever necessidades de manutenção"""
        alerts = []
        
        try:
            # Análise de bateria
            if 'bateria' in df.columns:
                bateria_values = pd.to_numeric(df['bateria'], errors='coerce').dropna()
                if not bateria_values.empty:
                    bateria_media = bateria_values.mean()
                    if bateria_media < 12:
                        alerts.append({
                            'tipo': 'Bateria',
                            'severidade': 'Alta' if bateria_media < 11 else 'Média',
                            'descricao': f'Bateria baixa (média: {bateria_media:.1f}V)',
                            'prazo': '3-7 dias' if bateria_media < 11 else '1-2 semanas'
                        })
            
            # Análise de velocidade excessiva
            vel_excessiva = len(df[df['velocidade_km'] > 80])
            if vel_excessiva > len(df) * 0.1:  # Mais de 10% do tempo em velocidade alta
                alerts.append({
                    'tipo': 'Desgaste',
                    'severidade': 'Média',
                    'descricao': f'Uso intensivo detectado ({vel_excessiva} ocorrências)',
                    'prazo': '2-4 semanas'
                })
            
            # Anomalias frequentes
            if anomalies.get('count', 0) > len(df) * 0.05:  # Mais de 5% anomalias
                alerts.append({
                    'tipo': 'Comportamento Anômalo',
                    'severidade': 'Média',
                    'descricao': f'{anomalies["count"]} anomalias detectadas',
                    'prazo': '1-3 semanas'
                })
                
        except Exception as e:
            print(f"Erro na previsão de manutenção: {e}")
        
        return alerts
    
    def _calculate_health_scores(self, df: pd.DataFrame, anomalies: Dict) -> Dict[str, float]:
        """Calcular scores de saúde do veículo"""
        scores = {}
        
        try:
            # Score da bateria (0-100)
            if 'bateria' in df.columns:
                bateria_values = pd.to_numeric(df['bateria'], errors='coerce').dropna()
                if not bateria_values.empty:
                    bateria_media = bateria_values.mean()
                    scores['bateria'] = max(0, min(100, (bateria_media - 10) * 10))  # 10V = 0%, 20V = 100%
                else:
                    scores['bateria'] = 50
            else:
                scores['bateria'] = 50
            
            # Score do comportamento (baseado em anomalias)
            total_registros = len(df)
            anomalia_ratio = anomalies.get('count', 0) / total_registros if total_registros > 0 else 0
            scores['comportamento'] = max(0, 100 - (anomalia_ratio * 500))  # Penaliza anomalias
            
            # Score de velocidade (uso responsável)
            vel_excessiva_ratio = len(df[df['velocidade_km'] > 80]) / total_registros if total_registros > 0 else 0
            scores['velocidade'] = max(0, 100 - (vel_excessiva_ratio * 200))
            
            # Score geral (média ponderada)
            scores['geral'] = (
                scores['bateria'] * 0.4 + 
                scores['comportamento'] * 0.35 + 
                scores['velocidade'] * 0.25
            )
            
        except Exception as e:
            print(f"Erro no cálculo de scores: {e}")
            scores = {'bateria': 50, 'comportamento': 50, 'velocidade': 50, 'geral': 50}
        
        return {k: round(v, 1) for k, v in scores.items()}
    
    def _classify_anomaly_severity(self, anomaly_scores: np.ndarray) -> str:
        """Classificar severidade das anomalias"""
        if len(anomaly_scores) == 0:
            return 'Baixa'
        
        mean_score = np.mean(anomaly_scores)
        if mean_score < -0.3:
            return 'Alta'
        elif mean_score < -0.1:
            return 'Média'
        else:
            return 'Baixa'
    
    def _generate_recommendations(self, health_scores: Dict, alerts: List[Dict]) -> List[str]:
        """Gerar recomendações baseadas na análise"""
        recommendations = []
        
        try:
            # Recomendações baseadas nos scores
            if health_scores.get('bateria', 50) < 70:
                recommendations.append("🔋 Verificar sistema elétrico e bateria")
            
            if health_scores.get('comportamento', 50) < 70:
                recommendations.append("⚠️ Revisar padrões de condução e treinamento")
            
            if health_scores.get('velocidade', 50) < 70:
                recommendations.append("🚗 Implementar controle de velocidade")
            
            # Recomendações baseadas nos alertas
            if any(alert['severidade'] == 'Alta' for alert in alerts):
                recommendations.append("🚨 Manutenção urgente necessária")
            
            if len(alerts) > 2:
                recommendations.append("📋 Revisar plano de manutenção preventiva")
            
            if not recommendations:
                recommendations.append("✅ Veículo em bom estado - manter rotina")
                
        except Exception as e:
            print(f"Erro ao gerar recomendações: {e}")
            recommendations = ["📋 Manter rotina de manutenção"]
        
        return recommendations
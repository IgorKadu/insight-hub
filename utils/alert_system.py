"""Sistema de Alertas em Tempo Real"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
from database.db_manager import DatabaseManager

class AlertSystem:
    def __init__(self):
        self.alert_configs = {
            'velocidade_maxima': 80,
            'velocidade_critica': 100,
            'bateria_baixa': 12,
            'bateria_critica': 11,
            'tempo_parado_max': 180,  # minutos
            'uso_noturno_inicio': 22,
            'uso_noturno_fim': 6
        }
    
    def check_realtime_alerts(self) -> List[Dict[str, Any]]:
        """Verifica alertas em tempo real"""
        alerts = []
        df = DatabaseManager.get_dashboard_data()
        
        if df.empty:
            return alerts
        
        # Validar e converter coluna de data
        if 'data' not in df.columns:
            return alerts
            
        # Converter para datetime de forma segura
        df = df.copy()
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        
        # Remover registros com data inválida
        df = df.dropna(subset=['data'])
        
        if df.empty:
            return alerts
        
        # Filtrar últimas 24h - timezone correto
        from datetime import timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Verificar se dados têm timezone
        if df['data'].dt.tz is not None:
            # Se dados não estão em UTC, converter
            if df['data'].dt.tz != timezone.utc:
                cutoff = cutoff.astimezone(df['data'].dt.tz)
        else:
            # Se dados são naive, usar cutoff naive
            cutoff = cutoff.replace(tzinfo=None)
        
        df_recent = df[df['data'] >= cutoff]
        
        # Alertas de velocidade
        speed_alerts = self._check_speed_alerts(df_recent)
        alerts.extend(speed_alerts)
        
        # Alertas de bateria
        battery_alerts = self._check_battery_alerts(df_recent)
        alerts.extend(battery_alerts)
        
        # Alertas de uso noturno
        night_alerts = self._check_night_usage(df_recent)
        alerts.extend(night_alerts)
        
        return alerts
    
    def _check_speed_alerts(self, df: pd.DataFrame) -> List[Dict]:
        alerts = []
        if 'velocidade_km' not in df.columns:
            return alerts
            
        # Filtrar apenas registros com velocidade > 0 para alertas
        df_moving = df[df['velocidade_km'] > 0]
        
        for _, row in df_moving.iterrows():
            vel = float(row['velocidade_km'])
            if vel > self.alert_configs['velocidade_critica']:
                alerts.append({
                    'tipo': 'Velocidade Crítica',
                    'severidade': 'Alta',
                    'veiculo': row['placa'],
                    'valor': f"{vel:.1f} km/h",
                    'timestamp': row['data'],
                    'localizacao': row.get('endereco', 'Localização não disponível')
                })
            elif vel > self.alert_configs['velocidade_maxima']:
                alerts.append({
                    'tipo': 'Excesso de Velocidade',
                    'severidade': 'Média',
                    'veiculo': row['placa'],
                    'valor': f"{vel:.1f} km/h",
                    'timestamp': row['data'],
                    'localizacao': row.get('endereco', 'Localização não disponível')
                })
        return alerts
    
    def _check_battery_alerts(self, df: pd.DataFrame) -> List[Dict]:
        alerts = []
        if 'battery_level' in df.columns:
            # Converter battery_level para numérico (vem como string)
            df_copy = df.copy()
            df_copy['bateria_num'] = pd.to_numeric(df_copy['battery_level'], errors='coerce')
            
            # Filtrar apenas valores válidos
            df_copy = df_copy.dropna(subset=['bateria_num'])
            
            if not df_copy.empty:
                # Alertas de bateria baixa (abaixo de 12V)
                low_battery = df_copy[df_copy['bateria_num'] < self.alert_configs['bateria_baixa']]
                
                for _, row in low_battery.iterrows():
                    bat = row['bateria_num']
                    severity = 'Alta' if bat < self.alert_configs['bateria_critica'] else 'Média'
                    alerts.append({
                        'tipo': 'Bateria Baixa',
                        'severidade': severity,
                        'veiculo': row['placa'],
                        'valor': f"{bat:.1f}V",
                        'timestamp': row['data'],
                        'localizacao': row.get('endereco', 'Localização não disponível')
                    })
        return alerts
    
    def _check_night_usage(self, df: pd.DataFrame) -> List[Dict]:
        alerts = []
        if 'data' not in df.columns:
            return alerts
            
        # Trabalhar com cópia para não modificar original
        df_copy = df.copy()
        
        # Converter para datetime se necessário
        if not pd.api.types.is_datetime64_any_dtype(df_copy['data']):
            df_copy['data'] = pd.to_datetime(df_copy['data'], errors='coerce')
            
        # Remover registros com data inválida
        df_copy = df_copy.dropna(subset=['data'])
        
        if df_copy.empty:
            return alerts
            
        df_copy['hora'] = df_copy['data'].dt.hour
        night_usage = df_copy[
            (df_copy['hora'] >= self.alert_configs['uso_noturno_inicio']) | 
            (df_copy['hora'] <= self.alert_configs['uso_noturno_fim'])
        ]
        
        if len(night_usage) > 10:  # Mais de 10 registros noturnos
            for veiculo in night_usage['placa'].unique():
                count = len(night_usage[night_usage['placa'] == veiculo])
                if count > 5:
                    alerts.append({
                        'tipo': 'Uso Noturno Frequente',
                        'severidade': 'Baixa',
                        'veiculo': veiculo,
                        'valor': f"{count} ocorrências",
                        'timestamp': night_usage['data'].max(),
                        'localizacao': 'Múltiplas'
                    })
        return alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Resumo dos alertas"""
        alerts = self.check_realtime_alerts()
        summary = {
            'total_alerts': len(alerts),
            'high_severity': len([a for a in alerts if a['severidade'] == 'Alta']),
            'medium_severity': len([a for a in alerts if a['severidade'] == 'Média']),
            'low_severity': len([a for a in alerts if a['severidade'] == 'Baixa']),
            'by_type': {}
        }
        
        for alert in alerts:
            tipo = alert['tipo']
            if tipo not in summary['by_type']:
                summary['by_type'][tipo] = 0
            summary['by_type'][tipo] += 1
            
        return summary
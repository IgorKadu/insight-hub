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
        
        # Filtrar últimas 24h - timezone correto
        from datetime import timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Verificar se dados têm timezone
        if df['data'].dt.tz is not None:
            # Se dados não estão em UTC, converter
            if df['data'].dt.tz != timezone.utc:
                cutoff = cutoff.astimezone(df['data'].dt.tz)
        
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
        for _, row in df.iterrows():
            vel = row['velocidade_km']
            if vel > self.alert_configs['velocidade_critica']:
                alerts.append({
                    'tipo': 'Velocidade Crítica',
                    'severidade': 'Alta',
                    'veiculo': row['placa'],
                    'valor': f"{vel} km/h",
                    'timestamp': row['data'],
                    'localizacao': row.get('endereco', 'N/A')
                })
            elif vel > self.alert_configs['velocidade_maxima']:
                alerts.append({
                    'tipo': 'Excesso de Velocidade',
                    'severidade': 'Média',
                    'veiculo': row['placa'],
                    'valor': f"{vel} km/h",
                    'timestamp': row['data'],
                    'localizacao': row.get('endereco', 'N/A')
                })
        return alerts
    
    def _check_battery_alerts(self, df: pd.DataFrame) -> List[Dict]:
        alerts = []
        if 'bateria' in df.columns:
            df['bateria_num'] = pd.to_numeric(df['bateria'], errors='coerce')
            low_battery = df[df['bateria_num'] < self.alert_configs['bateria_baixa']]
            
            for _, row in low_battery.iterrows():
                bat = row['bateria_num']
                severity = 'Alta' if bat < self.alert_configs['bateria_critica'] else 'Média'
                alerts.append({
                    'tipo': 'Bateria Baixa',
                    'severidade': severity,
                    'veiculo': row['placa'],
                    'valor': f"{bat:.1f}V",
                    'timestamp': row['data'],
                    'localizacao': row.get('endereco', 'N/A')
                })
        return alerts
    
    def _check_night_usage(self, df: pd.DataFrame) -> List[Dict]:
        alerts = []
        df['hora'] = df['data'].dt.hour
        night_usage = df[
            (df['hora'] >= self.alert_configs['uso_noturno_inicio']) | 
            (df['hora'] <= self.alert_configs['uso_noturno_fim'])
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
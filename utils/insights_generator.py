import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

class InsightsGenerator:
    """Gerador de insights automáticos para dados de frota"""
    
    def __init__(self, analyzer):
        """Inicializa com um analisador de dados"""
        self.analyzer = analyzer
        self.insights = []
    
    def generate_all_insights(self):
        """Gera todos os tipos de insights"""
        self.insights = []
        
        # Gerar diferentes tipos de insights
        self.generate_performance_insights()
        self.generate_compliance_insights()
        self.generate_efficiency_insights()
        self.generate_operational_insights()
        self.generate_predictive_insights()
        
        return self.insights
    
    def generate_performance_insights(self):
        """Gera insights de performance"""
        kpis = self.analyzer.get_kpis()
        speed_analysis = self.analyzer.get_speed_analysis()
        
        if not kpis:
            return
        
        # Insight sobre velocidade média
        if kpis['velocidade_media'] > 60:
            self.add_insight(
                "⚠️ Velocidade Elevada",
                f"A velocidade média da frota é de {kpis['velocidade_media']:.1f} km/h, acima do recomendado.",
                "Considere implementar políticas de condução mais rigorosas.",
                "warning"
            )
        elif kpis['velocidade_media'] < 25:
            self.add_insight(
                "🐌 Velocidade Baixa",
                f"A velocidade média da frota é de {kpis['velocidade_media']:.1f} km/h, possivelmente indicando trânsito urbano intenso.",
                "Avalie otimização de rotas em horários de menor movimento.",
                "info"
            )
        
        # Insight sobre cobertura GPS
        if kpis['cobertura_gps'] < 90:
            self.add_insight(
                "📡 Problemas de GPS",
                f"Cobertura GPS de apenas {kpis['cobertura_gps']:.1f}%, abaixo do ideal (>95%).",
                "Verifique equipamentos GPS e áreas de cobertura de sinal.",
                "error"
            )
        else:
            self.add_insight(
                "✅ Excelente Cobertura GPS",
                f"Cobertura GPS de {kpis['cobertura_gps']:.1f}%, dentro do padrão de qualidade.",
                "Sistema de rastreamento funcionando adequadamente.",
                "success"
            )
    
    def generate_compliance_insights(self):
        """Gera insights de compliance"""
        compliance = self.analyzer.get_compliance_analysis()
        
        if not compliance:
            return
        
        # Insights sobre violações de velocidade
        if compliance['violacoes_velocidade'] > 0:
            self.add_insight(
                "🚨 Violações de Velocidade",
                f"{compliance['violacoes_velocidade']} registros de excesso de velocidade detectados.",
                "Implemente treinamento de condutores e monitoramento rigoroso.",
                "error"
            )
        
        # Insights sobre veículos bloqueados
        if compliance['veiculos_bloqueados'] > 0:
            self.add_insight(
                "🔒 Veículos Bloqueados",
                f"{compliance['veiculos_bloqueados']} veículos com status de bloqueio ativo.",
                "Verifique motivos do bloqueio e normalize situação se necessário.",
                "warning"
            )
        
        # Score de compliance geral
        if compliance['score_compliance']:
            avg_score = np.mean(list(compliance['score_compliance'].values()))
            if avg_score >= 90:
                self.add_insight(
                    "🏆 Excelente Compliance",
                    f"Score médio de compliance de {avg_score:.1f}%, indicando ótima conformidade.",
                    "Mantenha os padrões de operação atuais.",
                    "success"
                )
            elif avg_score < 70:
                self.add_insight(
                    "⚠️ Compliance Baixo",
                    f"Score médio de compliance de {avg_score:.1f}%, requer atenção.",
                    "Implemente ações corretivas urgentes para melhorar conformidade.",
                    "error"
                )
    
    def generate_efficiency_insights(self):
        """Gera insights de eficiência"""
        kpis = self.analyzer.get_kpis()
        efficiency = self.analyzer.get_efficiency_metrics()
        
        if not kpis or not efficiency:
            return
        
        # Insight sobre utilização da frota
        if kpis['periodo_dias'] > 0:
            utilizacao_media = kpis['total_registros'] / (kpis['total_veiculos'] * kpis['periodo_dias'])
            
            if utilizacao_media < 10:
                self.add_insight(
                    "📉 Baixa Utilização",
                    f"Utilização média de {utilizacao_media:.1f} registros por veículo/dia.",
                    "Considere otimizar a distribuição e uso dos veículos.",
                    "warning"
                )
            elif utilizacao_media > 50:
                self.add_insight(
                    "📈 Alta Utilização",
                    f"Utilização média de {utilizacao_media:.1f} registros por veículo/dia.",
                    "Frota sendo bem utilizada, monitore sobrecarga.",
                    "success"
                )
        
        # Insight sobre distância percorrida
        if kpis['distancia_total'] > 0 and kpis['tempo_ativo_horas'] > 0:
            km_por_hora = kpis['distancia_total'] / kpis['tempo_ativo_horas']
            if km_por_hora < 15:
                self.add_insight(
                    "🐢 Baixa Produtividade",
                    f"Média de {km_por_hora:.1f} km/hora de operação, indicando possível ineficiência.",
                    "Analise rotas e otimize deslocamentos.",
                    "warning"
                )
    
    def generate_operational_insights(self):
        """Gera insights operacionais"""
        operational = self.analyzer.get_operational_analysis()
        patterns = self.analyzer.get_temporal_patterns()
        
        if not operational or not patterns:
            return
        
        # Insight sobre padrões de uso por hora
        if 'padroes_por_hora' in patterns and patterns['padroes_por_hora'] is not None:
            hourly_data = patterns['padroes_por_hora']
            
            # Se hourly_data é um DataFrame com dados válidos
            if isinstance(hourly_data, pd.DataFrame) and not hourly_data.empty:
                # Verificar se tem índice ou coluna de hora
                if hourly_data.index.name == 'hora' or 'hora' in hourly_data.columns:
                    # Usar a primeira coluna numérica disponível como proxy para atividade
                    numeric_cols = hourly_data.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        activity_col = numeric_cols[0]
                        peak_hour = hourly_data[activity_col].idxmax()
                        peak_value = hourly_data.loc[peak_hour, activity_col]
                        
                        self.add_insight(
                            "⏰ Pico de Utilização",
                            f"Maior atividade registrada às {peak_hour}h.",
                            "Considere balanceamento de carga em outros horários.",
                            "info"
                        )
                        return
        
        # Insight sobre veículos inativos
        if 'estatisticas_por_veiculo' in operational:
            vehicle_stats = operational['estatisticas_por_veiculo']
            if len(vehicle_stats) > 0:
                inactive_threshold = vehicle_stats['velocidade_km_count'].quantile(0.25)
                inactive_vehicles = len(vehicle_stats[vehicle_stats['velocidade_km_count'] < inactive_threshold])
                
                if inactive_vehicles > 0:
                    self.add_insight(
                        "😴 Veículos Pouco Ativos",
                        f"{inactive_vehicles} veículos com baixa atividade registrada.",
                        "Verifique se estes veículos estão sendo subutilizados.",
                        "info"
                    )
    
    def generate_predictive_insights(self):
        """Gera insights preditivos"""
        df = self.analyzer.filtered_df
        
        if df.empty:
            return
        
        # Análise de tendências - usar período dinâmico baseado nos dados filtrados
        if len(df) > 7:  # Pelo menos uma semana de dados
            # Calcular período de análise baseado no range total dos dados filtrados
            date_range = (df['data'].max() - df['data'].min()).days
            
            # Usar 25% do período total para análise recente, mínimo 1 dia, máximo 30 dias
            analysis_days = max(1, min(30, round(date_range * 0.25)))
            
            recent_data = df[df['data'] >= df['data'].max() - timedelta(days=analysis_days)]
            older_data = df[df['data'] < df['data'].max() - timedelta(days=analysis_days)]
            
            if not recent_data.empty and not older_data.empty:
                recent_avg_speed = recent_data['velocidade_km'].mean()
                older_avg_speed = older_data['velocidade_km'].mean()
                
                speed_change = ((recent_avg_speed - older_avg_speed) / older_avg_speed) * 100
                
                if abs(speed_change) > 10:
                    trend = "aumento" if speed_change > 0 else "redução"
                    period_text = f"últimos {analysis_days} dia{'s' if analysis_days > 1 else ''}"
                    self.add_insight(
                        f"📈 Tendência de Velocidade",
                        f"Detectado {trend} de {abs(speed_change):.1f}% na velocidade média nos {period_text}.",
                        f"Monitore esta tendência para identificar padrões sazonais ou operacionais.",
                        "info"
                    )
        
        # Predição de manutenção baseada em uso
        agg_map = {'odometro_periodo_km': 'sum'}
        if 'engine_hours_period' in df.columns:
            agg_map['engine_hours_period'] = 'sum'
        
        vehicle_usage = df.groupby('placa').agg(agg_map)
        
        for placa, data in vehicle_usage.iterrows():
            total_km = data['odometro_periodo_km']
            if total_km > 1000:  # Veículos com alta quilometragem
                self.add_insight(
                    "🔧 Manutenção Preventiva",
                    f"Veículo {placa} percorreu {total_km:.0f}km no período analisado.",
                    "Agende revisão preventiva para manter performance e segurança.",
                    "info"
                )
    
    def add_insight(self, title, description, recommendation, type="info"):
        """Adiciona um insight à lista"""
        insight = {
            'title': title,
            'description': description,
            'recommendation': recommendation,
            'type': type,
            'timestamp': datetime.now(),
            'priority': self.get_priority_by_type(type)
        }
        self.insights.append(insight)
    
    def get_priority_by_type(self, type):
        """Retorna prioridade baseada no tipo"""
        priority_map = {
            'error': 1,
            'warning': 2,
            'info': 3,
            'success': 4
        }
        return priority_map.get(type, 3)
    
    def get_insights_by_priority(self):
        """Retorna insights ordenados por prioridade"""
        return sorted(self.insights, key=lambda x: x['priority'])
    
    def get_insights_by_type(self, type):
        """Retorna insights de um tipo específico"""
        return [insight for insight in self.insights if insight['type'] == type]
    
    def export_insights_to_text(self):
        """Exporta insights para texto"""
        output = f"# Relatório de Insights - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        
        for insight in self.get_insights_by_priority():
            output += f"## {insight['title']}\n"
            output += f"**Descrição:** {insight['description']}\n"
            output += f"**Recomendação:** {insight['recommendation']}\n"
            output += f"**Tipo:** {insight['type'].upper()}\n\n"
        
        return output

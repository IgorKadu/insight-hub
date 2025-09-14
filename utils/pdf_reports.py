"""Gerador de Relatórios PDF Avançado"""
from fpdf import FPDF
import pandas as pd
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.data_analyzer import DataAnalyzer
from utils.insights_generator import InsightsGenerator
from utils.ml_predictive import PredictiveMaintenanceAnalyzer
import os
import numpy as np

class PDFReportGenerator:
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.pdf.add_page()
        self.pdf.set_font('Arial', 'B', 16)
    
    def add_header(self, title):
        """Adiciona cabeçalho da seção"""
        self.pdf.set_fill_color(230, 230, 230)
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 10, title, 0, 1, 'L', True)
        self.pdf.ln(5)
    
    def add_subsection(self, title):
        """Adiciona subtítulo"""
        self.pdf.set_font('Arial', 'B', 12)
        self.pdf.cell(0, 8, title, 0, 1, 'L')
        self.pdf.ln(3)
    
    def add_metric(self, label, value, unit=""):
        """Adiciona métrica formatada"""
        self.pdf.set_font('Arial', '', 10)
        self.pdf.cell(100, 6, f'{label}:', 0, 0, 'L')
        self.pdf.set_font('Arial', 'B', 10)
        self.pdf.cell(0, 6, f'{value} {unit}', 0, 1, 'L')
    
    def add_table_header(self, headers):
        """Adiciona cabeçalho de tabela"""
        self.pdf.set_font('Arial', 'B', 9)
        self.pdf.set_fill_color(200, 200, 200)
        col_width = 190 / len(headers)
        for header in headers:
            self.pdf.cell(col_width, 8, str(header), 1, 0, 'C', True)
        self.pdf.ln()
    
    def add_table_row(self, data):
        """Adiciona linha de tabela"""
        self.pdf.set_font('Arial', '', 8)
        col_width = 190 / len(data)
        for item in data:
            self.pdf.cell(col_width, 6, str(item), 1, 0, 'C')
        self.pdf.ln()
    
    def generate_comprehensive_report(self, output_path: str = "relatorio_completo_frota.pdf") -> str:
        """Gera relatório completo integrando dados de todos os painéis"""
        try:
            # Carregar dados brutos
            df = DatabaseManager.get_dashboard_data()
            summary = DatabaseManager.get_fleet_summary()
            
            if df.empty:
                self.pdf.cell(0, 10, 'ERRO: Nenhum dado disponível para gerar relatório', 0, 1, 'C')
                self.pdf.output(output_path)
                return output_path
            
            # Inicializar analisadores para dados processados
            analyzer = DataAnalyzer(df)
            insights_generator = InsightsGenerator(analyzer)
            predictive_analyzer = PredictiveMaintenanceAnalyzer()
            
            # Cabeçalho principal aprimorado
            self.pdf.set_font('Arial', 'B', 20)
            self.pdf.cell(0, 15, 'RELATÓRIO EXECUTIVO INTEGRADO DE FROTA', 0, 1, 'C')
            self.pdf.set_font('Arial', 'I', 14)
            self.pdf.cell(0, 8, 'Insight Hub - Análise Inteligente e Preditiva', 0, 1, 'C')
            self.pdf.set_font('Arial', '', 10)
            self.pdf.cell(0, 6, 'Relatório consolidado com dados de todos os painéis do sistema', 0, 1, 'C')
            self.pdf.ln(10)
            
            # Informações do relatório
            self.pdf.set_font('Arial', '', 10)
            self.pdf.cell(0, 6, f'Data de Geração: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1)
            self.pdf.cell(0, 6, f'Período Analisado: {df["data"].min().strftime("%d/%m/%Y")} a {df["data"].max().strftime("%d/%m/%Y")}', 0, 1)
            self.pdf.cell(0, 6, f'Fonte: Dados integrados de 5 painéis analíticos', 0, 1)
            self.pdf.ln(8)
            
            # Gerar insights automáticos
            insights = insights_generator.generate_all_insights()
            kpis = analyzer.get_kpis()
            
            # Análise preditiva (se houver dados suficientes)
            predictive_results = None
            if len(df) > 50:  # Mínimo de dados para ML
                try:
                    predictive_results = predictive_analyzer.analyze_vehicle_health(df)
                except Exception as e:
                    print(f"Erro na análise preditiva: {e}")
                    predictive_results = None
            
            # 1. RESUMO EXECUTIVO COM INSIGHTS INTELIGENTES
            self.add_header('1. RESUMO EXECUTIVO & INSIGHTS AUTOMÁTICOS')
            
            # Insights críticos no topo
            critical_insights = [i for i in insights if i['type'] == 'error']
            if critical_insights:
                self.add_subsection('🚨 ALERTAS CRÍTICOS IDENTIFICADOS:')
                for insight in critical_insights[:3]:  # Top 3 críticos
                    self.pdf.set_font('Arial', '', 9)
                    self.pdf.cell(0, 5, f"• {insight['title']}: {insight['description']}", 0, 1)
                self.pdf.ln(3)
            
            # Usar KPIs do analyzer ao invés de cálculos básicos
            total_records = kpis['total_registros'] if kpis else len(df)
            total_vehicles = kpis['total_veiculos'] if kpis else df['placa'].nunique()
            total_clients = kpis['total_clientes'] if kpis else df['cliente'].nunique() 
            avg_speed = kpis['velocidade_media'] if kpis else df['velocidade_km'].mean()
            max_speed = kpis['velocidade_maxima'] if kpis else df['velocidade_km'].max()
            total_distance = kpis['km_total'] if kpis else df['odometro_periodo_km'].sum()
            gps_coverage = kpis['cobertura_gps'] if kpis else 0
            
            # Métricas principais aprimoradas
            self.add_subsection('📊 MÉTRICAS PRINCIPAIS DA FROTA:')
            self.add_metric('Total de Registros Processados', f'{total_records:,}')
            self.add_metric('Veículos Monitorados', f'{total_vehicles}')
            self.add_metric('Clientes Atendidos', f'{total_clients}')
            self.add_metric('Velocidade Média da Frota', f'{avg_speed:.1f}', 'km/h')
            self.add_metric('Velocidade Máxima Registrada', f'{max_speed:.1f}', 'km/h')
            self.add_metric('Distância Total Percorrida', f'{total_distance:.1f}', 'km')
            self.add_metric('Cobertura GPS Ativa', f'{gps_coverage:.1f}', '%')
            
            # Score de saúde geral se disponível
            if predictive_results and predictive_results.get('status') == 'success':
                health_scores = predictive_results.get('health_scores', {})
                overall_health = health_scores.get('geral', 0)
                self.add_metric('Score de Saúde Geral da Frota', f'{overall_health}', '%')
                
                # Alertas de manutenção
                maintenance_alerts = predictive_results.get('maintenance_alerts', [])
                if maintenance_alerts:
                    self.add_metric('Alertas de Manutenção Preditiva', f'{len(maintenance_alerts)}')
            
            self.pdf.ln(5)
            
            # Recomendações prioritárias dos insights
            recommendations_insights = [i for i in insights if i['type'] in ['warning', 'info']]
            if recommendations_insights:
                self.add_subsection('💡 RECOMENDAÇÕES PRIORITÁRIAS:')
                for insight in recommendations_insights[:4]:  # Top 4 recomendações
                    self.pdf.set_font('Arial', '', 9)
                    self.pdf.cell(0, 5, f"• {insight.get('recommendation', 'Ver detalhes')}", 0, 1)
                self.pdf.ln(3)
            
            # 2. ANÁLISE PREDITIVA DE MANUTENÇÃO
            self.add_header('2. ANÁLISE PREDITIVA DE MANUTENÇÃO')
            
            if predictive_results and predictive_results.get('status') == 'success':
                health_scores = predictive_results.get('health_scores', {})
                maintenance_alerts = predictive_results.get('maintenance_alerts', [])
                
                self.add_subsection('Scores de Saúde dos Sistemas:')
                self.add_metric('Saúde da Bateria', f'{health_scores.get("bateria", 0)}%')
                self.add_metric('Comportamento de Condução', f'{health_scores.get("comportamento", 0)}%')
                self.add_metric('Perfil de Velocidade', f'{health_scores.get("velocidade", 0)}%')
                
                if maintenance_alerts:
                    self.add_subsection('Alertas de Manutenção Preditiva:')
                    for alert in maintenance_alerts[:5]:  # Top 5 alertas
                        self.pdf.set_font('Arial', '', 9)
                        alert_text = f"• {alert.get('vehicle', 'N/A')}: {alert.get('message', 'Alerta detectado')}"
                        self.pdf.cell(0, 5, alert_text[:90], 0, 1)  # Truncar se muito longo
                        
                # Recomendações de manutenção
                recommendations = predictive_results.get('recommendations', [])
                if recommendations:
                    self.add_subsection('Recomendações de Ação:')
                    for rec in recommendations[:3]:  # Top 3 recomendações
                        self.pdf.set_font('Arial', '', 9)
                        self.pdf.cell(0, 5, f"• {rec}"[:80], 0, 1)
            else:
                self.pdf.set_font('Arial', '', 10)
                self.pdf.cell(0, 6, 'Dados insuficientes para análise preditiva (mínimo 50 registros)', 0, 1)
            
            self.pdf.ln(5)
            
            # 3. ANÁLISE POR CLIENTE
            self.add_header('3. ANÁLISE POR CLIENTE')
            
            client_stats = df.groupby('cliente').agg({
                'placa': 'nunique',
                'velocidade_km': ['mean', 'max'],
                'odometro_periodo_km': 'sum'
            }).round(2)
            
            self.add_table_header(['Cliente', 'Veículos', 'Vel. Média', 'Vel. Máx', 'Dist. Total'])
            for cliente in client_stats.index:
                data = [
                    cliente,
                    client_stats.loc[cliente, ('placa', 'nunique')],
                    f"{client_stats.loc[cliente, ('velocidade_km', 'mean')]:.1f}",
                    f"{client_stats.loc[cliente, ('velocidade_km', 'max')]:.1f}",
                    f"{client_stats.loc[cliente, ('odometro_periodo_km', 'sum')]:.1f}"
                ]
                self.add_table_row(data)
            self.pdf.ln(5)
            
            # 4. ANÁLISE GEOGRÁFICA E PADRÕES DE ROTA
            self.add_header('4. ANÁLISE GEOGRÁFICA E PADRÕES DE ROTA')
            
            # Análise geográfica baseada em coordenadas
            if 'latitude' in df.columns and 'longitude' in df.columns:
                valid_coords = df.dropna(subset=['latitude', 'longitude'])
                valid_coords = valid_coords[(valid_coords['latitude'] != 0) & (valid_coords['longitude'] != 0)]
                
                if not valid_coords.empty:
                    # Estatísticas geográficas
                    center_lat = valid_coords['latitude'].mean()
                    center_lon = valid_coords['longitude'].mean()
                    
                    # Calcular dispersão geográfica
                    lat_range = valid_coords['latitude'].max() - valid_coords['latitude'].min()
                    lon_range = valid_coords['longitude'].max() - valid_coords['longitude'].min()
                    
                    self.add_subsection('Cobertura Geográfica:')
                    self.add_metric('Pontos com GPS Válido', f'{len(valid_coords):,}')
                    self.add_metric('Centro Geográfico', f'{center_lat:.4f}, {center_lon:.4f}')
                    self.add_metric('Dispersão Latitudinal', f'{lat_range:.4f}°')
                    self.add_metric('Dispersão Longitudinal', f'{lon_range:.4f}°')
                    
                    # Análise de velocidade por região (simplificada)
                    speed_violations = valid_coords[valid_coords['velocidade_km'] > 80]
                    if not speed_violations.empty:
                        self.add_subsection('Análise de Velocidade por Região:')
                        self.add_metric('Picos de Velocidade Geo-referenciados', f'{len(speed_violations):,}')
                        self.add_metric('Percentual de Violações', f'{len(speed_violations)/len(valid_coords)*100:.1f}%')
                else:
                    self.pdf.set_font('Arial', '', 10)
                    self.pdf.cell(0, 6, 'Coordenadas GPS não disponíveis para análise geográfica', 0, 1)
            else:
                self.pdf.set_font('Arial', '', 10)
                self.pdf.cell(0, 6, 'Dados de localização não encontrados', 0, 1)
            
            self.pdf.ln(5)
            
            # 5. ANÁLISE DETALHADA POR VEÍCULO
            self.add_header('5. ANÁLISE DETALHADA POR VEÍCULO')
            
            vehicle_stats = df.groupby(['cliente', 'placa']).agg({
                'velocidade_km': ['mean', 'max', 'std'],
                'odometro_periodo_km': 'sum',
                'data': 'count'
            }).round(2)
            
            self.add_table_header(['Cliente', 'Placa', 'Registros', 'Vel. Média', 'Vel. Máx', 'Distância'])
            for (cliente, placa) in vehicle_stats.index:
                data = [
                    cliente[:15],  # Truncar se muito longo
                    placa,
                    vehicle_stats.loc[(cliente, placa), ('data', 'count')],
                    f"{vehicle_stats.loc[(cliente, placa), ('velocidade_km', 'mean')]:.1f}",
                    f"{vehicle_stats.loc[(cliente, placa), ('velocidade_km', 'max')]:.1f}",
                    f"{vehicle_stats.loc[(cliente, placa), ('odometro_periodo_km', 'sum')]:.1f}"
                ]
                self.add_table_row(data)
            self.pdf.ln(5)
            
            # 6. ANÁLISE DE VELOCIDADE E CONFORMIDADE OPERACIONAL
            self.add_header('6. ANÁLISE DE VELOCIDADE E CONFORMIDADE OPERACIONAL')
            
            # Usar análise de compliance do DataAnalyzer
            compliance_data = analyzer.get_compliance_analysis() if kpis else None
            if compliance_data:
                self.add_subsection('Análise de Conformidade Avançada:')
                
                # Scores de compliance por veículo se disponível
                if 'compliance_scores' in compliance_data:
                    avg_compliance = np.mean(list(compliance_data['compliance_scores'].values()))
                    self.add_metric('Score Médio de Conformidade', f'{avg_compliance:.1f}%')
                    
                    # Veículos com baixa conformidade
                    low_compliance = {k: v for k, v in compliance_data['compliance_scores'].items() if v < 70}
                    if low_compliance:
                        self.add_metric('Veículos com Baixa Conformidade', f'{len(low_compliance)}')
                        
                        self.add_subsection('Veículos Críticos (< 70% conformidade):')
                        self.add_table_header(['Veículo', 'Score', 'Status'])
                        for vehicle, score in list(low_compliance.items())[:5]:  # Top 5 críticos
                            status = 'Crítico' if score < 50 else 'Atenção'
                            self.add_table_row([vehicle, f'{score:.1f}%', status])
            
            # Faixas de velocidade
            speed_ranges = {
                '0-30 km/h': len(df[df['velocidade_km'] <= 30]),
                '31-60 km/h': len(df[(df['velocidade_km'] > 30) & (df['velocidade_km'] <= 60)]),
                '61-80 km/h': len(df[(df['velocidade_km'] > 60) & (df['velocidade_km'] <= 80)]),
                '81-100 km/h': len(df[(df['velocidade_km'] > 80) & (df['velocidade_km'] <= 100)]),
                'Acima de 100 km/h': len(df[df['velocidade_km'] > 100])
            }
            
            self.add_subsection('Distribuição de Velocidades:')
            for faixa, count in speed_ranges.items():
                percentage = (count / total_records * 100) if total_records > 0 else 0
                self.add_metric(faixa, f'{count:,} ({percentage:.1f}%)')
            
            # Violações de velocidade (acima de 80 km/h)
            violations = df[df['velocidade_km'] > 80]
            self.add_subsection('Alertas de Velocidade (acima de 80 km/h):')
            self.add_metric('Total de Violações', f'{len(violations):,}')
            self.add_metric('Percentual da Frota', f'{(len(violations)/total_records*100):.1f}%')
            
            if not violations.empty:
                worst_violations = violations.nlargest(5, 'velocidade_km')
                self.add_subsection('Top 5 Maiores Velocidades:')
                self.add_table_header(['Placa', 'Cliente', 'Velocidade', 'Data/Hora'])
                for _, row in worst_violations.iterrows():
                    data = [
                        row['placa'],
                        row['cliente'][:15],
                        f"{row['velocidade_km']:.1f} km/h",
                        row['data'].strftime('%d/%m %H:%M')
                    ]
                    self.add_table_row(data)
            self.pdf.ln(5)
            
            # 5. ANÁLISE OPERACIONAL
            self.add_header('5. ANÁLISE OPERACIONAL')
            
            # Status operacional
            ignition_stats = df['ignicao'].value_counts() if 'ignicao' in df.columns else {}
            blocked_stats = df['bloqueado'].value_counts() if 'bloqueado' in df.columns else {}
            
            self.add_subsection('Status dos Veículos:')
            if 'ligado' in ignition_stats.index or 'desligado' in ignition_stats.index:
                self.add_metric('Veículos com Ignição Ligada', f'{ignition_stats.get("ligado", 0):,}')
                self.add_metric('Veículos com Ignição Desligada', f'{ignition_stats.get("desligado", 0):,}')
            
            if 'sim' in blocked_stats.index or 'não' in blocked_stats.index:
                self.add_metric('Veículos Bloqueados', f'{blocked_stats.get("sim", 0):,}')
                self.add_metric('Veículos Desbloqueados', f'{blocked_stats.get("não", 0):,}')
            
            # Análise temporal
            df['hora'] = df['data'].dt.hour
            peak_hour = df.groupby('hora').size().idxmax()
            peak_count = df.groupby('hora').size().max()
            
            self.add_subsection('Padrões de Uso:')
            self.add_metric('Horário de Pico', f'{peak_hour}:00 - {peak_hour+1}:00')
            self.add_metric('Atividade no Pico', f'{peak_count:,} registros')
            self.pdf.ln(5)
            
            # 6. ANÁLISE DE EFICIÊNCIA
            self.add_header('6. ANÁLISE DE EFICIÊNCIA ENERGÉTICA')
            
            if 'bateria' in df.columns:
                battery_avg = df['bateria'].mean()
                battery_low = len(df[df['bateria'] < 12.0])
                self.add_metric('Nível Médio de Bateria', f'{battery_avg:.1f}V')
                self.add_metric('Alertas de Bateria Baixa', f'{battery_low:,}')
            
            # Eficiência por veículo
            efficiency_stats = df.groupby('placa').agg({
                'velocidade_km': 'mean',
                'odometro_periodo_km': 'sum'
            }).round(2)
            
            # Top 5 mais eficientes (maior distância, menor velocidade média)
            efficiency_stats['score'] = efficiency_stats['odometro_periodo_km'] / (efficiency_stats['velocidade_km'] + 1)
            top_efficient = efficiency_stats.nlargest(5, 'score')
            
            self.add_subsection('Top 5 Veículos Mais Eficientes:')
            self.add_table_header(['Placa', 'Distância Total', 'Vel. Média', 'Score'])
            for placa in top_efficient.index:
                data = [
                    placa,
                    f"{top_efficient.loc[placa, 'odometro_periodo_km']:.1f} km",
                    f"{top_efficient.loc[placa, 'velocidade_km']:.1f} km/h",
                    f"{top_efficient.loc[placa, 'score']:.2f}"
                ]
                self.add_table_row(data)
            self.pdf.ln(5)
            
            # 7. INSIGHTS INTELIGENTES E OPORTUNIDADES
            self.add_header('7. INSIGHTS INTELIGENTES E OPORTUNIDADES DE MELHORIA')
            
            # Categorizar insights por tipo
            opportunities = [i for i in insights if i['type'] == 'info' and 'oportunidade' in i.get('description', '').lower()]
            warnings = [i for i in insights if i['type'] == 'warning']
            successes = [i for i in insights if i['type'] == 'success']
            
            if opportunities:
                self.add_subsection('🎯 Oportunidades de Otimização:')
                for opp in opportunities[:4]:  # Top 4 oportunidades
                    self.pdf.set_font('Arial', '', 9)
                    self.pdf.cell(0, 5, f"• {opp.get('recommendation', opp['description'])}"[:85], 0, 1)
            
            if warnings:
                self.add_subsection('⚠️ Pontos de Atenção:')
                for warn in warnings[:4]:  # Top 4 warnings
                    self.pdf.set_font('Arial', '', 9)
                    self.pdf.cell(0, 5, f"• {warn.get('recommendation', warn['description'])}"[:85], 0, 1)
            
            if successes:
                self.add_subsection('✅ Pontos Positivos:')
                for success in successes[:3]:  # Top 3 sucessos
                    self.pdf.set_font('Arial', '', 9)
                    self.pdf.cell(0, 5, f"• {success['description']}"[:85], 0, 1)
            
            self.pdf.ln(5)
            
            # 8. PLANO DE AÇÃO E RECOMENDAÇÕES
            self.add_header('8. PLANO DE AÇÃO E RECOMENDAÇÕES')
            
            self.pdf.set_font('Arial', '', 10)
            
            # Recomendações baseadas nos insights e análises
            recommendations = []
            
            # Recomendações baseadas nos insights automáticos
            for insight in insights:
                if insight.get('recommendation') and insight['type'] in ['error', 'warning']:
                    recommendations.append(f"• {insight['recommendation']}")
            
            # Recomendações baseadas na análise preditiva
            if predictive_results and predictive_results.get('recommendations'):
                for rec in predictive_results['recommendations'][:2]:
                    recommendations.append(f"• Manutenção: {rec}")
            
            # Recomendações específicas baseadas nos dados
            violations = df[df['velocidade_km'] > 80] if 'velocidade_km' in df.columns else pd.DataFrame()
            if len(violations) > total_records * 0.1:
                recommendations.append("• Implementar treinamento de condução defensiva para reduzir violações de velocidade")
            
            if gps_coverage < 95:
                recommendations.append("• Verificar sistema GPS dos veículos com baixa cobertura")
            
            # Adicionar recomendação sobre manutenção preditiva se aplicável
            if predictive_results and predictive_results.get('maintenance_alerts'):
                recommendations.append(f"• Agendar manutenção preventiva para {len(predictive_results['maintenance_alerts'])} veículos")
            
            # Se não há recomendações específicas, adicionar padrões
            if not recommendations or len([r for r in recommendations if not r.startswith('•')]) == 0:
                recommendations.extend([
                    "• Frota operando dentro dos parâmetros esperados",
                    "• Continuar monitoramento regular através do Insight Hub",
                    "• Revisar relatórios mensalmente para identificar tendências"
                ])
            
            for rec in recommendations:
                self.pdf.cell(0, 6, rec.encode('latin-1', 'replace').decode('latin-1'), 0, 1)
            
            self.pdf.ln(8)
            
            # Resumo final dos painéis analisados
            self.add_header('RESUMO DOS PAINÉIS ANALISADOS')
            self.pdf.set_font('Arial', '', 9)
            self.pdf.cell(0, 5, '✓ Análise Detalhada: KPIs, métricas operacionais e padrões temporais', 0, 1)
            self.pdf.cell(0, 5, '✓ Manutenção Preditiva: Health scores, alertas e detecção de anomalias', 0, 1)
            self.pdf.cell(0, 5, '✓ Insights Automáticos: Recomendações inteligentes e alertas críticos', 0, 1)
            self.pdf.cell(0, 5, '✓ Análise Geográfica: Padrões de rota e distribuição espacial', 0, 1)
            self.pdf.cell(0, 5, '✓ Controle Operacional: Conformidade e monitoramento regulatório', 0, 1)
            
            self.pdf.ln(8)
            
            # Rodapé aprimorado
            self.pdf.set_font('Arial', 'I', 8)
            self.pdf.cell(0, 5, f'Relatório Integrado gerado pelo Insight Hub - {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1, 'C')
            self.pdf.cell(0, 5, 'Dados consolidados de 5 painéis analíticos com IA e Machine Learning', 0, 1, 'C')
            
            # Salvar PDF
            self.pdf.output(output_path)
            return output_path
            
        except Exception as e:
            # Em caso de erro, criar relatório básico
            self.pdf.cell(0, 10, f'Erro ao gerar relatório detalhado: {str(e)}', 0, 1)
            self.pdf.output(output_path)
            return output_path
    
    def generate_fleet_report(self, output_path: str = "relatorio_frota.pdf") -> str:
        """Mantém compatibilidade - chama relatório completo"""
        return self.generate_comprehensive_report(output_path)
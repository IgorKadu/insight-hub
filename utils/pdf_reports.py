"""Gerador de Relatórios PDF Robusto e Seguro"""
from fpdf import FPDF
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import numpy as np
from io import BytesIO
from typing import Dict, Any, Optional, List

class PDFReportGenerator:
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        
        # Tentar adicionar fonte Unicode (DejaVu Sans)
        try:
            font_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'DejaVuSans.ttf')
            if os.path.exists(font_path):
                self.pdf.add_font('DejaVu', '', font_path, uni=True)
                self.unicode_font_available = True
                self.default_font = 'DejaVu'
            else:
                self.unicode_font_available = False
                self.default_font = 'Arial'
        except:
            self.unicode_font_available = False
            self.default_font = 'Arial'
        
        self.pdf.add_page()
        self.pdf.set_font(self.default_font, 'B', 16)
    
    def strip_emojis(self, text: str) -> str:
        """Remove emojis e caracteres especiais do texto"""
        if not text:
            return ""
        
        # Mapeamento de emojis comuns para texto
        emoji_map = {
            '🚛': '[CAMINHAO]',
            '📊': '[GRAFICO]',
            '🔍': '[LUPA]',
            '🔮': '[MANUTENCAO]',
            '🗺️': '[MAPA]',
            '🧠': '[INSIGHTS]',
            '🚨': '[ALERTA]',
            '📄': '[RELATORIO]',
            '⚡': '[VELOCIDADE]',
            '🏎️': '[CARRO]',
            '🚗': '[VEICULO]',
            '🏢': '[EMPRESA]',
            '📅': '[DATA]',
            '📈': '[TENDENCIA]',
            '✅': '[OK]',
            '❌': '[ERRO]',
            '⚠️': '[ATENCAO]',
            '💡': '[IDEIA]',
            '🎯': '[META]',
            '🔧': '[FERRAMENTA]',
            '📡': '[GPS]',
            '🛣️': '[ESTRADA]',
            '🔋': '[BATERIA]'
        }
        
        # Substituir emojis conhecidos
        for emoji, replacement in emoji_map.items():
            text = text.replace(emoji, replacement)
        
        # Remover emojis restantes (caracteres Unicode > 127 que não são acentos latinos)
        text = re.sub(r'[^\x00-\xFF\u00C0-\u00FF]+', '', text)
        
        return text
    
    def safe_text(self, text: str) -> str:
        """Converte texto para formato seguro para PDF"""
        if not text:
            return ""
        
        text = self.strip_emojis(str(text))
        
        # Se fonte Unicode não disponível, converter caracteres especiais
        if not self.unicode_font_available:
            text = text.encode('latin-1', 'replace').decode('latin-1')
        
        return text
    
    def add_header(self, title: str):
        """Adiciona cabeçalho da seção"""
        self.pdf.set_fill_color(230, 230, 230)
        self.pdf.set_font(self.default_font, 'B', 14)
        safe_title = self.safe_text(title)
        self.pdf.cell(0, 10, safe_title, 0, 1, 'L', True)
        self.pdf.ln(5)
    
    def add_subsection(self, title: str):
        """Adiciona subtítulo"""
        self.pdf.set_font(self.default_font, 'B', 12)
        safe_title = self.safe_text(title)
        self.pdf.cell(0, 8, safe_title, 0, 1, 'L')
        self.pdf.ln(3)
    
    def add_metric(self, label: str, value: str, unit: str = ""):
        """Adiciona métrica formatada"""
        self.pdf.set_font(self.default_font, '', 10)
        safe_label = self.safe_text(label)
        self.pdf.cell(100, 6, f'{safe_label}:', 0, 0, 'L')
        self.pdf.set_font(self.default_font, 'B', 10)
        safe_value = self.safe_text(str(value))
        safe_unit = self.safe_text(unit)
        self.pdf.cell(0, 6, f'{safe_value} {safe_unit}', 0, 1, 'L')
    
    def add_table_header(self, headers: List[str]):
        """Adiciona cabeçalho de tabela"""
        self.pdf.set_font(self.default_font, 'B', 9)
        self.pdf.set_fill_color(200, 200, 200)
        col_width = 190 / len(headers)
        for header in headers:
            safe_header = self.safe_text(str(header))
            self.pdf.cell(col_width, 8, safe_header, 1, 0, 'C', True)
        self.pdf.ln()
    
    def add_table_row(self, data: List[str]):
        """Adiciona linha de tabela"""
        self.pdf.set_font(self.default_font, '', 8)
        col_width = 190 / len(data)
        for item in data:
            safe_item = self.safe_text(str(item))
            # Truncar itens muito longos para caber na célula
            if len(safe_item) > 20:
                safe_item = safe_item[:17] + "..."
            self.pdf.cell(col_width, 6, safe_item, 1, 0, 'C')
        self.pdf.ln()
    
    def safe_date_format(self, date_value: Any, format_str: str = "%d/%m/%Y") -> str:
        """Formata data de forma segura"""
        try:
            if pd.isna(date_value):
                return "N/A"
            if isinstance(date_value, str):
                date_value = pd.to_datetime(date_value, errors='coerce')
            return date_value.strftime(format_str)
        except:
            return "N/A"
    
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
            
            # Rodapé
            self.pdf.set_font(self.default_font, 'I', 8)
            footer_text = f'Relatorio gerado em {datetime.now().strftime("%d/%m/%Y as %H:%M:%S")} - Insight Hub Fleet Monitor'
            self.pdf.cell(0, 6, self.safe_text(footer_text), 0, 1, 'C')
            
            # Gerar PDF como bytes
            buffer = BytesIO()
            self.pdf.output(buffer)
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'relatorio_frota_{timestamp}.pdf'
            
            return {
                'success': True,
                'pdf_bytes': buffer.getvalue(),
                'filename': filename,
                'total_records': total_records,
                'total_vehicles': total_vehicles,
                'total_clients': total_clients
            }
            
        except Exception as e:
            # Em caso de erro, retornar PDF de erro
            try:
                error_buffer = BytesIO()
                error_pdf = FPDF()
                error_pdf.add_page()
                error_pdf.set_font('Arial', 'B', 16)
                error_pdf.cell(0, 10, 'ERRO NA GERACAO DO RELATORIO', 0, 1, 'C')
                error_pdf.ln(10)
                error_pdf.set_font('Arial', '', 12)
                error_pdf.cell(0, 10, f'Erro: {str(e)[:100]}', 0, 1, 'C')
                error_pdf.output(error_buffer)
                
                return {
                    'success': False,
                    'error': str(e),
                    'pdf_bytes': error_buffer.getvalue(),
                    'filename': 'relatorio_erro.pdf'
                }
            except:
                return {
                    'success': False,
                    'error': str(e),
                    'pdf_bytes': b'',
                    'filename': 'relatorio_erro.pdf'
                }
    
    def generate_fleet_report(self, output_path: str = "relatorio_frota.pdf") -> str:
        """Método de compatibilidade para gerar relatório básico sem contextos"""
        try:
            from database.db_manager import DatabaseManager
            
            # Carregar dados
            df = DatabaseManager.get_dashboard_data()
            
            if df.empty:
                self.pdf.set_font(self.default_font, '', 12)
                self.pdf.cell(0, 10, 'Nenhum dado disponivel para gerar relatorio', 0, 1, 'C')
                self.pdf.output(output_path)
                return output_path
            
            # Criar contextos vazios para o método principal
            empty_contexts = {
                'kpis': {},
                'insights': [],
                'predictive': {'status': 'skipped', 'reason': 'Modo compatibilidade'},
                'routes': {},
                'operational': {},
                'compliance': {}
            }
            
            options = {'include_charts': False, 'report_type': 'Relatorio Basico'}
            result = self.generate_comprehensive_report(df, empty_contexts, options)
            
            if result['success']:
                # Salvar arquivo
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(result['pdf_bytes'])
                return output_path
            else:
                # Gerar relatório básico em caso de erro
                self.pdf.set_font(self.default_font, 'B', 16)
                self.pdf.cell(0, 10, 'RELATORIO DA FROTA', 0, 1, 'C')
                self.pdf.ln(10)
                
                self.pdf.set_font(self.default_font, '', 12)
                self.pdf.cell(0, 8, f'Data: {datetime.now().strftime("%d/%m/%Y")}', 0, 1)
                self.pdf.cell(0, 8, f'Total de registros: {len(df):,}', 0, 1)
                self.pdf.cell(0, 8, f'Veiculos: {df["placa"].nunique() if "placa" in df.columns else 0}', 0, 1)
                self.pdf.cell(0, 8, f'Clientes: {df["cliente"].nunique() if "cliente" in df.columns else 0}', 0, 1)
                
                if 'velocidade_km' in df.columns:
                    self.pdf.cell(0, 8, f'Velocidade media: {df["velocidade_km"].mean():.1f} km/h', 0, 1)
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                self.pdf.output(output_path)
                return output_path
            
        except Exception as e:
            # Relatório de erro mínimo
            try:
                self.pdf.set_font('Arial', 'B', 14)
                self.pdf.cell(0, 10, 'ERRO NO RELATORIO', 0, 1, 'C')
                self.pdf.ln(5)
                self.pdf.set_font('Arial', '', 10)
                error_msg = f'Erro: {str(e)[:50]}'
                self.pdf.cell(0, 8, error_msg, 0, 1)
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                self.pdf.output(output_path)
                return output_path
            except:
                # Último recurso - criar arquivo vazio
                with open(output_path, 'w') as f:
                    f.write('Erro na geracao do relatorio PDF')
                return output_path
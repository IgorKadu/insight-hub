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
        
        # Carregamento resiliente de fontes Unicode (DejaVu Sans)
        font_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts')
        font_regular = os.path.join(font_dir, 'DejaVuSans.ttf')
        font_bold = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
        font_italic = os.path.join(font_dir, 'DejaVuSans-Oblique.ttf')
        
        self.available_styles = []
        self.unicode_font_available = False
        
        # Tentar carregar fonte regular
        if os.path.exists(font_regular):
            try:
                self.pdf.add_font('DejaVu', '', font_regular, uni=True)
                self.available_styles.append('')
                self.unicode_font_available = True
                self.default_font = 'DejaVu'
            except Exception as e:
                print(f'Warning: Could not load DejaVu regular font: {e}')
        
        # Tentar carregar fonte Bold independentemente
        if os.path.exists(font_bold):
            try:
                self.pdf.add_font('DejaVu', 'B', font_bold, uni=True)
                self.available_styles.append('B')
            except Exception as e:
                print(f'Warning: Could not load DejaVu bold font: {e}')
        
        # Tentar carregar fonte Italic independentemente
        if os.path.exists(font_italic):
            try:
                self.pdf.add_font('DejaVu', 'I', font_italic, uni=True)
                self.available_styles.append('I')
            except Exception as e:
                print(f'Warning: Could not load DejaVu italic font: {e}')
        
        # Fallback para Arial se DejaVu não funcionou
        if not self.unicode_font_available:
            self.default_font = 'Arial'
            print('Warning: Using Arial fallback - Portuguese accents may be degraded')
        
        self.pdf.add_page()
        self._safe_set_font(self.default_font, 'B', 16)
    
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
    
    def _safe_makedirs(self, output_path: str) -> None:
        """Cria diretório apenas se necessário, evitando erro com arquivo sem diretório"""
        output_dir = os.path.dirname(output_path)
        if output_dir:  # Só criar se há diretório no caminho
            os.makedirs(output_dir, exist_ok=True)
    
    def _safe_set_font(self, family: str, style: str = '', size: int = 12) -> None:
        """Define fonte de forma segura, fazendo fallback se o estilo não estiver disponível"""
        if self.unicode_font_available and family == 'DejaVu':
            # Verificar se o estilo está disponível
            if style in self.available_styles:
                self.pdf.set_font(family, style, size)
            else:
                # Fallback para estilo regular se o solicitado não estiver disponível
                fallback_style = '' if '' in self.available_styles else 'B' if 'B' in self.available_styles else ''
                self.pdf.set_font(family, fallback_style, size)
        else:
            # Usar Arial com estilos padrão
            self.pdf.set_font(family, style, size)
    
    def _force_ascii_text(self, text: str) -> str:
        """Força conversão para ASCII seguro para tratamento de erros"""
        if not text:
            return ""
        
        text = self.strip_emojis(str(text))
        
        # Mapeamento rigoroso para ASCII
        char_map = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n',
            'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
            'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
            'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C', 'Ñ': 'N'
        }
        
        # Substituir caracteres especiais
        for char, replacement in char_map.items():
            text = text.replace(char, replacement)
        
        # Forçar remoção de qualquer caractere não ASCII
        text = ''.join(c if ord(c) < 128 else '?' for c in text)
        
        return text
    
    def safe_text(self, text: str) -> str:
        """Converte texto para formato seguro para PDF"""
        if not text:
            return ""
        
        text = self.strip_emojis(str(text))
        
        # Se temos fonte Unicode, manter caracteres portugueses
        if self.unicode_font_available:
            return text
        
        # Fallback: Mapeamento de caracteres especiais portugueses para ASCII
        char_map = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n',
            'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
            'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
            'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C', 'Ñ': 'N'
        }
        
        # Substituir caracteres especiais apenas se fonte Unicode não disponível
        for char, replacement in char_map.items():
            text = text.replace(char, replacement)
        
        # Remover qualquer caractere não ASCII restante
        text = ''.join(c if ord(c) < 128 else '?' for c in text)
        
        return text
    
    def add_header(self, title: str):
        """Adiciona cabeçalho da seção"""
        self.pdf.set_fill_color(230, 230, 230)
        self._safe_set_font(self.default_font, 'B', 14)
        safe_title = self.safe_text(title)
        self.pdf.cell(0, 10, safe_title, 0, 1, 'L', True)
        self.pdf.ln(5)
    
    def add_subsection(self, title: str):
        """Adiciona subtítulo"""
        self._safe_set_font(self.default_font, 'B', 12)
        safe_title = self.safe_text(title)
        self.pdf.cell(0, 8, safe_title, 0, 1, 'L')
        self.pdf.ln(3)
    
    def add_metric(self, label: str, value: str, unit: str = ""):
        """Adiciona métrica formatada"""
        self._safe_set_font(self.default_font, '', 10)
        safe_label = self.safe_text(label)
        self.pdf.cell(100, 6, f'{safe_label}:', 0, 0, 'L')
        self._safe_set_font(self.default_font, 'B', 10)
        safe_value = self.safe_text(str(value))
        safe_unit = self.safe_text(unit)
        self.pdf.cell(0, 6, f'{safe_value} {safe_unit}', 0, 1, 'L')
    
    def add_table_header(self, headers: List[str]):
        """Adiciona cabeçalho de tabela"""
        self._safe_set_font(self.default_font, 'B', 9)
        self.pdf.set_fill_color(200, 200, 200)
        col_width = 190 / len(headers)
        for header in headers:
            safe_header = self.safe_text(str(header))
            self.pdf.cell(col_width, 8, safe_header, 1, 0, 'C', True)
        self.pdf.ln()
    
    def add_table_row(self, data: List[str]):
        """Adiciona linha de tabela"""
        self._safe_set_font(self.default_font, '', 8)
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
    
    def _add_safe_text(self, font: str, style: str, size: int, text: str, 
                      align: str = 'L', height: int = 6, border: int = 0) -> None:
        """Adiciona texto de forma segura ao PDF"""
        self._safe_set_font(font, style, size)
        safe_text = self.safe_text(text)
        self.pdf.cell(0, height, safe_text, border, 1, align)
    
    def _generate_error_pdf(self, error_message: str) -> Dict[str, Any]:
        """Gera PDF de erro padronizado"""
        try:
            error_pdf = FPDF()
            error_pdf.add_page()
            error_pdf.set_font('Arial', 'B', 16)
            error_pdf.cell(0, 10, 'ERRO NA GERACAO DO RELATORIO', 0, 1, 'C')
            error_pdf.ln(10)
            error_pdf.set_font('Arial', '', 12)
            safe_error = self.safe_text(error_message[:100])
            error_pdf.cell(0, 10, safe_error, 0, 1, 'C')
            
            # Gerar PDF de forma consistente
            error_output = error_pdf.output(dest='S')
            error_bytes = error_output.encode('latin-1') if isinstance(error_output, str) else error_output
            
            return {
                'success': False,
                'error': error_message,
                'pdf_bytes': error_bytes,
                'filename': 'relatorio_erro.pdf'
            }
        except Exception as e:
            return {
                'success': False,
                'error': error_message,
                'pdf_bytes': b'',
                'filename': 'relatorio_erro.pdf'
            }
    
    def generate_comprehensive_report(self, filtered_df: pd.DataFrame, contexts: Dict[str, Any], 
                                    options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Gera relatório robusto usando dados filtrados e contextos pré-processados"""
        try:
            if options is None:
                options = {}
            
            include_charts = options.get('include_charts', False)
            report_type = options.get('report_type', 'Relatorio Executivo Completo')
            
            if filtered_df.empty:
                return self._generate_error_pdf('Nenhum dado disponivel para gerar relatorio')
            
            # Usar dados e contextos já processados (sem depender de imports externos)
            kpis = contexts.get('kpis', {})
            insights = contexts.get('insights', [])
            predictive_results = contexts.get('predictive', {})
            routes_context = contexts.get('routes', {})
            operational_context = contexts.get('operational', {})
            compliance_context = contexts.get('compliance', {})
            
            # Usar dados filtrados ao invés de recarregar
            total_records = len(filtered_df)
            total_vehicles = filtered_df['placa'].nunique() if 'placa' in filtered_df.columns else 0
            total_clients = filtered_df['cliente'].nunique() if 'cliente' in filtered_df.columns else 0
            
            # Cabeçalho principal aprimorado
            self._add_safe_text(self.default_font, 'B', 20, 'RELATORIO EXECUTIVO INTEGRADO DE FROTA', align='C', height=15)
            self._add_safe_text(self.default_font, 'I', 14, 'Insight Hub - Analise Inteligente e Preditiva', align='C', height=8)
            self._add_safe_text(self.default_font, '', 10, 'Relatorio consolidado com dados de todos os paineis do sistema', align='C', height=6)
            self.pdf.ln(10)
            
            # Informações do relatório com tratamento seguro de datas
            generation_date = datetime.now().strftime("%d/%m/%Y as %H:%M:%S")
            self._add_safe_text(self.default_font, '', 10, f'Data de Geracao: {generation_date}')
            
            # Tratamento seguro do período
            period_start = self.safe_date_format(filtered_df['data'].min() if 'data' in filtered_df.columns else None)
            period_end = self.safe_date_format(filtered_df['data'].max() if 'data' in filtered_df.columns else None)
            self._add_safe_text(self.default_font, '', 10, f'Periodo Analisado: {period_start} a {period_end}')
            
            self._add_safe_text(self.default_font, '', 10, 'Fonte: Dados integrados de 5 paineis analiticos')
            self.pdf.ln(8)
            
            # 1. RESUMO EXECUTIVO COM INSIGHTS INTELIGENTES
            self.add_header('1. RESUMO EXECUTIVO & INSIGHTS AUTOMATICOS')
            
            # Insights críticos no topo
            critical_insights = [i for i in insights if i.get('type') == 'error']
            if critical_insights:
                self.add_subsection('ALERTAS CRITICOS IDENTIFICADOS:')
                for insight in critical_insights[:3]:  # Top 3 críticos
                    title = self.safe_text(insight.get('title', ''))
                    description = self.safe_text(insight.get('description', ''))
                    text = f"* {title}: {description}"
                    # Quebrar linhas longas
                    if len(text) > 80:
                        text = text[:77] + "..."
                    self._add_safe_text(self.default_font, '', 9, text, height=5)
                self.pdf.ln(3)
            
            # Usar KPIs do contexto com fallbacks seguros
            avg_speed = kpis.get('velocidade_media', 0) if kpis else (
                filtered_df['velocidade_km'].mean() if 'velocidade_km' in filtered_df.columns else 0)
            max_speed = kpis.get('velocidade_maxima', 0) if kpis else (
                filtered_df['velocidade_km'].max() if 'velocidade_km' in filtered_df.columns else 0)
            total_distance = kpis.get('km_total', 0) if kpis else (
                filtered_df['odometro_periodo_km'].sum() if 'odometro_periodo_km' in filtered_df.columns else 0)
            gps_coverage = kpis.get('cobertura_gps', 0) if kpis else 0
            
            # Métricas principais aprimoradas
            self.add_subsection('METRICAS PRINCIPAIS DA FROTA:')
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
            recommendations_insights = [i for i in insights if i.get('type') in ['warning', 'info']]
            if recommendations_insights:
                self.add_subsection('RECOMENDACOES PRIORITARIAS:')
                for insight in recommendations_insights[:4]:  # Top 4 recomendações
                    recommendation = self.safe_text(insight.get('recommendation', 'Ver detalhes'))
                    if len(recommendation) > 75:
                        recommendation = recommendation[:72] + "..."
                    self._add_safe_text(self.default_font, '', 9, f"* {recommendation}", height=5)
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
                        self._safe_set_font(self.default_font, '', 9)
                        alert_text = f"- {alert.get('vehicle', 'N/A')}: {alert.get('message', 'Alerta detectado')}"
                        self.pdf.cell(0, 5, self.safe_text(alert_text[:90]), 0, 1)
                        
                # Recomendações de manutenção
                recommendations = predictive_results.get('recommendations', [])
                if recommendations:
                    self.add_subsection('Recomendações de Ação:')
                    for rec in recommendations[:3]:  # Top 3 recomendações
                        self._safe_set_font(self.default_font, '', 9)
                        self.pdf.cell(0, 5, self.safe_text(f"- {rec}"[:80]), 0, 1)
            else:
                self._safe_set_font(self.default_font, '', 10)
                self.pdf.cell(0, 6, self.safe_text('Dados insuficientes para análise preditiva (mínimo 50 registros)'), 0, 1)
            
            self.pdf.ln(5)
            
            # 3. ANÁLISE POR CLIENTE
            self.add_header('3. ANÁLISE POR CLIENTE')
            
            client_stats = filtered_df.groupby('cliente').agg({
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
            if 'latitude' in filtered_df.columns and 'longitude' in filtered_df.columns:
                valid_coords = filtered_df.dropna(subset=['latitude', 'longitude'])
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
                    self._safe_set_font(self.default_font, '', 10)
                    self.pdf.cell(0, 6, self.safe_text('Coordenadas GPS não disponíveis para análise geográfica'), 0, 1)
            else:
                self._safe_set_font(self.default_font, '', 10)
                self.pdf.cell(0, 6, self.safe_text('Dados de localização não encontrados'), 0, 1)
            
            self.pdf.ln(5)
            
            # 5. ANÁLISE DETALHADA POR VEÍCULO
            self.add_header('5. ANÁLISE DETALHADA POR VEÍCULO')
            
            vehicle_stats = filtered_df.groupby(['cliente', 'placa']).agg({
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
            
            # Usar dados de conformidade do contexto
            compliance_data = compliance_context
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
            
            # Distribuição de velocidades do contexto
            speed_distribution = compliance_context.get('speed_distribution', {})
            if speed_distribution:
                speed_ranges = speed_distribution
            else:
                # Fallback se contexto não tiver distribuição
                if 'velocidade_km' in filtered_df.columns:
                    speed_ranges = {
                        '0-30 km/h': len(filtered_df[filtered_df['velocidade_km'] <= 30]),
                        '31-60 km/h': len(filtered_df[(filtered_df['velocidade_km'] > 30) & (filtered_df['velocidade_km'] <= 60)]),
                        '61-80 km/h': len(filtered_df[(filtered_df['velocidade_km'] > 60) & (filtered_df['velocidade_km'] <= 80)]),
                        '81-100 km/h': len(filtered_df[(filtered_df['velocidade_km'] > 80) & (filtered_df['velocidade_km'] <= 100)]),
                        'Acima de 100 km/h': len(filtered_df[filtered_df['velocidade_km'] > 100])
                    }
                else:
                    speed_ranges = {}
            
            self.add_subsection('Distribuição de Velocidades:')
            for faixa, count in speed_ranges.items():
                percentage = (count / total_records * 100) if total_records > 0 else 0
                self.add_metric(faixa, f'{count:,} ({percentage:.1f}%)')
            
            # Alertas de velocidade do contexto
            total_violations = compliance_context.get('total_violations', 0)
            violations = filtered_df[filtered_df['velocidade_km'] > 80] if 'velocidade_km' in filtered_df.columns and not filtered_df.empty else pd.DataFrame()
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
            self._safe_set_font(self.default_font, 'I', 8)
            footer_text = f'Relatorio gerado em {datetime.now().strftime("%d/%m/%Y as %H:%M:%S")} - Insight Hub Fleet Monitor'
            self.pdf.cell(0, 6, self.safe_text(footer_text), 0, 1, 'C')
            
            # Gerar PDF como bytes de forma segura
            pdf_output = self.pdf.output(dest='S')  # Retorna string
            pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else pdf_output
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'relatorio_frota_{timestamp}.pdf'
            
            return {
                'success': True,
                'pdf_bytes': pdf_bytes,
                'filename': filename,
                'total_records': total_records,
                'total_vehicles': total_vehicles,
                'total_clients': total_clients
            }
            
        except Exception as e:
            # Em caso de erro, retornar PDF de erro com encoding seguro
            try:
                error_pdf = FPDF()
                error_pdf.add_page()
                error_pdf.set_font('Arial', 'B', 16)
                error_pdf.cell(0, 10, 'ERRO NA GERACAO DO RELATORIO', 0, 1, 'C')
                error_pdf.ln(10)
                error_pdf.set_font('Arial', '', 12)
                # Sanitizar mensagem de erro
                error_msg = self.safe_text(str(e)[:100])
                error_pdf.cell(0, 10, f'Erro: {error_msg}', 0, 1, 'C')
                
                # Gerar PDF de erro de forma segura
                error_output = error_pdf.output(dest='S')
                error_bytes = error_output.encode('latin-1') if isinstance(error_output, str) else error_output
                
                return {
                    'success': False,
                    'error': str(e),
                    'pdf_bytes': error_bytes,
                    'filename': 'relatorio_erro.pdf'
                }
            except Exception as inner_e:
                return {
                    'success': False,
                    'error': f'Erro critico na geracao: {str(e)}. Erro interno: {str(inner_e)}',
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
                self._safe_set_font(self.default_font, '', 12)
                self.pdf.cell(0, 10, self.safe_text('Nenhum dado disponivel para gerar relatorio'), 0, 1, 'C')
                # Usar output consistente
                pdf_output = self.pdf.output(dest='S')
                pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else pdf_output
                self._safe_makedirs(output_path)
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
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
                self._safe_makedirs(output_path)
                with open(output_path, 'wb') as f:
                    f.write(result['pdf_bytes'])
                return output_path
            else:
                # Gerar relatório básico em caso de erro
                self.pdf.set_font(self.default_font, 'B', 16)
                self.pdf.cell(0, 10, 'RELATORIO DA FROTA', 0, 1, 'C')
                self.pdf.ln(10)
                
                self.pdf.set_font(self.default_font, '', 12)
                self.pdf.cell(0, 8, self.safe_text(f'Data: {datetime.now().strftime("%d/%m/%Y")}'), 0, 1)
                self.pdf.cell(0, 8, self.safe_text(f'Total de registros: {len(df):,}'), 0, 1)
                self._add_safe_text(self.default_font, '', 12, f'Veiculos: {df["placa"].nunique() if "placa" in df.columns else 0}', height=8)
                self._add_safe_text(self.default_font, '', 12, f'Clientes: {df["cliente"].nunique() if "cliente" in df.columns else 0}', height=8)
                
                if 'velocidade_km' in df.columns:
                    self._add_safe_text(self.default_font, '', 12, f'Velocidade media: {df["velocidade_km"].mean():.1f} km/h', height=8)
                
                # Usar output consistente
                pdf_output = self.pdf.output(dest='S')
                pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else pdf_output
                self._safe_makedirs(output_path)
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                return output_path
            
        except Exception as e:
            # Relatório de erro mínimo
            try:
                self.pdf.set_font(self.default_font, 'B', 14)
                self.pdf.cell(0, 10, self.safe_text('ERRO NO RELATORIO'), 0, 1, 'C')
                self.pdf.ln(5)
                self._safe_set_font(self.default_font, '', 10)
                error_msg = self.safe_text(f'Erro: {str(e)[:50]}')
                self.pdf.cell(0, 8, error_msg, 0, 1)
                
                # Usar output consistente
                pdf_output = self.pdf.output(dest='S')
                pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else pdf_output
                self._safe_makedirs(output_path)
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                return output_path
            except:
                # Último recurso - criar arquivo vazio
                with open(output_path, 'w') as f:
                    f.write('Erro na geracao do relatorio PDF')
                return output_path
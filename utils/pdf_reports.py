"""Gerador de Relatórios PDF Avançado"""
from fpdf import FPDF
import pandas as pd
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
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
        """Gera relatório completo e detalhado da frota"""
        try:
            # Carregar dados
            df = DatabaseManager.get_dashboard_data()
            summary = DatabaseManager.get_fleet_summary()
            
            if df.empty:
                self.pdf.cell(0, 10, 'ERRO: Nenhum dado disponível para gerar relatório', 0, 1, 'C')
                self.pdf.output(output_path)
                return output_path
            
            # Cabeçalho principal
            self.pdf.set_font('Arial', 'B', 18)
            self.pdf.cell(0, 15, 'RELATÓRIO EXECUTIVO DE FROTA', 0, 1, 'C')
            self.pdf.set_font('Arial', 'I', 12)
            self.pdf.cell(0, 8, 'Insight Hub - Sistema de Monitoramento Municipal', 0, 1, 'C')
            self.pdf.ln(10)
            
            # Informações do relatório
            self.pdf.set_font('Arial', '', 10)
            self.pdf.cell(0, 6, f'Data de Geração: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1)
            self.pdf.cell(0, 6, f'Período Analisado: {df["data"].min().strftime("%d/%m/%Y")} a {df["data"].max().strftime("%d/%m/%Y")}', 0, 1)
            self.pdf.ln(10)
            
            # 1. RESUMO EXECUTIVO
            self.add_header('1. RESUMO EXECUTIVO')
            
            total_records = len(df)
            total_vehicles = df['placa'].nunique()
            total_clients = df['cliente'].nunique()
            avg_speed = df['velocidade_km'].mean()
            max_speed = df['velocidade_km'].max()
            total_distance = df['odometro_periodo_km'].sum()
            
            # Métricas principais
            self.add_metric('Total de Registros Processados', f'{total_records:,}')
            self.add_metric('Veículos Monitorados', f'{total_vehicles}')
            self.add_metric('Clientes Atendidos', f'{total_clients}')
            self.add_metric('Velocidade Média da Frota', f'{avg_speed:.1f}', 'km/h')
            self.add_metric('Velocidade Máxima Registrada', f'{max_speed:.1f}', 'km/h')
            self.add_metric('Distância Total Percorrida', f'{total_distance:.1f}', 'km')
            
            # Cobertura GPS
            gps_quality = df['gps'].value_counts()
            gps_coverage = (gps_quality.get('Ativo', 0) / total_records * 100) if total_records > 0 else 0
            self.add_metric('Cobertura GPS Ativa', f'{gps_coverage:.1f}', '%')
            self.pdf.ln(5)
            
            # 2. ANÁLISE POR CLIENTE
            self.add_header('2. ANÁLISE POR CLIENTE')
            
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
            
            # 3. ANÁLISE DETALHADA POR VEÍCULO
            self.add_header('3. ANÁLISE DETALHADA POR VEÍCULO')
            
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
            
            # 4. ANÁLISE DE VELOCIDADE E SEGURANÇA
            self.add_header('4. ANÁLISE DE VELOCIDADE E SEGURANÇA')
            
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
            
            # 7. RECOMENDAÇÕES
            self.add_header('7. RECOMENDAÇÕES E ALERTAS')
            
            self.pdf.set_font('Arial', '', 10)
            recommendations = []
            
            if len(violations) > total_records * 0.1:
                recommendations.append("• Implementar treinamento de condução defensiva para reduzir violações de velocidade")
            
            if gps_coverage < 95:
                recommendations.append("• Verificar sistema GPS dos veículos com baixa cobertura")
            
            low_activity_vehicles = vehicle_stats[vehicle_stats[('data', 'count')] < 50].index
            if len(low_activity_vehicles) > 0:
                recommendations.append(f"• Investigar {len(low_activity_vehicles)} veículos com baixa atividade")
            
            if not recommendations:
                recommendations.append("• Frota operando dentro dos parâmetros normais")
                recommendations.append("• Continuar monitoramento regular")
            
            for rec in recommendations:
                self.pdf.cell(0, 6, rec.encode('latin-1', 'replace').decode('latin-1'), 0, 1)
            
            self.pdf.ln(10)
            
            # Rodapé
            self.pdf.set_font('Arial', 'I', 8)
            self.pdf.cell(0, 5, f'Relatório gerado automaticamente pelo Insight Hub em {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', 0, 1, 'C')
            
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
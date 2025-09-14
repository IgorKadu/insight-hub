"""Gerador de Relatórios PDF"""
from fpdf import FPDF
import pandas as pd
from datetime import datetime
from database.db_manager import DatabaseManager
import os

class PDFReportGenerator:
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.add_page()
        self.pdf.set_font('Arial', 'B', 16)
    
    def generate_fleet_report(self, output_path: str = "relatorio_frota.pdf") -> str:
        """Gera relatório completo da frota"""
        # Dados da base
        df = DatabaseManager.get_dashboard_data()
        summary = DatabaseManager.get_fleet_summary()
        
        # Cabeçalho
        self.pdf.cell(200, 10, 'RELATÓRIO DE FROTA - INSIGHT HUB', 0, 1, 'C')
        self.pdf.ln(10)
        
        # Informações gerais
        self.pdf.set_font('Arial', 'B', 12)
        self.pdf.cell(200, 10, f'Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
        self.pdf.ln(5)
        
        # Resumo executivo
        self.pdf.cell(200, 10, 'RESUMO EXECUTIVO', 0, 1)
        self.pdf.set_font('Arial', '', 10)
        self.pdf.cell(200, 8, f'Total de Registros: {summary["total_records"]:,}', 0, 1)
        self.pdf.cell(200, 8, f'Veículos Monitorados: {summary["total_vehicles"]}', 0, 1)
        self.pdf.cell(200, 8, f'Clientes Ativos: {summary["total_clients"]}', 0, 1)
        self.pdf.cell(200, 8, f'Cobertura GPS: {summary["gps_coverage"]:.1f}%', 0, 1)
        self.pdf.cell(200, 8, f'Velocidade Média: {summary["avg_speed"]:.1f} km/h', 0, 1)
        self.pdf.ln(10)
        
        # Análise por veículo
        if not df.empty:
            self.pdf.set_font('Arial', 'B', 12)
            self.pdf.cell(200, 10, 'ANÁLISE POR VEÍCULO', 0, 1)
            self.pdf.set_font('Arial', '', 9)
            
            for veiculo in df['placa'].unique():
                df_veiculo = df[df['placa'] == veiculo]
                vel_media = df_veiculo['velocidade_km'].mean()
                registros = len(df_veiculo)
                
                self.pdf.cell(200, 6, f'{veiculo}: {registros:,} registros, {vel_media:.1f} km/h média', 0, 1)
        
        # Salvar PDF
        self.pdf.output(output_path)
        return output_path
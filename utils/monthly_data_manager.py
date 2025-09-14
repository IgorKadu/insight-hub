"""
Gerenciador de dados mensais - preparado para uploads recorrentes
"""

import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from database.db_manager import DatabaseManager

class MonthlyDataManager:
    """Gerencia uploads de dados mensais com a mesma estrutura"""
    
    @staticmethod
    def process_monthly_upload(csv_files: List[str]) -> Dict[str, Any]:
        """Processa upload mensal de múltiplos arquivos CSV"""
        results = {
            'success': True,
            'processed_files': 0,
            'total_records': 0,
            'new_vehicles': 0,
            'errors': []
        }
        
        for csv_file in csv_files:
            try:
                if not os.path.exists(csv_file):
                    results['errors'].append(f"Arquivo não encontrado: {csv_file}")
                    continue
                
                # Processar arquivo
                result = DatabaseManager.migrate_csv_to_database(csv_file)
                
                if result['success']:
                    results['processed_files'] += 1
                    results['total_records'] += result.get('records_processed', 0)
                    results['new_vehicles'] += result.get('unique_vehicles', 0)
                else:
                    results['errors'].append(f"{os.path.basename(csv_file)}: {result.get('error', 'Erro desconhecido')}")
                    
            except Exception as e:
                results['errors'].append(f"{os.path.basename(csv_file)}: {str(e)}")
        
        # Se houve erros mas alguns sucessos, ainda é parcialmente bem-sucedido
        if results['errors'] and results['processed_files'] == 0:
            results['success'] = False
        
        return results
    
    @staticmethod
    def get_monthly_summary() -> Dict[str, Any]:
        """Resumo dos dados mensais na base"""
        summary = DatabaseManager.get_fleet_summary()
        
        # Adicionar informações específicas mensais
        df = DatabaseManager.get_dashboard_data()
        
        if not df.empty:
            # Análise temporal
            df['mes'] = df['data'].dt.to_period('M')
            monthly_data = df.groupby('mes').agg({
                'placa': 'nunique',
                'velocidade_km': 'mean',
                'data': 'count'
            }).reset_index()
            
            summary['monthly_breakdown'] = monthly_data.to_dict('records')
            summary['data_period'] = {
                'start': df['data'].min().strftime('%d/%m/%Y'),
                'end': df['data'].max().strftime('%d/%m/%Y'),
                'days': (df['data'].max() - df['data'].min()).days
            }
        
        return summary
    
    @staticmethod
    def prepare_for_next_month() -> Dict[str, Any]:
        """Prepara sistema para próximo upload mensal"""
        current_summary = MonthlyDataManager.get_monthly_summary()
        
        return {
            'current_data': current_summary,
            'ready_for_upload': True,
            'upload_instructions': {
                'format': 'CSV com separador ; (ponto e vírgula)',
                'encoding': 'Latin-1 (ISO 8859-1)',
                'required_columns': [
                    'Cliente', 'Placa', 'Ativo', 'Data', 'Data (GPRS)',
                    'Velocidade (Km)', 'Ignição', 'Motorista', 'GPS', 'Gprs',
                    'Localização', 'Endereço', 'Tipo do Evento', 'Cerca',
                    'Saida', 'Entrada', 'Pacote', 'Odômetro do período  (Km)',
                    'Horímetro do período', 'Horímetro embarcado',
                    'Odômetro embarcado (Km)', 'Bateria', 'Imagem', 'Tensão', 'Bloqueado'
                ],
                'date_format': 'DD/MM/AAAA HH:MM:SS (formato brasileiro)',
                'notes': 'O sistema detecta automaticamente o formato e processa múltiplos arquivos'
            }
        }
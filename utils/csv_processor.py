import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
import os
import re

class CSVProcessor:
    """Classe para processar arquivos CSV de dados telemáticos"""
    
    # Campos obrigatórios do CSV
    REQUIRED_FIELDS = [
        'Cliente', 'Placa', 'Ativo', 'Data', 'Data (GPRS)',
        'Velocidade (Km)', 'Ignição', 'Motorista', 'GPS', 'Gprs',
        'Localização', 'Endereço', 'Tipo do Evento', 'Cerca',
        'Saida', 'Entrada', 'Pacote', 'Odômetro do período (Km)',
        'Horímetro do período', 'Horímetro embarcado',
        'Odômetro embarcado (Km)', 'Bateria', 'Imagem', 'Tensão', 'Bloqueado'
    ]
    
    def __init__(self):
        """Inicializa o processador de CSV"""
        self.data = None
        self.validation_errors = []
        
    def validate_csv_structure(self, df):
        """Valida a estrutura do CSV"""
        self.validation_errors = []
        
        # Verificar se todos os campos obrigatórios estão presentes
        missing_fields = []
        for field in self.REQUIRED_FIELDS:
            if field not in df.columns:
                missing_fields.append(field)
        
        if missing_fields:
            self.validation_errors.append(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")
        
        # Verificar se há dados
        if df.empty:
            self.validation_errors.append("O arquivo CSV está vazio")
        
        # Verificar tipos de dados básicos
        try:
            # Tentar converter datas
            if 'Data' in df.columns:
                pd.to_datetime(df['Data'], errors='coerce')
            if 'Data (GPRS)' in df.columns:
                pd.to_datetime(df['Data (GPRS)'], errors='coerce')
        except Exception as e:
            self.validation_errors.append(f"Erro na validação de datas: {str(e)}")
        
        return len(self.validation_errors) == 0
    
    def clean_and_standardize_data(self, df):
        """Limpa e padroniza os dados do CSV"""
        try:
            # Criar cópia do DataFrame
            clean_df = df.copy()
            
            # Padronizar nomes das colunas
            column_mapping = {
                'Cliente': 'cliente',
                'Placa': 'placa',
                'Ativo': 'ativo',
                'Data': 'data',
                'Data (GPRS)': 'data_gprs',
                'Velocidade (Km)': 'velocidade_km',
                'Ignição': 'ignicao',
                'Motorista': 'motorista',
                'GPS': 'gps',
                'Gprs': 'gprs',
                'Localização': 'localizacao',
                'Endereço': 'endereco',
                'Tipo do Evento': 'tipo_evento',
                'Cerca': 'cerca',
                'Saida': 'saida',
                'Entrada': 'entrada',
                'Pacote': 'pacote',
                'Odômetro do período (Km)': 'odometro_periodo_km',
                'Horímetro do período': 'horimetro_periodo',
                'Horímetro embarcado': 'horimetro_embarcado',
                'Odômetro embarcado (Km)': 'odometro_embarcado_km',
                'Bateria': 'bateria',
                'Imagem': 'imagem',
                'Tensão': 'tensao',
                'Bloqueado': 'bloqueado'
            }
            
            clean_df = clean_df.rename(columns=column_mapping)
            
            # Converter datas
            clean_df['data'] = pd.to_datetime(clean_df['data'], errors='coerce')
            clean_df['data_gprs'] = pd.to_datetime(clean_df['data_gprs'], errors='coerce')
            
            # Converter velocidade para numérico
            clean_df['velocidade_km'] = pd.to_numeric(clean_df['velocidade_km'], errors='coerce')
            
            # Converter GPS e GPRS para booleano
            clean_df['gps'] = clean_df['gps'].astype(str).str.strip() == '1'
            clean_df['gprs'] = clean_df['gprs'].astype(str).str.strip() == '1'
            
            # Converter bloqueado para booleano
            clean_df['bloqueado'] = clean_df['bloqueado'].astype(str).str.strip() == '1'
            
            # Converter odômetros para numérico
            clean_df['odometro_periodo_km'] = pd.to_numeric(clean_df['odometro_periodo_km'], errors='coerce')
            clean_df['odometro_embarcado_km'] = pd.to_numeric(clean_df['odometro_embarcado_km'], errors='coerce')
            
            # Converter tensão para numérico
            clean_df['tensao'] = pd.to_numeric(clean_df['tensao'], errors='coerce')
            
            # Limpar campos de texto
            text_fields = ['cliente', 'placa', 'ativo', 'motorista', 'endereco', 'tipo_evento']
            for field in text_fields:
                if field in clean_df.columns:
                    clean_df[field] = clean_df[field].astype(str).str.strip()
            
            # Padronizar placas (remover espaços e converter para maiúsculas)
            clean_df['placa'] = clean_df['placa'].str.upper().str.replace(' ', '')
            
            # Adicionar timestamp de processamento
            clean_df['processed_at'] = datetime.now()
            
            return clean_df
            
        except Exception as e:
            self.validation_errors.append(f"Erro na limpeza dos dados: {str(e)}")
            return None
    
    def convert_time_to_hours(self, time_str):
        """Converte string de tempo (HH:MM:SS) para horas decimais"""
        if pd.isna(time_str) or time_str == '':
            return 0.0
        
        try:
            time_str = str(time_str).strip()
            if ':' in time_str:
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
                seconds = int(parts[2]) if len(parts) > 2 else 0
                return hours + minutes/60 + seconds/3600
            else:
                return float(time_str)
        except:
            return 0.0
    
    def process_csv_file(self, uploaded_file):
        """Processa arquivo CSV completo"""
        try:
            # Ler arquivo CSV
            df = pd.read_csv(uploaded_file)
            
            # Validar estrutura
            if not self.validate_csv_structure(df):
                return None, self.validation_errors
            
            # Limpar e padronizar dados
            clean_df = self.clean_and_standardize_data(df)
            
            if clean_df is None:
                return None, self.validation_errors
            
            # Converter horímetros
            if 'horimetro_periodo' in clean_df.columns:
                clean_df['horimetro_periodo_horas'] = clean_df['horimetro_periodo'].apply(
                    self.convert_time_to_hours
                )
            
            # Salvar dados processados
            self.save_processed_data(clean_df)
            
            self.data = clean_df
            return clean_df, []
            
        except Exception as e:
            error_msg = f"Erro no processamento do arquivo: {str(e)}"
            return None, [error_msg]
    
    def save_processed_data(self, df):
        """Salva dados processados em arquivo"""
        try:
            # Criar diretório se não existir
            os.makedirs('data', exist_ok=True)
            
            # Salvar arquivo principal
            df.to_csv('data/processed_data.csv', index=False)
            
            # Salvar backup com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            df.to_csv(f'data/backup_{timestamp}.csv', index=False)
            
        except Exception as e:
            st.error(f"Erro ao salvar dados: {str(e)}")
    
    def get_data_summary(self, df):
        """Gera resumo dos dados processados"""
        if df is None or df.empty:
            return {}
        
        summary = {
            'total_registros': len(df),
            'total_veiculos': df['placa'].nunique(),
            'total_clientes': df['cliente'].nunique(),
            'periodo_inicio': df['data'].min(),
            'periodo_fim': df['data'].max(),
            'velocidade_media': df['velocidade_km'].mean(),
            'velocidade_maxima': df['velocidade_km'].max(),
            'total_km_periodo': df['odometro_periodo_km'].sum(),
            'registros_com_gps': df['gps'].sum(),
            'registros_sem_gps': (~df['gps']).sum(),
            'veiculos_bloqueados': df['bloqueado'].sum()
        }
        
        return summary

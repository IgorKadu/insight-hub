import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
import os
import re
import sys
sys.path.append('.')
from database.db_manager import DatabaseManager

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
        self.use_database = True  # Enable database integration
        
    def normalize_column_name(self, col_name):
        """Normaliza nome da coluna removendo espaços extras e caracteres especiais"""
        # Remover espaços extras e normalizar
        normalized = re.sub(r'\s+', ' ', str(col_name).strip())
        return normalized
    
    def validate_csv_structure(self, df):
        """Valida a estrutura do CSV"""
        self.validation_errors = []
        
        # Normalizar nomes das colunas - handle double spaces and irregular spacing
        df.columns = [' '.join(col.strip().split()) for col in df.columns]
        
        # Criar mapeamento de colunas normalizadas
        normalized_columns = {self.normalize_column_name(col): col for col in df.columns}
        
        # Verificar se todos os campos obrigatórios estão presentes
        missing_fields = []
        for field in self.REQUIRED_FIELDS:
            field_normalized = self.normalize_column_name(field)
            if field_normalized not in normalized_columns:
                missing_fields.append(field)
        
        if missing_fields:
            self.validation_errors.append(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")
        
        # Verificar se há dados
        if df.empty:
            self.validation_errors.append("O arquivo CSV está vazio")
        
        # Verificar tipos de dados básicos
        try:
            # Tentar converter datas (formato brasileiro)
            if 'Data' in df.columns:
                pd.to_datetime(df['Data'], errors='coerce', dayfirst=True)
            if 'Data (GPRS)' in df.columns:
                pd.to_datetime(df['Data (GPRS)'], errors='coerce', dayfirst=True)
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
                'Odômetro do período  (Km)': 'odometro_periodo_km',  # Handle double space variant
                'Horímetro do período': 'horimetro_periodo',
                'Horímetro embarcado': 'horimetro_embarcado',
                'Odômetro embarcado (Km)': 'odometro_embarcado_km',
                'Bateria': 'bateria',
                'Imagem': 'imagem',
                'Tensão': 'tensao',
                'Bloqueado': 'bloqueado'
            }
            
            clean_df = clean_df.rename(columns=column_mapping)
            
            # Converter datas com formato brasileiro (DD/MM/YYYY)
            clean_df['data'] = pd.to_datetime(clean_df['data'], errors='coerce', dayfirst=True)
            clean_df['data_gprs'] = pd.to_datetime(clean_df['data_gprs'], errors='coerce', dayfirst=True)
            
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
            # Detectar separador e encoding do arquivo
            separator = ','
            encoding = 'utf-8'
            
            # Tentar diferentes separadores e encodings
            sample = uploaded_file.read(1024)
            uploaded_file.seek(0)
            
            if isinstance(sample, bytes):
                sample_str = sample.decode('utf-8', errors='ignore')
            else:
                sample_str = sample
            
            # Detectar separador (vírgula vs ponto e vírgula)
            if sample_str.count(';') > sample_str.count(','):
                separator = ';'
            
            # Tentar ler com diferentes encodings
            df = None
            encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']
            
            for enc in encodings_to_try:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=separator, encoding=enc)
                    encoding = enc
                    break
                except:
                    continue
            
            if df is None:
                # Fall back para leitura padrão
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=separator)
            
            st.info(f"📄 Arquivo lido com separador '{separator}' e encoding '{encoding}'")
            
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
            filename = getattr(uploaded_file, 'name', 'uploaded_file.csv')
            self.save_processed_data(clean_df, filename)
            
            self.data = clean_df
            return clean_df, []
            
        except Exception as e:
            error_msg = f"Erro no processamento do arquivo: {str(e)}"
            return None, [error_msg]
    
    def save_processed_data(self, df, filename=None):
        """Salva dados processados na base de dados e como backup"""
        try:
            # Salvar na base de dados se habilitado
            if self.use_database:
                result = DatabaseManager.migrate_csv_to_database_from_df(df, filename)
                if not result['success']:
                    st.error(f"Erro ao salvar na base de dados: {result['error']}")
                    # Fall back to file save
                    self.use_database = False
            
            # Sempre manter backup em arquivo
            os.makedirs('data', exist_ok=True)
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

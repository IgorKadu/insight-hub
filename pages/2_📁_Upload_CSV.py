import streamlit as st
import pandas as pd
import os
from datetime import datetime
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.csv_processor import CSVProcessor
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="Upload CSV - Insight Hub",
    page_icon="📁",
    layout="wide"
)

def main():
    st.title("📁 Upload e Processamento de Dados CSV")
    st.markdown("---")
    
    # Informações sobre o formato esperado
    with st.expander("📋 Formato do Arquivo CSV", expanded=False):
        st.markdown("""
        ### Campos Obrigatórios (25 campos):
        
        1. **Cliente** - Nome do cliente/empresa
        2. **Placa** - Placa do veículo
        3. **Ativo** - Identificador do ativo
        4. **Data** - Data/hora do evento
        5. **Data (GPRS)** - Data/hora de comunicação GPRS
        6. **Velocidade (Km)** - Velocidade em km/h
        7. **Ignição** - Status da ignição (D/L)
        8. **Motorista** - Identificação do motorista
        9. **GPS** - Status do GPS (0/1)
        10. **Gprs** - Status do GPRS (0/1)
        11. **Localização** - Coordenadas do veículo
        12. **Endereço** - Endereço convertido
        13. **Tipo do Evento** - Tipo do evento registrado
        14. **Cerca** - Informações de cerca eletrônica
        15. **Saida** - Status das saídas digitais
        16. **Entrada** - Status das entradas digitais
        17. **Pacote** - Informações de pacotes de dados
        18. **Odômetro do período (Km)** - Km percorridos
        19. **Horímetro do período** - Tempo de funcionamento
        20. **Horímetro embarcado** - Contador de horas
        21. **Odômetro embarcado (Km)** - Odômetro embarcado
        22. **Bateria** - Nível de bateria
        23. **Imagem** - Link para imagem (opcional)
        24. **Tensão** - Tensão elétrica
        25. **Bloqueado** - Status de bloqueio (0/1)
        
        ### Observações:
        - O arquivo deve estar em formato CSV com separador vírgula (,)
        - Todos os 25 campos são obrigatórios
        - Tamanho máximo: 50MB
        - Até 100.000 registros por arquivo
        """)
    
    # Área de upload
    st.subheader("📤 Fazer Upload do Arquivo CSV")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo CSV:",
        type=['csv'],
        help="Arquivo CSV com dados telemáticos da frota",
        accept_multiple_files=False
    )
    
    if uploaded_file is not None:
        # Mostrar informações do arquivo
        file_details = {
            "Nome do Arquivo": uploaded_file.name,
            "Tamanho": f"{uploaded_file.size / 1024 / 1024:.2f} MB",
            "Tipo": uploaded_file.type
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"""
            **📄 Detalhes do Arquivo:**
            - Nome: {file_details['Nome do Arquivo']}
            - Tamanho: {file_details['Tamanho']}
            - Tipo: {file_details['Tipo']}
            """)
        
        # Verificações iniciais
        if uploaded_file.size > 50 * 1024 * 1024:  # 50MB
            st.error("❌ Arquivo muito grande! Tamanho máximo: 50MB")
            st.stop()
        
        # Preview do arquivo
        try:
            # Ler as primeiras linhas para preview
            preview_df = pd.read_csv(uploaded_file, nrows=5)
            
            with col2:
                st.success(f"""
                **✅ Preview do Arquivo:**
                - Colunas encontradas: {len(preview_df.columns)}
                - Registros (preview): {len(preview_df)}
                """)
            
            st.subheader("👀 Preview dos Dados")
            st.dataframe(preview_df, use_container_width=True)
            
            # Reset do ponteiro do arquivo
            uploaded_file.seek(0)
            
            # Botão para processar
            if st.button("🚀 Processar Arquivo", type="primary", use_container_width=True):
                process_csv_file(uploaded_file)
                
        except Exception as e:
            st.error(f"❌ Erro ao ler o arquivo: {str(e)}")
    
    # Mostrar histórico de arquivos processados
    show_processing_history()

def process_csv_file(uploaded_file):
    """Processa o arquivo CSV enviado"""
    
    with st.spinner("🔄 Processando arquivo..."):
        # Inicializar processador
        processor = CSVProcessor()
        
        # Processar arquivo
        processed_df, errors = processor.process_csv_file(uploaded_file)
        
        if errors:
            st.error("❌ Erros encontrados durante o processamento:")
            for error in errors:
                st.error(f"• {error}")
            st.stop()
        
        if processed_df is None:
            st.error("❌ Falha no processamento do arquivo.")
            st.stop()
        
        # Mostrar resultado do processamento
        st.success("✅ Arquivo processado com sucesso!")
        
        # Mostrar resumo
        summary = processor.get_data_summary(processed_df)
        show_processing_summary(summary, uploaded_file.name)
        
        # Salvar registro do processamento
        save_processing_record(uploaded_file.name, summary)
        
        # Mostrar preview dos dados processados
        st.subheader("📊 Dados Processados")
        st.dataframe(
            processed_df.head(10),
            use_container_width=True
        )
        
        # Botão para ir ao dashboard
        if st.button("📊 Ir para Dashboard", type="primary"):
            st.switch_page("pages/1_📊_Dashboard.py")

def show_processing_summary(summary, filename):
    """Mostra resumo do processamento"""
    
    st.subheader("📊 Resumo do Processamento")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📁 Total de Registros",
            value=f"{summary.get('total_registros', 0):,}"
        )
    
    with col2:
        st.metric(
            label="🚗 Total de Veículos",
            value=f"{summary.get('total_veiculos', 0):,}"
        )
    
    with col3:
        st.metric(
            label="🏢 Total de Clientes",
            value=f"{summary.get('total_clientes', 0):,}"
        )
    
    with col4:
        st.metric(
            label="📅 Período",
            value=f"{(summary.get('periodo_fim', datetime.now()) - summary.get('periodo_inicio', datetime.now())).days + 1} dias"
        )
    
    # Métricas adicionais
    st.markdown("### 📈 Métricas dos Dados")
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric(
            label="⚡ Velocidade Média",
            value=f"{summary.get('velocidade_media', 0):.1f} km/h"
        )
    
    with col6:
        st.metric(
            label="🏎️ Velocidade Máxima",
            value=f"{summary.get('velocidade_maxima', 0):.0f} km/h"
        )
    
    with col7:
        st.metric(
            label="🛣️ Total KM",
            value=f"{summary.get('total_km_periodo', 0):.0f} km"
        )
    
    with col8:
        st.metric(
            label="📡 Com GPS",
            value=f"{summary.get('registros_com_gps', 0):,}"
        )

def save_processing_record(filename, summary):
    """Salva registro do processamento"""
    try:
        os.makedirs('data', exist_ok=True)
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'summary': summary
        }
        
        # Carregar histórico existente
        history_file = 'data/processing_history.csv'
        
        if os.path.exists(history_file):
            history_df = pd.read_csv(history_file)
        else:
            history_df = pd.DataFrame()
        
        # Adicionar novo registro
        new_record = pd.DataFrame([{
            'timestamp': record['timestamp'],
            'filename': filename,
            'total_registros': summary.get('total_registros', 0),
            'total_veiculos': summary.get('total_veiculos', 0),
            'total_clientes': summary.get('total_clientes', 0),
            'periodo_inicio': summary.get('periodo_inicio', ''),
            'periodo_fim': summary.get('periodo_fim', ''),
            'velocidade_media': summary.get('velocidade_media', 0),
            'total_km': summary.get('total_km_periodo', 0)
        }])
        
        history_df = pd.concat([history_df, new_record], ignore_index=True)
        history_df.to_csv(history_file, index=False)
        
    except Exception as e:
        st.warning(f"⚠️ Não foi possível salvar o registro: {str(e)}")

def show_processing_history():
    """Mostra histórico de processamentos"""
    history_file = 'data/processing_history.csv'
    
    if not os.path.exists(history_file):
        st.info("📋 Nenhum histórico de processamento encontrado.")
        return
    
    try:
        history_df = pd.read_csv(history_file)
        
        if history_df.empty:
            st.info("📋 Nenhum arquivo processado ainda.")
            return
        
        st.subheader("📋 Histórico de Processamentos")
        
        # Ordenar por timestamp mais recente
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        history_df = history_df.sort_values('timestamp', ascending=False)
        
        # Formatar para exibição
        display_df = history_df.copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%d/%m/%Y %H:%M')
        display_df = display_df.rename(columns={
            'timestamp': 'Data/Hora',
            'filename': 'Arquivo',
            'total_registros': 'Registros',
            'total_veiculos': 'Veículos',
            'total_clientes': 'Clientes',
            'velocidade_media': 'Vel. Média',
            'total_km': 'Total KM'
        })
        
        # Selecionar colunas para exibição
        display_columns = ['Data/Hora', 'Arquivo', 'Registros', 'Veículos', 'Clientes', 'Vel. Média', 'Total KM']
        
        st.dataframe(
            display_df[display_columns].head(10),
            use_container_width=True,
            hide_index=True
        )
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🗑️ Limpar Histórico", type="secondary"):
                if os.path.exists(history_file):
                    os.remove(history_file)
                    st.success("✅ Histórico limpo com sucesso!")
                    st.rerun()
        
        with col_btn2:
            if os.path.exists('data/processed_data.csv'):
                if st.button("🗂️ Limpar Dados Processados", type="secondary"):
                    # Remover arquivos de dados
                    for file in os.listdir('data'):
                        if file.endswith('.csv') and file != 'processing_history.csv':
                            os.remove(os.path.join('data', file))
                    st.success("✅ Dados processados removidos!")
                    st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar histórico: {str(e)}")

if __name__ == "__main__":
    main()

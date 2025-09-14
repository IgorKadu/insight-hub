import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Insight Hub - Monitoramento de Frotas",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhor aparência
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

def load_processed_data():
    """Carrega dados processados se existirem"""
    data_file = "data/processed_data.csv"
    if os.path.exists(data_file):
        try:
            df = pd.read_csv(data_file)
            df['data'] = pd.to_datetime(df['data'])
            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            return pd.DataFrame()
    return pd.DataFrame()

def main():
    # Header principal
    st.markdown('<h1 class="main-header">🚛 Insight Hub</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Plataforma de Monitoramento e Análise de Frotas Municipais</p>', unsafe_allow_html=True)
    
    # Verificar se há dados processados
    df = load_processed_data()
    
    if df.empty:
        st.warning("📁 Nenhum dado encontrado. Faça o upload de um arquivo CSV na página 'Upload CSV' para começar.")
        
        # Informações sobre o sistema
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎯 **Funcionalidades Principais**
            
            - **📊 Dashboard Interativo**: KPIs em tempo real
            - **📁 Upload de CSV**: Processamento de dados telemáticos
            - **🔍 Análise Detalhada**: Filtros avançados por cliente e período
            - **📈 Comparação de Veículos**: Análise comparativa de performance
            - **🧠 Insights Automáticos**: Geração inteligente de relatórios
            """)
        
        with col2:
            st.markdown("""
            ### 📋 **Campos Obrigatórios do CSV**
            
            - Cliente, Placa, Ativo, Data, Data (GPRS)
            - Velocidade (Km), Ignição, Motorista
            - GPS, Gprs, Localização, Endereço
            - Tipo do Evento, Cerca, Saída, Entrada
            - Pacote, Odômetro do período (Km)
            - Horímetro do período, Horímetro embarcado
            - Odômetro embarcado (Km), Bateria
            - Imagem, Tensão, Bloqueado
            """)
        
        st.markdown("---")
        st.info("💡 **Dica**: Comece fazendo o upload de um arquivo CSV com dados de frota na aba lateral.")
        
    else:
        # Mostrar resumo dos dados carregados
        st.success(f"✅ Dados carregados: {len(df):,} registros processados")
        
        # Métricas gerais
        st.markdown("### 📈 **Visão Geral dos Dados**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_vehicles = df['placa'].nunique()
            st.metric("🚗 Total de Veículos", f"{total_vehicles:,}")
        
        with col2:
            total_clients = df['cliente'].nunique()
            st.metric("🏢 Total de Clientes", f"{total_clients:,}")
        
        with col3:
            date_range = df['data'].max() - df['data'].min()
            st.metric("📅 Período dos Dados", f"{date_range.days} dias")
        
        with col4:
            total_records = len(df)
            st.metric("📊 Total de Registros", f"{total_records:,}")
        
        # Gráfico de distribuição temporal
        st.markdown("### 📊 **Distribuição Temporal dos Dados**")
        
        # Agrupar por data
        daily_data = df.groupby(df['data'].dt.date).size().reset_index()
        daily_data.columns = ['data', 'registros']
        
        fig = px.line(
            daily_data, 
            x='data', 
            y='registros',
            title='Registros por Data',
            labels={'data': 'Data', 'registros': 'Número de Registros'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Top veículos por atividade
        st.markdown("### 🚗 **Veículos Mais Ativos**")
        
        vehicle_activity = df.groupby('placa').size().sort_values(ascending=False).head(10)
        
        fig_bar = px.bar(
            x=vehicle_activity.values,
            y=vehicle_activity.index,
            orientation='h',
            title='Top 10 Veículos por Número de Registros',
            labels={'x': 'Número de Registros', 'y': 'Placa'}
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

if __name__ == "__main__":
    main()

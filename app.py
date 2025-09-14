import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from database.db_manager import DatabaseManager

# Configuração da página
st.set_page_config(
    page_title="🚛 Insight Hub",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhor aparência e substituir nome "app"
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
    /* Substituir o texto "app" no botão de navegação por "Insight Hub" */
    [data-testid="stSidebar"] a[href="/"] p,
    [data-testid="stSidebar"] a[href="/?nav=wide"] p,
    [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] p,
    [data-testid="stSidebar"] .stSidebarNav a:first-child p {
        font-size: 0 !important;
        color: transparent !important;
        position: relative;
    }
    [data-testid="stSidebar"] a[href="/"] p::after,
    [data-testid="stSidebar"] a[href="/?nav=wide"] p::after,
    [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] p::after,
    [data-testid="stSidebar"] .stSidebarNav a:first-child p::after {
        content: "🚛 Insight Hub";
        font-size: 16px !important;
        color: #262730 !important;
        font-weight: normal;
        position: absolute;
        left: 0;
        top: 0;
    }
    /* Seletor mais genérico para capturar o botão app */
    [data-testid="stSidebar"] ul li:first-child a p {
        font-size: 0 !important;
        color: transparent !important;
        position: relative;
    }
    [data-testid="stSidebar"] ul li:first-child a p::after {
        content: "🚛 Insight Hub";
        font-size: 16px !important;
        color: #262730 !important;
        font-weight: normal;
        position: absolute;
        left: 0;
        top: 0;
    }
    </style>
""", unsafe_allow_html=True)

def load_processed_data():
    """Carrega dados da base PostgreSQL"""
    try:
        df = DatabaseManager.get_dashboard_data()
        if not df.empty:
            st.success(f"✅ Dados carregados: {len(df):,} registros da base PostgreSQL")
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados da base: {str(e)}")
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
            
            - **📊 Análise Profissional**: KPIs em tempo real  
            - **📁 Upload de CSV**: Processamento de dados telemáticos
            - **🔍 Análise Detalhada**: Filtros avançados por cliente e período
            - **📈 Comparação de Veículos**: Análise comparativa de performance
            - **🔧 Manutenção Preditiva**: Alertas e previsões
            - **🚨 Alertas**: Monitoramento em tempo real
            - **🧠 Insights Automáticos**: Geração inteligente de relatórios
            - **📄 Relatórios Avançados**: Documentação completa
            - **🚨 Controle Operacional**: Conformidade municipal
            """)
        
        with col2:
            st.markdown("""
            ### 📋 **Campos Obrigatórios do CSV**
            
            - Cliente, Placa, Ativo, Data, Data (GPRS)
            - Velocidade (Km/h), Ignição, Motorista
            - GPS, GPRS, Localização, Endereço
            - Tipo do Evento, Cerca, Saída, Entrada
            - Pacote, Odômetro do período (Km)
            - Horímetro do período, Horímetro embarcado
            - Odômetro embarcado (Km), Bateria (%)
            - Imagem, Tensão (V), Bloqueado
            - Latitude, Longitude (coordenadas GPS)
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
        st.plotly_chart(fig, width='stretch')
        
        # Indicadores de Qualidade e Performance
        st.markdown("### 🎯 **Indicadores de Performance do Sistema**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Calcular métricas de qualidade
        coordenadas_validas = len(df[(df['latitude'] != 0) & (df['longitude'] != 0) & 
                                   (df['latitude'].notna()) & (df['longitude'].notna())])
        gps_quality = df['gps'].mean() if 'gps' in df.columns else 0
        gprs_quality = df['gprs'].mean() if 'gprs' in df.columns else 0
        velocidade_media = df['velocidade_km'].mean() if 'velocidade_km' in df.columns else 0
        
        with col1:
            coord_percent = (coordenadas_validas / len(df) * 100) if len(df) > 0 else 0
            st.metric("🗺️ Coordenadas Válidas", f"{coord_percent:.1f}%", 
                     delta=f"{coordenadas_validas:,} de {len(df):,}")
        
        with col2:
            st.metric("📡 Qualidade GPS", f"{gps_quality:.1f}%", 
                     delta="Média geral")
        
        with col3:
            st.metric("📶 Qualidade GPRS", f"{gprs_quality:.1f}%", 
                     delta="Conectividade")
        
        with col4:
            st.metric("🚗 Velocidade Média", f"{velocidade_media:.1f} km/h", 
                     delta="Frota geral")
        
        # Análise de Cobertura Temporal e Operacional
        st.markdown("### ⏰ **Análise Operacional**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Análise por horário
            if 'data' in df.columns:
                df_temp = df.copy()
                df_temp['hora'] = df_temp['data'].dt.hour
                hourly_activity = df_temp.groupby('hora').size()
                
                fig_hourly = px.bar(
                    x=hourly_activity.index,
                    y=hourly_activity.values,
                    title='Atividade por Hora do Dia',
                    labels={'x': 'Hora', 'y': 'Número de Registros'},
                    color=hourly_activity.values,
                    color_continuous_scale='Blues'
                )
                fig_hourly.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_hourly, width='stretch')
        
        with col2:
            # Top veículos por atividade
            vehicle_activity = df.groupby('placa').size().sort_values(ascending=False).head(8)
            
            fig_vehicles = px.bar(
                x=vehicle_activity.values,
                y=vehicle_activity.index,
                orientation='h',
                title='Top 8 Veículos Mais Ativos',
                labels={'x': 'Registros', 'y': 'Placa'},
                color=vehicle_activity.values,
                color_continuous_scale='Greens'
            )
            fig_vehicles.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_vehicles, width='stretch')
        
        # Alertas e Anomalias
        st.markdown("### 🚨 **Status e Alertas do Sistema**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Veículos inativos (sem registros recentes)
            if 'data' in df.columns and not df.empty:
                data_mais_recente = df['data'].max()
                veiculos_inativos = df[df['data'] < (data_mais_recente - timedelta(days=1))]['placa'].nunique()
                total_veiculos = df['placa'].nunique()
                st.metric("⚠️ Veículos com Inatividade", f"{veiculos_inativos}",
                         delta=f"de {total_veiculos} total")
        
        with col2:
            # Registros sem coordenadas
            registros_sem_coord = len(df) - coordenadas_validas
            percent_sem_coord = (registros_sem_coord / len(df) * 100) if len(df) > 0 else 0
            delta_color = "inverse" if percent_sem_coord > 5 else "normal"
            st.metric("📍 Registros sem GPS", f"{registros_sem_coord:,}",
                     delta=f"{percent_sem_coord:.1f}% do total",
                     delta_color=delta_color)
        
        with col3:
            # Análise de conectividade
            if 'ignicao' in df.columns:
                ignicao_ligada = len(df[df['ignicao'] == 'Ligada']) if 'ignicao' in df.columns else 0
                percent_ignicao = (ignicao_ligada / len(df) * 100) if len(df) > 0 else 0
                st.metric("🔑 Registros c/ Ignição", f"{percent_ignicao:.1f}%",
                         delta=f"{ignicao_ligada:,} registros")
        
        # Distribuição temporal melhorada
        st.markdown("### 📊 **Distribuição Temporal dos Dados**")
        
        # Agrupar por data
        daily_data = df.groupby(df['data'].dt.date).size().reset_index()
        daily_data.columns = ['data', 'registros']
        
        fig = px.line(
            daily_data, 
            x='data', 
            y='registros',
            title='Evolução Diária de Registros',
            labels={'data': 'Data', 'registros': 'Número de Registros'},
            markers=True
        )
        fig.update_layout(height=400)
        fig.add_hline(y=daily_data['registros'].mean(), line_dash="dash", 
                     line_color="red", annotation_text="Média")
        st.plotly_chart(fig, width='stretch')
        
        # Informações adicionais de sistema
        st.markdown("### 💾 **Informações do Sistema**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Última atualização
            if 'data' in df.columns and not df.empty:
                ultima_atualizacao = df['data'].max()
                st.info(f"🕐 **Última atualização:** {ultima_atualizacao.strftime('%d/%m/%Y %H:%M')}")
        
        with col2:
            # Período total coberto
            if 'data' in df.columns and not df.empty:
                periodo_total = (df['data'].max() - df['data'].min()).days
                st.info(f"📅 **Período coberto:** {periodo_total} dias de dados")
        
        with col3:
            # Taxa de dados por dia
            if 'data' in df.columns and not df.empty:
                registros_por_dia = len(df) / max(1, (df['data'].max() - df['data'].min()).days)
                st.info(f"📈 **Taxa média:** {registros_por_dia:.0f} registros/dia")


if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_analyzer import DataAnalyzer
from utils.visualizations import FleetVisualizations
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="Dashboard - Insight Hub",
    page_icon="📊",
    layout="wide"
)

def load_data():
    """Carrega dados processados da base de dados ou arquivo"""
    try:
        # Tentar carregar da base de dados primeiro
        if DatabaseManager.has_data():
            df = DatabaseManager.get_dashboard_data()
            if not df.empty:
                return df
        
        # Fall back para arquivo se não há dados na base de dados
        data_file = "data/processed_data.csv"
        if os.path.exists(data_file):
            df = pd.read_csv(data_file)
            df['data'] = pd.to_datetime(df['data'])
            return df
            
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("📊 Dashboard de Monitoramento")
    st.markdown("---")
    
    # Carregar dados
    df = load_data()
    
    if df.empty:
        st.warning("📁 Nenhum dado encontrado. Faça o upload de um arquivo CSV primeiro.")
        st.stop()
    
    # Inicializar analisador com dados da base de dados
    analyzer = DataAnalyzer.from_database()
    visualizer = FleetVisualizations(analyzer)
    
    # Sidebar com filtros
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por cliente
    clientes = ['Todos'] + sorted(df['cliente'].unique().tolist())
    cliente_selecionado = st.sidebar.selectbox("Cliente:", clientes)
    
    # Filtro por período
    min_date = df['data'].min().date()
    max_date = df['data'].max().date()
    
    col_data1, col_data2 = st.sidebar.columns(2)
    with col_data1:
        data_inicio = st.date_input("Data Início:", min_date, min_value=min_date, max_value=max_date)
    with col_data2:
        data_fim = st.date_input("Data Fim:", max_date, min_value=min_date, max_value=max_date)
    
    # Filtro por veículo
    veiculos_disponiveis = ['Todos']
    if cliente_selecionado != "Todos":
        veiculos_disponiveis.extend(sorted(df[df['cliente'] == cliente_selecionado]['placa'].unique().tolist()))
    else:
        veiculos_disponiveis.extend(sorted(df['placa'].unique().tolist()))
    
    veiculo_selecionado = st.sidebar.selectbox("Veículo:", veiculos_disponiveis)
    
    # Aplicar filtros
    filtered_df = analyzer.apply_filters(
        cliente=cliente_selecionado,
        placa=veiculo_selecionado,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    if filtered_df.empty:
        st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados.")
        st.stop()
    
    # Obter KPIs
    kpis = analyzer.get_kpis()
    
    # Mostrar métricas principais
    st.header("📈 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🚗 Total de Veículos",
            value=f"{kpis['total_veiculos']:,}",
            delta=f"{len(filtered_df):,} registros"
        )
    
    with col2:
        st.metric(
            label="⚡ Velocidade Média",
            value=f"{kpis['velocidade_media']:.1f} km/h",
            delta=f"Max: {kpis['velocidade_maxima']:.0f} km/h"
        )
    
    with col3:
        st.metric(
            label="🛣️ Distância Total",
            value=f"{kpis['distancia_total']:.0f} km",
            delta=f"{kpis['tempo_ativo_horas']:.1f} horas ativas"
        )
    
    with col4:
        st.metric(
            label="📡 Cobertura GPS",
            value=f"{kpis['cobertura_gps']:.1f}%",
            delta=f"{kpis['veiculos_bloqueados']} bloqueados"
        )
    
    st.markdown("---")
    
    # Gráficos principais
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Distribuição de Velocidade")
        
        speed_dist_fig = px.histogram(
            filtered_df,
            x='velocidade_km',
            nbins=30,
            title='Distribuição de Velocidade',
            labels={'velocidade_km': 'Velocidade (km/h)', 'count': 'Frequência'}
        )
        speed_dist_fig.update_layout(height=400)
        st.plotly_chart(speed_dist_fig, use_container_width=True)
    
    with col_right:
        st.subheader("🚗 Top 10 Veículos Mais Ativos")
        
        vehicle_activity = filtered_df.groupby('placa').size().sort_values(ascending=False).head(10)
        
        activity_fig = px.bar(
            x=vehicle_activity.values,
            y=vehicle_activity.index,
            orientation='h',
            title='Registros por Veículo',
            labels={'x': 'Número de Registros', 'y': 'Placa'}
        )
        activity_fig.update_layout(height=400)
        st.plotly_chart(activity_fig, use_container_width=True)
    
    # Análise temporal
    st.subheader("⏰ Análise Temporal")
    
    # Atividade por hora
    hourly_activity = filtered_df.groupby(filtered_df['data'].dt.hour).agg({
        'placa': 'nunique',
        'velocidade_km': 'mean'
    }).reset_index()
    
    col_temp1, col_temp2 = st.columns(2)
    
    with col_temp1:
        hourly_vehicles_fig = px.line(
            hourly_activity,
            x='data',
            y='placa',
            title='Veículos Ativos por Hora',
            labels={'data': 'Hora do Dia', 'placa': 'Número de Veículos Ativos'}
        )
        hourly_vehicles_fig.update_layout(height=350)
        st.plotly_chart(hourly_vehicles_fig, use_container_width=True)
    
    with col_temp2:
        hourly_speed_fig = px.line(
            hourly_activity,
            x='data',
            y='velocidade_km',
            title='Velocidade Média por Hora',
            labels={'data': 'Hora do Dia', 'velocidade_km': 'Velocidade Média (km/h)'}
        )
        hourly_speed_fig.update_layout(height=350)
        st.plotly_chart(hourly_speed_fig, use_container_width=True)
    
    # Atividade diária (se mais de um dia)
    if kpis['periodo_dias'] > 1:
        daily_activity = filtered_df.groupby(filtered_df['data'].dt.date).agg({
            'placa': 'nunique',
            'velocidade_km': 'mean',
            'odometro_periodo_km': 'sum'
        }).reset_index()
        
        st.subheader("📅 Tendência Diária")
        
        daily_fig = px.line(
            daily_activity,
            x='data',
            y='placa',
            title='Veículos Ativos por Dia',
            labels={'data': 'Data', 'placa': 'Número de Veículos Ativos'}
        )
        daily_fig.update_layout(height=400)
        st.plotly_chart(daily_fig, use_container_width=True)
    
    # Tabela de resumo por veículo
    st.subheader("📋 Resumo por Veículo")
    
    vehicle_summary = filtered_df.groupby('placa').agg({
        'velocidade_km': ['count', 'mean', 'max'],
        'odometro_periodo_km': 'sum',
        'gps': lambda x: (x.sum() / len(x)) * 100,
        'bloqueado': 'any'
    }).round(2)
    
    # Achatar MultiIndex
    vehicle_summary.columns = [
        'Registros', 'Vel. Média', 'Vel. Máxima', 
        'KM Total', 'GPS (%)', 'Bloqueado'
    ]
    
    vehicle_summary = vehicle_summary.sort_values('Registros', ascending=False)
    
    st.dataframe(
        vehicle_summary,
        use_container_width=True,
        height=300
    )
    
    # Estatísticas do período filtrado
    st.markdown("---")
    st.subheader("📊 Estatísticas do Período")
    
    info_col1, info_col2, info_col3 = st.columns(3)
    
    with info_col1:
        st.info(f"""
        **📅 Período Analisado:**
        - Início: {data_inicio.strftime('%d/%m/%Y')}
        - Fim: {data_fim.strftime('%d/%m/%Y')}
        - Duração: {kpis['periodo_dias']} dias
        """)
    
    with info_col2:
        st.info(f"""
        **🚗 Frota:**
        - Total de Veículos: {kpis['total_veiculos']:,}
        - Total de Registros: {kpis['total_registros']:,}
        - Média por Veículo: {kpis['total_registros']/kpis['total_veiculos']:.0f}
        """)
    
    with info_col3:
        st.info(f"""
        **⚡ Performance:**
        - Velocidade Média: {kpis['velocidade_media']:.1f} km/h
        - Distância Total: {kpis['distancia_total']:.0f} km
        - Tempo Ativo: {kpis['tempo_ativo_horas']:.1f} horas
        """)

if __name__ == "__main__":
    main()

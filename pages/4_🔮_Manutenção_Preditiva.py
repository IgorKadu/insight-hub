"""
Página de Manutenção Preditiva - Análise Avançada com ML
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.ml_predictive import PredictiveMaintenanceAnalyzer

# Configuração da página
st.set_page_config(
    page_title="Manutenção Preditiva",
    page_icon="🔮",
    layout="wide"
)

st.title("🔮 Manutenção Preditiva")
st.markdown("Análise avançada com Machine Learning para prevenção de falhas")

# Verificar se há dados
if not DatabaseManager.has_data():
    st.warning("⚠️ Nenhum dado encontrado. Faça o upload de um arquivo CSV primeiro.")
    st.stop()

# Carregar dados
with st.spinner("Carregando dados..."):
    try:
        df = DatabaseManager.get_dashboard_data()
        if df.empty:
            st.error("❌ Erro ao carregar dados da base de dados")
            st.stop()
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        st.stop()

# Filtros laterais
st.sidebar.header("🔧 Filtros")

# Filtro de cliente
clientes = sorted(df['cliente'].unique())
cliente_selecionado = st.sidebar.selectbox(
    "Cliente:",
    options=['Todos'] + clientes,
    index=0
)

# Filtro de veículo
if cliente_selecionado != 'Todos':
    veiculos = sorted(df[df['cliente'] == cliente_selecionado]['placa'].unique())
else:
    veiculos = sorted(df['placa'].unique())

veiculo_selecionado = st.sidebar.selectbox(
    "Veículo:",
    options=['Todos'] + list(veiculos),
    index=0
)

# Filtro de período
periodo = st.sidebar.selectbox(
    "Período:",
    options=['Últimos 7 dias', 'Últimos 30 dias', 'Todos'],
    index=1
)

# Aplicar filtros
df_filtrado = df.copy()

if cliente_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['cliente'] == cliente_selecionado]

if veiculo_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['placa'] == veiculo_selecionado]

# Filtro de período
if periodo != 'Todos':
    data_limite = datetime.now()
    if periodo == 'Últimos 7 dias':
        data_limite -= timedelta(days=7)
    elif periodo == 'Últimos 30 dias':
        data_limite -= timedelta(days=30)
    
    df_filtrado = df_filtrado[df_filtrado['data'] >= data_limite]

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
    st.stop()

# Análise de Manutenção Preditiva
st.header("🤖 Análise de Machine Learning")

with st.spinner("Executando análise preditiva..."):
    analyzer = PredictiveMaintenanceAnalyzer()
    resultado = analyzer.analyze_vehicle_health(df_filtrado)

if resultado['status'] == 'error':
    st.error(f"❌ {resultado['message']}")
    st.stop()

# Dashboard de Health Scores
col1, col2, col3, col4 = st.columns(4)

health_scores = resultado['health_scores']

with col1:
    score_geral = health_scores.get('geral', 0)
    cor_geral = 'green' if score_geral > 80 else 'orange' if score_geral > 60 else 'red'
    st.metric(
        label="🏥 Saúde Geral",
        value=f"{score_geral}%",
        delta=None
    )
    st.markdown(f"<div style='color:{cor_geral}'>●</div>", unsafe_allow_html=True)

with col2:
    score_bateria = health_scores.get('bateria', 0)
    cor_bateria = 'green' if score_bateria > 70 else 'orange' if score_bateria > 50 else 'red'
    st.metric(
        label="🔋 Bateria",
        value=f"{score_bateria}%"
    )
    st.markdown(f"<div style='color:{cor_bateria}'>●</div>", unsafe_allow_html=True)

with col3:
    score_comportamento = health_scores.get('comportamento', 0)
    cor_comportamento = 'green' if score_comportamento > 70 else 'orange' if score_comportamento > 50 else 'red'
    st.metric(
        label="📊 Comportamento",
        value=f"{score_comportamento}%"
    )
    st.markdown(f"<div style='color:{cor_comportamento}'>●</div>", unsafe_allow_html=True)

with col4:
    score_velocidade = health_scores.get('velocidade', 0)
    cor_velocidade = 'green' if score_velocidade > 70 else 'orange' if score_velocidade > 50 else 'red'
    st.metric(
        label="🚗 Velocidade",
        value=f"{score_velocidade}%"
    )
    st.markdown(f"<div style='color:{cor_velocidade}'>●</div>", unsafe_allow_html=True)

# Gráfico de Health Scores
fig_health = go.Figure()

scores = [health_scores.get(k, 0) for k in ['bateria', 'comportamento', 'velocidade']]
labels = ['Bateria', 'Comportamento', 'Velocidade']
colors = ['#ff7f0e', '#2ca02c', '#d62728']

fig_health.add_trace(go.Bar(
    x=labels,
    y=scores,
    marker_color=colors,
    text=[f"{s}%" for s in scores],
    textposition='auto',
))

fig_health.update_layout(
    title="📊 Scores de Saúde do Veículo",
    yaxis_title="Score (%)",
    yaxis=dict(range=[0, 100]),
    showlegend=False,
    height=400
)

st.plotly_chart(fig_health, use_container_width=True)

# Alertas de Manutenção
st.header("🚨 Alertas de Manutenção")

maintenance_alerts = resultado['maintenance_alerts']

if maintenance_alerts:
    for alert in maintenance_alerts:
        severidade = alert['severidade']
        cor = '🔴' if severidade == 'Alta' else '🟡' if severidade == 'Média' else '🟢'
        
        with st.expander(f"{cor} {alert['tipo']} - {severidade}"):
            st.write(f"**Descrição:** {alert['descricao']}")
            st.write(f"**Prazo:** {alert['prazo']}")
else:
    st.success("✅ Nenhum alerta de manutenção detectado!")

# Anomalias Detectadas
st.header("⚠️ Anomalias Detectadas")

anomalies = resultado['anomalies']
anomaly_count = anomalies.get('count', 0)

col1, col2 = st.columns([1, 2])

with col1:
    st.metric(
        label="Total de Anomalias",
        value=anomaly_count
    )
    
    if anomaly_count > 0:
        severity = anomalies.get('severity', 'Baixa')
        color_map = {'Alta': '🔴', 'Média': '🟡', 'Baixa': '🟢'}
        st.write(f"**Severidade:** {color_map.get(severity, '🟢')} {severity}")

with col2:
    # Gráfico de anomalias ao longo do tempo
    if anomaly_count > 0 and 'indices' in anomalies:
        try:
            anomaly_indices = anomalies['indices']
            if anomaly_indices:
                df_anomalies = df_filtrado.iloc[anomaly_indices].copy()
                
                fig_anomalies = px.scatter(
                    df_anomalies,
                    x='data',
                    y='velocidade_km',
                    title="Anomalias de Velocidade",
                    color_discrete_sequence=['red'],
                    hover_data=['placa']
                )
                
                fig_anomalies.update_layout(height=300)
                st.plotly_chart(fig_anomalies, use_container_width=True)
        except Exception as e:
            st.write("Dados de anomalias não disponíveis para visualização")

# Padrões de Uso
st.header("📈 Padrões de Uso")

patterns = resultado.get('patterns', {})

if patterns:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚗 Padrões de Velocidade")
        vel_patterns = patterns.get('velocidade', {})
        if vel_patterns:
            st.write(f"**Velocidade Média:** {vel_patterns.get('media', 0)} km/h")
            st.write(f"**Velocidade Máxima:** {vel_patterns.get('maxima', 0)} km/h")
            st.write(f"**Excessos de Velocidade:** {vel_patterns.get('excessos', 0)}")
            st.write(f"**Paradas:** {vel_patterns.get('paradas', 0)}")
    
    with col2:
        st.subheader("⏰ Padrões Temporais")
        temp_patterns = patterns.get('uso_temporal', {})
        if temp_patterns:
            st.write(f"**Horário de Pico:** {temp_patterns.get('horario_pico', 'N/A')}h")
            st.write(f"**Horário de Menor Uso:** {temp_patterns.get('horario_baixo', 'N/A')}h")
            st.write(f"**Uso Noturno:** {temp_patterns.get('uso_noturno', 0)} registros")

# Recomendações
st.header("💡 Recomendações")

recommendations = resultado.get('recommendations', [])
if recommendations:
    for rec in recommendations:
        st.write(f"• {rec}")
else:
    st.info("📋 Nenhuma recomendação específica no momento.")

# Informações adicionais
st.header("ℹ️ Informações da Análise")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📊 Registros Analisados", len(df_filtrado))

with col2:
    periodo_analise = df_filtrado['data'].max() - df_filtrado['data'].min()
    st.metric("📅 Período", f"{periodo_analise.days} dias")

with col3:
    st.metric("🚗 Veículos", df_filtrado['placa'].nunique())

st.info("🤖 **Sobre a Análise:** Esta análise utiliza algoritmos de Machine Learning (Isolation Forest) para detectar anomalias e padrões nos dados telemáticos, fornecendo insights preditivos para manutenção preventiva.")
"""Página de Alertas em Tempo Real"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.alert_system import AlertSystem

st.set_page_config(page_title="Alertas", page_icon="🚨", layout="wide")
st.title("🚨 Alertas em Tempo Real")

if not DatabaseManager.has_data():
    st.warning("⚠️ Nenhum dado encontrado.")
    st.stop()

# Sistema de alertas
alert_system = AlertSystem()

# Auto-refresh a cada 30 segundos
if st.button("🔄 Atualizar Alertas"):
    st.rerun()

# Resumo dos alertas
col1, col2, col3, col4 = st.columns(4)
summary = alert_system.get_alert_summary()

with col1:
    st.metric("🚨 Total", summary['total_alerts'])
with col2:
    st.metric("🔴 Alta", summary['high_severity'], delta=f"+{summary['high_severity']}")
with col3:
    st.metric("🟡 Média", summary['medium_severity'])
with col4:
    st.metric("🟢 Baixa", summary['low_severity'])

# Lista de alertas
st.header("📋 Alertas Ativos")
alerts = alert_system.check_realtime_alerts()

if alerts:
    for alert in sorted(alerts, key=lambda x: x['timestamp'], reverse=True):
        severity_color = {
            'Alta': '🔴',
            'Média': '🟡', 
            'Baixa': '🟢'
        }
        
        with st.expander(f"{severity_color[alert['severidade']]} {alert['tipo']} - {alert['veiculo']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Valor:** {alert['valor']}")
                st.write(f"**Veículo:** {alert['veiculo']}")
            with col2:
                st.write(f"**Horário:** {alert['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}")
                st.write(f"**Local:** {alert['localizacao']}")
else:
    st.success("✅ Nenhum alerta ativo!")

# Configurações de alertas
st.header("⚙️ Configurações")
with st.expander("Configurar Limites"):
    col1, col2 = st.columns(2)
    with col1:
        vel_max = st.number_input("Velocidade Máxima (km/h)", value=80, min_value=50, max_value=120)
        bat_baixa = st.number_input("Bateria Baixa (V)", value=12.0, min_value=10.0, max_value=15.0)
    with col2:
        vel_crit = st.number_input("Velocidade Crítica (km/h)", value=100, min_value=80, max_value=150)
        bat_crit = st.number_input("Bateria Crítica (V)", value=11.0, min_value=9.0, max_value=12.0)
    
    if st.button("💾 Salvar Configurações"):
        st.success("Configurações salvas!")

# Histórico de alertas por hora
st.header("📊 Histórico de Alertas")
if alerts:
    df_alerts = pd.DataFrame(alerts)
    df_alerts['hora'] = df_alerts['timestamp'].dt.hour
    alerts_por_hora = df_alerts.groupby('hora').size().reset_index(name='count')
    
    fig = px.bar(alerts_por_hora, x='hora', y='count', title="Alertas por Hora")
    st.plotly_chart(fig, use_container_width=True)
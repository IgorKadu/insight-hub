"""Painel de Mapa de Rotas - Análise de Trajetos e Velocidade"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.data_analyzer import DataAnalyzer
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Mapa de Rotas", page_icon="🗺️", layout="wide")
st.title("🗺️ Mapa de Rotas")
st.markdown("**Análise de trajetos, frequência de rotas, desvios e picos de velocidade**")

# Carregar dados
df = DatabaseManager.get_dashboard_data()
if df.empty:
    st.warning("⚠️ Nenhum dado encontrado. Faça o upload de um arquivo CSV primeiro.")
    st.stop()
else:
    st.success(f"✅ Dados carregados: {len(df):,} registros para análise de rotas")

# Filtros na sidebar
with st.sidebar:
    st.header("🔍 Filtros de Análise")
    
    # Filtro de cliente
    clients = ["Todos"] + sorted(df['cliente'].unique().tolist())
    selected_client = st.selectbox("Cliente:", clients, index=0)
    
    # Filtrar veículos baseado no cliente
    if selected_client != "Todos":
        vehicles_df = df[df['cliente'] == selected_client]
    else:
        vehicles_df = df
    
    vehicles = ["Todos"] + sorted(vehicles_df['placa'].unique().tolist())
    selected_vehicle = st.selectbox("Veículo:", vehicles, index=0)
    
    # Filtro de período
    st.subheader("📅 Período")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Data Início:",
            value=datetime.now().date() - timedelta(days=7)
        )
    with col2:
        end_date = st.date_input(
            "Data Fim:",
            value=datetime.now().date()
        )
    
    # Filtros de análise
    st.subheader("⚡ Parâmetros de Análise")
    speed_threshold = st.slider(
        "Limite de velocidade para picos (km/h):",
        min_value=50,
        max_value=120,
        value=80,
        step=5
    )
    
    deviation_radius = st.slider(
        "Raio para detecção de desvios (km):",
        min_value=0.5,
        max_value=5.0,
        value=2.0,
        step=0.5
    )

# Aplicar filtros usando método centralizado do DataAnalyzer
analyzer = DataAnalyzer(df)
filtered_df = analyzer.apply_filters(
    cliente=selected_client,
    placa=selected_vehicle,
    data_inicio=start_date,
    data_fim=end_date
)

if filtered_df.empty:
    st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")
    
    # Ajudar o usuário a entender o problema
    st.info("💡 **Dicas para encontrar dados:**")
    st.markdown("""
    - ✅ Verifique se o **período de datas** corresponde aos dados disponíveis
    - ✅ Experimente ampliar o **intervalo de datas** 
    - ✅ Tente selecionar **"Todos"** para cliente ou veículo
    - ✅ Use filtros mais amplos para ver dados disponíveis
    """)
    st.stop()

# Preparar dados para análise de rotas
def prepare_route_data(df):
    """Prepara dados para análise de rotas"""
    route_df = df.copy()
    
    # Garantir colunas necessárias
    required_cols = ['latitude', 'longitude', 'velocidade_km', 'data', 'placa']
    available_cols = [col for col in required_cols if col in route_df.columns]
    
    if len(available_cols) < 3:
        return pd.DataFrame()
    
    # Remover registros sem coordenadas válidas
    route_df = route_df.dropna(subset=['latitude', 'longitude'])
    route_df = route_df[(route_df['latitude'] != 0) & (route_df['longitude'] != 0)]
    
    # Converter velocidade para numérico
    if 'velocidade_km' in route_df.columns:
        route_df['velocidade_km'] = pd.to_numeric(route_df['velocidade_km'], errors='coerce')
        route_df['velocidade_km'] = route_df['velocidade_km'].fillna(0)
    
    return route_df

route_data = prepare_route_data(filtered_df)

if route_data.empty:
    st.warning("⚠️ Dados insuficientes para análise de rotas (faltam coordenadas válidas).")
    st.stop()

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Mapa Interativo", 
    "📊 Análise de Velocidade", 
    "🛣️ Rotas Frequentes",
    "⚠️ Desvios Detectados",
    "📈 Padrões Temporais"
])

with tab1:
    st.header("🗺️ Mapa Interativo de Trajetos")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if not route_data.empty and len(route_data) > 0:
            # Criar mapa Folium
            center_lat = route_data['latitude'].mean()
            center_lon = route_data['longitude'].mean()
            
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=12,
                tiles='OpenStreetMap'
            )
            
            # Adicionar pontos coloridos por velocidade
            for idx, row in route_data.iterrows():
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    color = 'red' if row.get('velocidade_km', 0) > speed_threshold else 'green'
                    popup_text = f"""
                    Veículo: {row.get('placa', 'N/A')}<br>
                    Velocidade: {row.get('velocidade_km', 0):.1f} km/h<br>
                    Data: {row.get('data', 'N/A')}<br>
                    Coordenadas: {row['latitude']:.6f}, {row['longitude']:.6f}
                    """
                    
                    folium.CircleMarker(
                        location=[row['latitude'], row['longitude']],
                        radius=3,
                        popup=popup_text,
                        color=color,
                        fill=True,
                        fillOpacity=0.7
                    ).add_to(m)
            
            # Exibir mapa
            map_data = st_folium(m, width=700, height=400)
        else:
            st.warning("Não há dados de coordenadas suficientes para exibir o mapa.")
    
    with col2:
        st.subheader("📊 Resumo da Rota")
        
        if not route_data.empty:
            total_points = len(route_data)
            speed_violations = len(route_data[route_data['velocidade_km'] > speed_threshold])
            avg_speed = route_data['velocidade_km'].mean()
            max_speed = route_data['velocidade_km'].max()
            
            st.metric("Total de Pontos", f"{total_points:,}")
            st.metric("Velocidade Média", f"{avg_speed:.1f} km/h")
            st.metric("Velocidade Máxima", f"{max_speed:.1f} km/h")
            st.metric("Picos de Velocidade", f"{speed_violations:,}", 
                     delta=f"{(speed_violations/total_points*100):.1f}% do total")

with tab2:
    st.header("📊 Análise de Velocidade")
    
    if not route_data.empty and 'velocidade_km' in route_data.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Histograma de velocidades
            fig_hist = px.histogram(
                route_data, 
                x='velocidade_km',
                nbins=30,
                title="Distribuição de Velocidades",
                labels={'velocidade_km': 'Velocidade (km/h)', 'count': 'Frequência'}
            )
            fig_hist.add_vline(x=speed_threshold, line_dash="dash", line_color="red", 
                              annotation_text=f"Limite: {speed_threshold} km/h")
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Velocidade ao longo do tempo
            if 'data' in route_data.columns:
                route_data_sorted = route_data.sort_values('data')
                fig_time = px.line(
                    route_data_sorted,
                    x='data',
                    y='velocidade_km',
                    title="Velocidade ao Longo do Tempo",
                    labels={'data': 'Data/Hora', 'velocidade_km': 'Velocidade (km/h)'}
                )
                fig_time.add_hline(y=speed_threshold, line_dash="dash", line_color="red")
                st.plotly_chart(fig_time, use_container_width=True)
        
        # Tabela de picos de velocidade
        speed_violations_df = route_data[route_data['velocidade_km'] > speed_threshold]
        if not speed_violations_df.empty:
            st.subheader("⚠️ Picos de Velocidade Detectados")
            speed_violations_display = speed_violations_df[['data', 'placa', 'velocidade_km', 'latitude', 'longitude']].copy()
            speed_violations_display = speed_violations_display.sort_values('velocidade_km', ascending=False)
            st.dataframe(speed_violations_display.head(20), use_container_width=True)

with tab3:
    st.header("🛣️ Análise de Rotas Frequentes")
    
    if not route_data.empty:
        # Agrupar pontos próximos para identificar rotas frequentes
        st.subheader("📍 Pontos Mais Visitados")
        
        # Criar grid de coordenadas para agrupar pontos próximos
        precision = 0.01  # Precisão do grid (aproximadamente 1km)
        route_data['lat_grid'] = (route_data['latitude'] / precision).round() * precision
        route_data['lon_grid'] = (route_data['longitude'] / precision).round() * precision
        
        # Contar frequência de cada ponto
        point_frequency = route_data.groupby(['lat_grid', 'lon_grid']).size().reset_index(name='frequencia')
        point_frequency = point_frequency.sort_values('frequencia', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top 10 pontos mais frequentes
            top_points = point_frequency.head(10)
            fig_freq = px.bar(
                top_points,
                x='frequencia',
                y=range(len(top_points)),
                orientation='h',
                title="Top 10 Locais Mais Visitados",
                labels={'frequencia': 'Número de Visitas', 'y': 'Ranking'}
            )
            st.plotly_chart(fig_freq, use_container_width=True)
        
        with col2:
            # Análise por horário
            if 'data' in route_data.columns:
                route_data['hora'] = route_data['data'].dt.hour
                hourly_activity = route_data.groupby('hora').size().reset_index(name='atividade')
                
                fig_hourly = px.bar(
                    hourly_activity,
                    x='hora',
                    y='atividade',
                    title="Atividade por Horário do Dia",
                    labels={'hora': 'Hora do Dia', 'atividade': 'Número de Registros'}
                )
                st.plotly_chart(fig_hourly, use_container_width=True)

with tab4:
    st.header("⚠️ Análise de Desvios de Rota")
    
    if not route_data.empty:
        st.subheader("🔍 Detecção de Desvios")
        
        # Calcular centro geográfico das rotas
        center_lat = route_data['latitude'].mean()
        center_lon = route_data['longitude'].mean()
        
        # Calcular distância do centro para cada ponto
        def haversine_distance(lat1, lon1, lat2, lon2):
            from math import radians, cos, sin, asin, sqrt
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            return 2 * asin(sqrt(a)) * 6371  # Raio da Terra em km
        
        route_data['distancia_centro'] = route_data.apply(
            lambda row: haversine_distance(center_lat, center_lon, row['latitude'], row['longitude']),
            axis=1
        )
        
        # Identificar desvios (pontos muito distantes do centro)
        desvios = route_data[route_data['distancia_centro'] > deviation_radius]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total de Desvios Detectados", len(desvios))
            st.metric("Raio de Análise", f"{deviation_radius} km")
            
            if not desvios.empty:
                st.subheader("📋 Lista de Desvios")
                desvios_display = desvios[['data', 'placa', 'distancia_centro', 'velocidade_km']].copy()
                desvios_display['distancia_centro'] = desvios_display['distancia_centro'].round(2)
                st.dataframe(desvios_display.head(10), use_container_width=True)
        
        with col2:
            if not route_data.empty:
                # Gráfico de dispersão das distâncias
                fig_scatter = px.scatter(
                    route_data,
                    x='distancia_centro',
                    y='velocidade_km',
                    color='placa' if 'placa' in route_data.columns else None,
                    title="Desvios vs Velocidade",
                    labels={'distancia_centro': 'Distância do Centro (km)', 'velocidade_km': 'Velocidade (km/h)'}
                )
                fig_scatter.add_vline(x=deviation_radius, line_dash="dash", line_color="red",
                                    annotation_text=f"Limite: {deviation_radius} km")
                st.plotly_chart(fig_scatter, use_container_width=True)

with tab5:
    st.header("📈 Padrões Temporais de Movimento")
    
    if not route_data.empty and 'data' in route_data.columns:
        # Análise por dia da semana
        route_data['dia_semana'] = route_data['data'].dt.day_name()
        route_data['dia_semana_num'] = route_data['data'].dt.dayofweek
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Atividade por dia da semana
            daily_activity = route_data.groupby('dia_semana').size().reset_index(name='atividade')
            # Ordenar por dia da semana
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            daily_activity['dia_semana'] = pd.Categorical(daily_activity['dia_semana'], categories=day_order, ordered=True)
            daily_activity = daily_activity.sort_values('dia_semana')
            
            fig_daily = px.bar(
                daily_activity,
                x='dia_semana',
                y='atividade',
                title="Atividade por Dia da Semana",
                labels={'dia_semana': 'Dia da Semana', 'atividade': 'Número de Registros'}
            )
            st.plotly_chart(fig_daily, use_container_width=True)
        
        with col2:
            # Heatmap de atividade por hora e dia
            route_data['hora'] = route_data['data'].dt.hour
            heatmap_data = route_data.groupby(['dia_semana_num', 'hora']).size().reset_index(name='atividade')
            
            # Criar pivot table para heatmap
            pivot_data = heatmap_data.pivot(index='dia_semana_num', columns='hora', values='atividade').fillna(0)
            
            fig_heatmap = px.imshow(
                pivot_data,
                labels=dict(x="Hora do Dia", y="Dia da Semana", color="Atividade"),
                title="Padrão de Atividade (Heatmap)",
                aspect="auto"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Análise de velocidade média por período
        st.subheader("🚗 Velocidade Média por Período")
        route_data['periodo'] = route_data['hora'].apply(
            lambda x: 'Madrugada (00-06)' if x < 6 
            else 'Manhã (06-12)' if x < 12 
            else 'Tarde (12-18)' if x < 18 
            else 'Noite (18-24)'
        )
        
        period_stats = route_data.groupby('periodo')['velocidade_km'].agg(['mean', 'max', 'count']).reset_index()
        period_stats.columns = ['periodo', 'velocidade_media', 'velocidade_maxima', 'total_registros']
        
        fig_period = px.bar(
            period_stats,
            x='periodo',
            y='velocidade_media',
            title="Velocidade Média por Período do Dia",
            labels={'periodo': 'Período', 'velocidade_media': 'Velocidade Média (km/h)'}
        )
        st.plotly_chart(fig_period, use_container_width=True)
        
        # Tabela resumo
        st.subheader("📊 Resumo Estatístico por Período")
        st.dataframe(period_stats, use_container_width=True)

# Footer com informações técnicas
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    <p>🗺️ Mapa de Rotas - Sistema de Análise de Trajetos</p>
    <p>Dados processados: {total_records:,} registros | Última atualização: {timestamp}</p>
</div>
""".format(
    total_records=len(route_data),
    timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
), unsafe_allow_html=True)
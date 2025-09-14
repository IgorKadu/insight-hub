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
import pydeck as pdk

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
    
    # Opções de visualização
    col_controls = st.columns([2, 1, 1])
    with col_controls[0]:
        view_mode = st.radio(
            "Modo de Visualização:",
            options=["Pontos Individuais", "Densidade (Hexágonos)"],
            horizontal=True,
            help="Pontos para datasets pequenos, Hexágonos para otimizar performance com muitos dados"
        )
    
    with col_controls[1]:
        expand_map = st.checkbox("🔍 Expandir Mapa", help="Aumentar o tamanho do mapa para melhor visualização")
    
    with col_controls[2]:
        if not route_data.empty:
            st.metric("Total de Pontos", f"{len(route_data):,}")
    
    # Configuração do mapa responsivo
    map_height = 800 if expand_map else 600
    
    if not route_data.empty and len(route_data) > 0:
        # Preparar dados para pydeck
        center_lat = route_data['latitude'].mean()
        center_lon = route_data['longitude'].mean()
        
        # Preparar dados com cores baseadas na velocidade
        map_data = route_data.copy()
        map_data['color'] = map_data['velocidade_km'].apply(
            lambda x: [255, 0, 0, 160] if x > speed_threshold else [0, 255, 0, 160]  # [R, G, B, A]
        )
        
        # Preparar dados formatados para tooltip
        map_data['velocidade_formatada'] = map_data['velocidade_km'].apply(lambda x: f"{x:.1f} km/h")
        map_data['data_formatada'] = pd.to_datetime(map_data['data'], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
        map_data['status_velocidade'] = map_data['velocidade_km'].apply(
            lambda x: "⚠️ Acima do limite" if x > speed_threshold else "✅ Velocidade normal"
        )
        
        # Adicionar endereço se disponível, senão usar região baseada nas coordenadas
        if 'endereco' in map_data.columns and not map_data['endereco'].isna().all():
            map_data['local_formatado'] = map_data['endereco'].fillna("Localização não identificada")
        else:
            # Simplificar coordenadas para tooltip mais limpo
            map_data['local_formatado'] = map_data.apply(
                lambda row: f"Lat: {row['latitude']:.4f}, Lon: {row['longitude']:.4f}", axis=1
            )
        
        # Cliente e motorista se disponível
        info_adicional = ""
        if 'cliente' in map_data.columns:
            map_data['info_cliente'] = map_data['cliente'].fillna("Cliente não informado")
        if 'motorista' in map_data.columns:
            map_data['info_motorista'] = map_data['motorista'].fillna("Motorista não informado")
        
        # Tooltip otimizado para usuários finais
        tooltip_text = {
            "html": """
            <div style='padding: 8px; max-width: 300px;'>
                <h4 style='margin: 0 0 8px 0; color: #2E86C1;'>🚛 {placa}</h4>
                <p style='margin: 2px 0;'><b>Velocidade:</b> {velocidade_formatada}</p>
                <p style='margin: 2px 0;'><b>Status:</b> {status_velocidade}</p>
                <p style='margin: 2px 0;'><b>Data/Hora:</b> {data_formatada}</p>
                <p style='margin: 2px 0;'><b>Local:</b> {local_formatado}</p>
            </div>
            """,
            "style": {
                "backgroundColor": "rgba(255, 255, 255, 0.95)", 
                "color": "#333333",
                "border": "1px solid #ccc",
                "borderRadius": "8px",
                "fontSize": "12px",
                "fontFamily": "Arial, sans-serif"
            }
        }
        
        # Configurar visualização inicial
        initial_view = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=12,
            pitch=0,
            bearing=0
        )
        
        if view_mode == "Pontos Individuais":
            # Camada de pontos (ScatterplotLayer) - Otimizada para performance
            scatter_layer = pdk.Layer(
                'ScatterplotLayer',
                data=map_data,
                get_position=['longitude', 'latitude'],
                get_color='color',
                get_radius=30,  # Radius em metros
                radius_min_pixels=2,
                radius_max_pixels=8,
                pickable=True,
                auto_highlight=True
            )
            
            layers = [scatter_layer]
            
        else:  # Densidade (Hexágonos)
            # Camada de hexágonos para datasets grandes (HexagonLayer)
            hex_layer = pdk.Layer(
                'HexagonLayer',
                data=map_data,
                get_position=['longitude', 'latitude'],
                radius=200,  # Raio do hexágono em metros
                elevation_scale=4,
                elevation_range=[0, 100],
                pickable=True,
                extruded=True,
                coverage=1
            )
            
            layers = [hex_layer]
        
        # Criar deck
        deck = pdk.Deck(
            layers=layers,
            initial_view_state=initial_view,
            tooltip=tooltip_text if view_mode == "Pontos Individuais" else None,
            map_provider='carto',  # Usar Carto (gratuito) ao invés de Mapbox
            map_style='light'
        )
        
        # Renderizar mapa
        st.pydeck_chart(deck, height=map_height)
        
    else:
        st.warning("⚠️ Não há dados de coordenadas suficientes para exibir o mapa.")
    
    # Resumo estatístico em colunas
    if not route_data.empty:
        st.subheader("📊 Estatísticas da Rota")
        col1, col2, col3, col4 = st.columns(4)
        
        total_points = len(route_data)
        speed_violations = len(route_data[route_data['velocidade_km'] > speed_threshold])
        avg_speed = route_data['velocidade_km'].mean()
        max_speed = route_data['velocidade_km'].max()
        
        with col1:
            st.metric("Total de Pontos", f"{total_points:,}")
        with col2:
            st.metric("Velocidade Média", f"{avg_speed:.1f} km/h")
        with col3:
            st.metric("Velocidade Máxima", f"{max_speed:.1f} km/h")
        with col4:
            st.metric("Picos de Velocidade", f"{speed_violations:,}", 
                     delta=f"{(speed_violations/total_points*100):.1f}% do total")
        
        # Informações sobre otimização
        if total_points > 10000:
            st.info(
                f"💡 **Dica de Performance**: Com {total_points:,} pontos, use o modo 'Densidade (Hexágonos)' "
                "para melhor performance e visualização de padrões."
            )
        
        # Legenda de cores
        st.markdown("""
        **Legenda:**
        - 🟢 **Verde**: Velocidade normal (≤ {} km/h)
        - 🔴 **Vermelho**: Pico de velocidade (> {} km/h)
        """.format(speed_threshold, speed_threshold))

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
            st.plotly_chart(fig_hist, width='stretch')
        
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
                st.plotly_chart(fig_time, width='stretch')
        
        # Tabela de picos de velocidade
        speed_violations_df = route_data[route_data['velocidade_km'] > speed_threshold]
        if not speed_violations_df.empty:
            st.subheader("⚠️ Picos de Velocidade Detectados")
            speed_violations_display = speed_violations_df[['data', 'placa', 'velocidade_km', 'latitude', 'longitude']].copy()
            speed_violations_display = speed_violations_display.sort_values('velocidade_km', ascending=False)
            st.dataframe(speed_violations_display.head(20), width='stretch')

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
            st.plotly_chart(fig_freq, width='stretch')
        
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
                st.plotly_chart(fig_hourly, width='stretch')

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
                st.plotly_chart(fig_scatter, width='stretch')

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
            st.plotly_chart(fig_daily, width='stretch')
        
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
            st.plotly_chart(fig_heatmap, width='stretch')
        
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
        st.plotly_chart(fig_period, width='stretch')
        
        # Tabela resumo
        st.subheader("📊 Resumo Estatístico por Período")
        st.dataframe(period_stats, width='stretch')

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
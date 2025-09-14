import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, time, timedelta
import pytz
from database.db_manager import DatabaseManager
from utils.data_analyzer import DataAnalyzer

def main():
    st.title("🚨 Controle Operacional")
    st.markdown("**Monitoramento de conformidade operacional das vans da prefeitura**")
    
    # Carregar dados diretamente
    df_inicial = DatabaseManager.get_dashboard_data()
    if df_inicial.empty:
        st.warning("⚠️ Não há dados carregados. Faça upload de arquivos CSV primeiro.")
        return
    else:
        st.success(f"✅ Dados carregados: {len(df_inicial):,} registros para controle operacional")
    
    # Sidebar com filtros
    with st.sidebar:
        st.header("🔍 Filtros")
        
        # Filtro de cliente
        clients = get_client_list()
        selected_client = st.selectbox(
            "Cliente:",
            ["Todos"] + clients,
            index=0
        )
        
        # Filtro de veículo
        vehicles = get_vehicle_list(selected_client if selected_client != "Todos" else None)
        selected_vehicle = st.selectbox(
            "Veículo:",
            ["Todos"] + vehicles,
            index=0
        )
        
        # Filtro de período
        st.subheader("📅 Período de Análise")
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
        
        # Filtros de horário autorizado
        st.subheader("⏰ Filtros de Horário")
        
        # Botões de preset para períodos autorizados
        st.markdown("**Períodos Autorizados:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🌅 Manhã\n04:00-07:00", key="morning"):
                st.session_state.time_filter = "morning"
        with col2:
            if st.button("🍽️ Almoço\n10:50-13:00", key="lunch"):
                st.session_state.time_filter = "lunch"
        with col3:
            if st.button("🌇 Tarde\n16:50-19:00", key="afternoon"):
                st.session_state.time_filter = "afternoon"
        
        # Filtro personalizado de horário
        time_filter_mode = st.selectbox(
            "Filtrar por período:",
            ["Todos os horários", "Apenas horários autorizados", "Apenas violações de horário", "Período personalizado"],
            index=0
        )
        
        custom_start_time = None
        custom_end_time = None
        if time_filter_mode == "Período personalizado":
            col1, col2 = st.columns(2)
            with col1:
                custom_start_time = st.time_input("Hora início:", value=time(0, 0))
            with col2:
                custom_end_time = st.time_input("Hora fim:", value=time(23, 59))
        
        # Critérios de movimento
        st.subheader("🚗 Critérios de Movimento")
        include_stationary = st.checkbox(
            "Incluir veículos parados na análise de violações",
            value=False,
            help="Quando desmarcado, apenas veículos em movimento (velocidade > 0 ou ignição ligada) serão considerados para violações"
        )
        
        # Limites de velocidade
        st.subheader("⚡ Configurações")
        speed_violation_threshold = st.slider(
            "Limite de velocidade (km/h):",
            min_value=10,
            max_value=120,
            value=80,
            step=5,
            help="Velocidades acima deste valor serão destacadas como picos"
        )
    
    # Aplicar filtros aos dados já carregados
    df = apply_filters_to_data(df_inicial, selected_client, selected_vehicle, start_date, end_date)
    
    # Aplicar filtros de horário se especificado
    if time_filter_mode != "Todos os horários" and not df.empty:
        df = apply_time_filters(df, time_filter_mode, custom_start_time, custom_end_time)
    
    if df.empty:
        st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados.")
        return
    
    # Processar dados para análise operacional
    df = process_operational_data(df, include_stationary=include_stationary)
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Resumo Operacional", 
        "⚠️ Violações Detectadas", 
        "🗺️ Mapa de Trajetos", 
        "📋 Relatório Detalhado"
    ])
    
    with tab1:
        show_operational_summary(df)
    
    with tab2:
        show_violations(df)
    
    with tab3:
        show_trajectory_map(df)
    
    with tab4:
        show_detailed_report(df)

@st.cache_data(ttl=300)
def get_client_list():
    """Busca lista de clientes com cache para melhor performance"""
    try:
        df = DatabaseManager.get_dashboard_data()
        if not df.empty and 'cliente' in df.columns:
            return sorted(df['cliente'].unique().tolist())
        return []
    except Exception as e:
        st.error(f"Erro ao carregar clientes: {str(e)}")
        return []

@st.cache_data(ttl=300)
def get_vehicle_list(client_filter=None):
    """Busca lista de veículos com cache para melhor performance"""
    try:
        df = DatabaseManager.get_dashboard_data()
        if not df.empty and 'placa' in df.columns:
            # Filtrar por cliente se especificado
            if client_filter and client_filter != "Todos":
                df = df[df['cliente'] == client_filter]
            return sorted(df['placa'].unique().tolist())
        return []
    except Exception as e:
        st.error(f"Erro ao carregar veículos: {str(e)}")
        return []

def apply_filters_to_data(df, client_filter, vehicle_filter, start_date, end_date):
    """Aplica filtros aos dados já carregados"""
    try:
        if df.empty:
            return df
            
        filtered_df = df.copy()
        
        # Filtro de cliente
        if client_filter and client_filter != "Todos":
            filtered_df = filtered_df[filtered_df['cliente'] == client_filter]
        
        # Filtro de veículo  
        if vehicle_filter and vehicle_filter != "Todos":
            filtered_df = filtered_df[filtered_df['placa'] == vehicle_filter]
        
        # Filtro de data - com tratamento robusto de timezone
        if 'data' in filtered_df.columns and not filtered_df.empty:
            try:
                # Garantir que a coluna data é datetime
                if not pd.api.types.is_datetime64_any_dtype(filtered_df['data']):
                    filtered_df['data'] = pd.to_datetime(filtered_df['data'], errors='coerce')
                
                # Criar datetimes para comparação
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                
                # Se dados têm timezone, converter filtros também
                if filtered_df['data'].dt.tz is not None:
                    start_datetime = pd.Timestamp(start_datetime).tz_localize('UTC')
                    end_datetime = pd.Timestamp(end_datetime).tz_localize('UTC')
                
                # Aplicar filtros de data
                filtered_df = filtered_df[
                    (filtered_df['data'] >= start_datetime) & 
                    (filtered_df['data'] <= end_datetime)
                ]
            except Exception as date_error:
                # Em caso de erro de datetime, não aplicar filtro de data
                st.warning(f"Aviso: Erro no filtro de data - {str(date_error)}")
                pass
        
        return filtered_df
    except Exception as e:
        st.error(f"Erro ao aplicar filtros: {str(e)}")
        return pd.DataFrame()

def load_filtered_data(client_filter, vehicle_filter, start_date, end_date):
    """Função mantida para compatibilidade - Carrega dados filtrados"""
    try:
        client_f = None if client_filter == "Todos" else client_filter
        vehicle_f = None if vehicle_filter == "Todos" else vehicle_filter
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        df = DatabaseManager.get_dashboard_data(
            client_filter=client_f,
            vehicle_filter=vehicle_f,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

def apply_time_filters(df, time_filter_mode, custom_start_time=None, custom_end_time=None):
    """Aplica filtros de horário aos dados"""
    if df.empty:
        return df
        
    df_filtered = df.copy()
    
    # Verificar se colunas necessárias existem
    if 'data' not in df_filtered.columns:
        return df_filtered
    
    # Converter para datetime se necessário
    if not pd.api.types.is_datetime64_any_dtype(df_filtered['data']):
        df_filtered['data'] = pd.to_datetime(df_filtered['data'], errors='coerce')
    
    # Filtrar por período autorizado ou violações
    if time_filter_mode == "Apenas horários autorizados":
        df_filtered = df_filtered[df_filtered['operacao_autorizada'] == True]
    elif time_filter_mode == "Apenas violações de horário":
        df_filtered = df_filtered[df_filtered['operacao_autorizada'] == False]
    elif time_filter_mode == "Período personalizado" and custom_start_time and custom_end_time:
        # Filtrar por horário personalizado
        hour_filter = (
            (df_filtered['data'].dt.time >= custom_start_time) & 
            (df_filtered['data'].dt.time <= custom_end_time)
        )
        df_filtered = df_filtered[hour_filter]
    
    return df_filtered

def safe_column_access(df, column, default_value=None, numeric=False):
    """Acesso seguro a colunas do DataFrame com valores padrão"""
    if column not in df.columns:
        if numeric:
            return pd.Series([0] * len(df), index=df.index)
        else:
            return pd.Series([default_value] * len(df), index=df.index)
    
    series = df[column]
    if numeric:
        return pd.to_numeric(series, errors='coerce').fillna(0)
    else:
        return series.fillna(default_value if default_value is not None else '')

def process_operational_data(df, include_stationary=False):
    """Processa dados para análise operacional com critérios de movimento"""
    if df.empty:
        return df
    
    df = df.copy()
    
    # Verificar e converter colunas essenciais com acesso seguro
    if 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
    else:
        # Se não há coluna de data, criar uma padrão
        df['data'] = pd.Timestamp.now()
    
    # Acessar colunas de forma segura
    df['velocidade_km'] = safe_column_access(df, 'velocidade_km', 0, numeric=True)
    df['ignicao'] = safe_column_access(df, 'ignicao', 'D')
    df['latitude'] = safe_column_access(df, 'latitude', 0, numeric=True)
    df['longitude'] = safe_column_access(df, 'longitude', 0, numeric=True)
    df['endereco'] = safe_column_access(df, 'endereco', 'Local não informado')
    df['placa'] = safe_column_access(df, 'placa', 'Placa não informada')
    
    # Extrair informações de tempo
    df['hora'] = df['data'].dt.hour
    df['minuto'] = df['data'].dt.minute
    df['dia_semana'] = df['data'].dt.dayofweek  # 0=Segunda, 6=Domingo
    df['dia_semana_nome'] = df['data'].dt.strftime('%A')
    df['data_date'] = df['data'].dt.date
    df['hora_minuto'] = df['data'].dt.time
    
    # Determinar se o veículo está em movimento
    df['em_movimento'] = (
        (df['velocidade_km'] > 0) | 
        (df['ignicao'].isin(['D', 'L', 'Dirigindo', 'Ligado']))
    )
    
    # Definir horários permitidos pela prefeitura
    df['horario_permitido'] = df.apply(is_authorized_time, axis=1)
    df['dia_util'] = df['dia_semana'] < 5  # Segunda a Sexta (0-4)
    df['operacao_autorizada'] = df['horario_permitido'] & df['dia_util']
    
    # Aplicar critério de movimento para violações (se configurado)
    if not include_stationary:
        # Apenas considerar violações quando o veículo está em movimento
        df['violacao_considerada'] = ~df['operacao_autorizada'] & df['em_movimento']
    else:
        # Considerar todas as violações, independente do movimento
        df['violacao_considerada'] = ~df['operacao_autorizada']
    
    # Classificar violações considerando movimento
    df['tipo_violacao'] = df.apply(lambda row: classify_violation(row, include_stationary), axis=1)
    
    return df

def is_authorized_time(row):
    """Verifica se o horário está dentro dos períodos autorizados"""
    hora = row['hora']
    minuto = row['minuto']
    time_current = time(hora, minuto)
    
    # Horários permitidos pela prefeitura
    morning_start = time(4, 0)   # 04:00
    morning_end = time(7, 0)     # 07:00
    
    lunch_start = time(10, 50)   # 10:50
    lunch_end = time(13, 0)      # 13:00
    
    afternoon_start = time(16, 50)  # 16:50
    afternoon_end = time(19, 0)     # 19:00
    
    # Verificar se está em algum período permitido
    is_morning = morning_start <= time_current <= morning_end
    is_lunch = lunch_start <= time_current <= lunch_end
    is_afternoon = afternoon_start <= time_current <= afternoon_end
    
    return is_morning or is_lunch or is_afternoon

def classify_violation(row, include_stationary=False):
    """Classifica o tipo de violação considerando critérios de movimento"""
    # Se a operação é autorizada, sempre é válida
    if row['operacao_autorizada']:
        return "✅ Autorizada"
    
    # Se não devemos incluir veículos parados e o veículo não está em movimento
    if not include_stationary and not row.get('em_movimento', True):
        return "🚙 Parado (Não Analisado)"
    
    # Classificar tipos de violação
    if not row['dia_util']:
        return "🚫 Final de Semana"
    elif not row['horario_permitido']:
        return "⏰ Horário Não Autorizado"
    else:
        return "❓ Outros"

def show_operational_summary(df):
    """Mostra resumo operacional"""
    st.markdown("### 📊 Resumo Operacional")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_records = len(df)
    authorized_records = len(df[df['operacao_autorizada']])
    violation_records = len(df[~df['operacao_autorizada']])
    compliance_rate = (authorized_records / total_records * 100) if total_records > 0 else 0
    
    with col1:
        st.metric(
            "📊 Total de Registros",
            f"{total_records:,}",
            help="Total de registros no período selecionado"
        )
    
    with col2:
        st.metric(
            "✅ Operações Autorizadas",
            f"{authorized_records:,}",
            delta=f"{(authorized_records/total_records*100):.1f}%" if total_records > 0 else "0%"
        )
    
    with col3:
        st.metric(
            "⚠️ Violações Detectadas",
            f"{violation_records:,}",
            delta=f"-{(violation_records/total_records*100):.1f}%" if total_records > 0 else "0%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "📈 Taxa de Conformidade",
            f"{compliance_rate:.1f}%",
            delta="Meta: 100%",
            delta_color="normal" if compliance_rate >= 95 else "inverse"
        )
    
    # Gráfico de distribuição por tipo de operação
    st.markdown("### 📈 Distribuição de Operações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza - Autorizada vs Violação
        violation_counts = df['operacao_autorizada'].value_counts()
        
        fig_pie = px.pie(
            values=violation_counts.values,
            names=['✅ Autorizadas' if x else '⚠️ Violações' for x in violation_counts.index],
            title="Proporção de Operações",
            color_discrete_map={
                '✅ Autorizadas': '#2E8B57',
                '⚠️ Violações': '#DC143C'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Gráfico de barras - Tipos de violação
        violation_types = df['tipo_violacao'].value_counts()
        
        fig_bar = px.bar(
            x=violation_types.index,
            y=violation_types.values,
            title="Tipos de Violação",
            color=violation_types.index,
            color_discrete_map={
                '✅ Autorizada': '#2E8B57',
                '🚫 Final de Semana': '#FF4500',
                '⏰ Horário Não Autorizado': '#DC143C',
                '❓ Outros': '#696969'
            }
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

def show_violations(df):
    """Mostra violações detectadas"""
    st.markdown("### ⚠️ Violações Operacionais Detectadas")
    
    # Filtrar apenas violações
    violations_df = df[~df['operacao_autorizada']].copy()
    
    if violations_df.empty:
        st.success("🎉 Nenhuma violação detectada no período selecionado!")
        return
    
    # Resumo das violações
    col1, col2, col3 = st.columns(3)
    
    weekend_violations = len(violations_df[violations_df['tipo_violacao'] == '🚫 Final de Semana'])
    time_violations = len(violations_df[violations_df['tipo_violacao'] == '⏰ Horário Não Autorizado'])
    
    with col1:
        st.metric("🚫 Final de Semana", f"{weekend_violations:,}")
    with col2:
        st.metric("⏰ Horário Irregular", f"{time_violations:,}")
    with col3:
        unique_vehicles = violations_df['placa'].nunique()
        st.metric("🚗 Veículos Envolvidos", unique_vehicles)
    
    # Análise temporal das violações
    st.markdown("#### 📅 Violações por Dia")
    
    daily_violations = violations_df.groupby(['data_date', 'tipo_violacao']).size().reset_index(name='count')
    daily_violations['data_date'] = pd.to_datetime(daily_violations['data_date'])
    
    fig_daily = px.bar(
        daily_violations,
        x='data_date',
        y='count',
        color='tipo_violacao',
        title="Violações Diárias por Tipo",
        color_discrete_map={
            '🚫 Final de Semana': '#FF4500',
            '⏰ Horário Não Autorizado': '#DC143C',
            '❓ Outros': '#696969'
        }
    )
    st.plotly_chart(fig_daily, use_container_width=True)
    
    # Tabela detalhada das violações
    st.markdown("#### 📋 Detalhes das Violações")
    
    # Preparar dados para tabela
    display_df = violations_df[[
        'data', 'placa', 'tipo_violacao', 'velocidade_km', 'endereco'
    ]].copy()
    
    display_df['data'] = display_df['data'].dt.strftime('%d/%m/%Y %H:%M:%S')
    display_df = display_df.rename(columns={
        'data': 'Data/Hora',
        'placa': 'Veículo',
        'tipo_violacao': 'Tipo de Violação',
        'velocidade_km': 'Velocidade (km/h)',
        'endereco': 'Local'
    })
    
    # Ordenar por data mais recente
    display_df = display_df.sort_values('Data/Hora', ascending=False)
    
    st.dataframe(
        display_df.head(100),  # Limitar a 100 registros para performance
        use_container_width=True,
        hide_index=True
    )
    
    if len(display_df) > 100:
        st.info(f"📋 Mostrando os 100 registros mais recentes de {len(display_df):,} violações totais.")

def show_trajectory_map(df):
    """Mostra mapa de trajetos e picos de velocidade"""
    st.markdown("### 🗺️ Mapa de Trajetos e Velocidade")
    
    # Verificar se há coordenadas
    map_df = df[(df['latitude'].notna()) & (df['longitude'].notna()) & 
                (df['latitude'] != 0) & (df['longitude'] != 0)].copy()
    
    if map_df.empty:
        st.warning("⚠️ Nenhum dado com coordenadas GPS válidas encontrado.")
        return
    
    # Filtros para o mapa
    col1, col2, col3 = st.columns(3)
    
    with col1:
        map_filter = st.selectbox(
            "Mostrar no mapa:",
            ["Todas as operações", "Apenas violações", "Apenas autorizadas"]
        )
    
    with col2:
        speed_threshold = st.number_input(
            "Pico de velocidade acima de (km/h):",
            min_value=0,
            max_value=200,
            value=80,
            step=5
        )
    
    with col3:
        if st.button("🔄 Atualizar Mapa"):
            st.rerun()
    
    # Filtrar dados do mapa
    if map_filter == "Apenas violações":
        map_df = map_df[~map_df['operacao_autorizada']]
    elif map_filter == "Apenas autorizadas":
        map_df = map_df[map_df['operacao_autorizada']]
    
    if map_df.empty:
        st.warning("⚠️ Nenhum dado para exibir no mapa com os filtros selecionados.")
        return
    
    # Identificar picos de velocidade
    map_df['pico_velocidade'] = map_df['velocidade_km'] > speed_threshold
    
    # Preparar dados para o mapa com cores por status
    map_df['cor_status'] = map_df.apply(lambda row: 
        '#FF0000' if row['pico_velocidade'] else  # Vermelho para picos de velocidade
        '#DC143C' if row['tipo_violacao'] == '⏰ Horário Não Autorizado' else  # Vermelho escuro para violações de horário
        '#FF4500' if row['tipo_violacao'] == '🚫 Final de Semana' else  # Laranja para final de semana
        '#2E8B57' if row['tipo_violacao'] == '✅ Autorizada' else  # Verde para autorizadas
        '#696969', axis=1  # Cinza para outros
    )
    
    map_df['tamanho_ponto'] = map_df['pico_velocidade'].apply(lambda x: 12 if x else 6)
    map_df['hover_info'] = map_df.apply(lambda row: 
        f"<b>{row['placa']}</b><br>" +
        f"Data: {row['data'].strftime('%d/%m/%Y %H:%M')}<br>" +
        f"Velocidade: {row['velocidade_km']:.1f} km/h<br>" +
        f"Status: {row['tipo_violacao']}<br>" +
        f"Local: {row['endereco'][:50]}...", axis=1
    )
    
    # Calcular centro do mapa
    center_lat = map_df['latitude'].mean()
    center_lon = map_df['longitude'].mean()
    
    # Criar mapa real com Mapbox e OpenStreetMap
    try:
        # Usar scatter_mapbox para mapa real
        fig_map = px.scatter_mapbox(
            map_df,
            lat='latitude',
            lon='longitude',
            color='tipo_violacao',
            size='tamanho_ponto',
            hover_data={
                'placa': True,
                'velocidade_km': ':.1f',
                'data': True,
                'endereco': True,
                'latitude': False,
                'longitude': False,
                'tamanho_ponto': False
            },
            color_discrete_map={
                '✅ Autorizada': '#2E8B57',
                '🚫 Final de Semana': '#FF4500', 
                '⏰ Horário Não Autorizado': '#DC143C',
                '🚗 Parado (Não Analisado)': '#808080',
                '❓ Outros': '#696969'
            },
            title="🗺️ Mapa Real de Trajetos e Operações",
            mapbox_style="open-street-map",  # Usar OpenStreetMap
            height=600,
            zoom=12
        )
        
        # Configurar layout do mapa
        fig_map.update_layout(
            mapbox=dict(
                center=dict(lat=center_lat, lon=center_lon),
                zoom=12
            ),
            title={
                'text': "🗺️ Mapa Real de Trajetos e Operações",
                'x': 0.5,
                'xanchor': 'center'
            },
            showlegend=True,
            height=600
        )
        
        # Adicionar linhas de trajeto por veículo
        vehicles = map_df['placa'].unique()
        colors = px.colors.qualitative.Set1
        
        for i, vehicle in enumerate(vehicles[:5]):  # Limitar a 5 veículos para performance
            vehicle_df = map_df[map_df['placa'] == vehicle].sort_values('data')
            if len(vehicle_df) > 1:  # Só adicionar linha se houver múltiplos pontos
                color = colors[i % len(colors)]
                
                # Adicionar linha de trajeto
                fig_map.add_trace(
                    go.Scattermapbox(
                        lat=vehicle_df['latitude'],
                        lon=vehicle_df['longitude'],
                        mode='lines',
                        line=dict(width=2, color=color),
                        name=f'Trajeto {vehicle}',
                        showlegend=True,
                        opacity=0.7
                    )
                )
        
        st.plotly_chart(fig_map, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar mapa: {str(e)}")
        st.info("🗺️ Usando visualização alternativa...")
        
        # Fallback: usar pydeck se mapbox falhar
        try:
            import pydeck as pdk
            
            # Configurar layer do pydeck
            layer = pdk.Layer(
                'ScatterplotLayer',
                data=map_df,
                get_position='[longitude, latitude]',
                get_color='[255, 0, 0, 160]',  # Vermelho semi-transparente
                get_radius=50,
                pickable=True
            )
            
            # Configurar viewport
            view_state = pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=12,
                pitch=0
            )
            
            # Criar deck
            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={
                    'text': 'Veículo: {placa}\nVelocidade: {velocidade_km} km/h\nStatus: {tipo_violacao}'
                }
            )
            
            st.pydeck_chart(deck)
            
        except Exception as e2:
            st.error(f"Erro ao carregar visualização alternativa: {str(e2)}")
            st.warning("⚠️ Mapa não pôde ser carregado. Verifique os dados de coordenadas.")
    
    # Estatísticas do mapa
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📍 Pontos no Mapa", f"{len(map_df):,}")
    with col2:
        st.metric("⭐ Picos de Velocidade", f"{len(map_df[map_df['pico_velocidade']]):,}")
    with col3:
        st.metric("🚗 Veículos Únicos", f"{map_df['placa'].nunique()}")
    with col4:
        avg_speed = map_df['velocidade_km'].mean()
        st.metric("⚡ Velocidade Média", f"{avg_speed:.1f} km/h")

def show_detailed_report(df):
    """Mostra relatório detalhado"""
    st.markdown("### 📋 Relatório Detalhado de Conformidade")
    
    # Relatório por veículo
    st.markdown("#### 🚗 Análise por Veículo")
    
    vehicle_summary = df.groupby('placa').agg({
        'data': 'count',
        'operacao_autorizada': ['sum', 'mean'],
        'velocidade_km': ['mean', 'max'],
        'tipo_violacao': lambda x: (x != '✅ Autorizada').sum()
    }).round(2)
    
    vehicle_summary.columns = ['Total Registros', 'Operações Autorizadas', 'Taxa Conformidade (%)', 
                              'Velocidade Média', 'Velocidade Máxima', 'Total Violações']
    vehicle_summary['Taxa Conformidade (%)'] = (vehicle_summary['Taxa Conformidade (%)'] * 100).round(1)
    
    # Colorir células baseado na conformidade
    def color_compliance(val):
        if isinstance(val, (int, float)):
            if val >= 95:
                return 'color: green'
            elif val >= 80:
                return 'color: orange'
            else:
                return 'color: red'
        return ''
    
    styled_df = vehicle_summary.style.applymap(
        color_compliance, 
        subset=['Taxa Conformidade (%)']
    )
    
    st.dataframe(styled_df, use_container_width=True)
    
    # Relatório por dia da semana
    st.markdown("#### 📅 Análise por Dia da Semana")
    
    weekday_names = {
        0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 
        4: 'Sexta', 5: 'Sábado', 6: 'Domingo'
    }
    
    df['dia_semana_nome'] = df['dia_semana'].map(weekday_names)
    
    weekday_summary = df.groupby('dia_semana_nome').agg({
        'data': 'count',
        'operacao_autorizada': ['sum', 'mean'],
        'tipo_violacao': lambda x: (x != '✅ Autorizada').sum()
    }).round(2)
    
    weekday_summary.columns = ['Total Registros', 'Operações Autorizadas', 'Taxa Conformidade', 'Total Violações']
    weekday_summary['Taxa Conformidade'] = (weekday_summary['Taxa Conformidade'] * 100).round(1)
    
    # Reordenar dias da semana
    day_order = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    weekday_summary = weekday_summary.reindex([day for day in day_order if day in weekday_summary.index])
    
    fig_weekday = px.bar(
        weekday_summary.reset_index(),
        x='dia_semana_nome',
        y='Taxa Conformidade',
        title="Taxa de Conformidade por Dia da Semana",
        color='Taxa Conformidade',
        color_continuous_scale='RdYlGn'
    )
    fig_weekday.update_layout(showlegend=False)
    st.plotly_chart(fig_weekday, use_container_width=True)
    
    # Exportar relatório
    if st.button("📄 Exportar Relatório Completo"):
        # Aqui você pode implementar exportação para PDF ou Excel
        st.success("🎉 Funcionalidade de exportação será implementada em breve!")

if __name__ == "__main__":
    main()
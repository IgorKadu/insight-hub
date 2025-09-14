import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_analyzer import DataAnalyzer
from utils.visualizations import FleetVisualizations

st.set_page_config(
    page_title="Comparação de Veículos - Insight Hub",
    page_icon="📈",
    layout="wide"
)

@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data():
    """Carrega dados APENAS da base de dados (dados reais) com otimizações"""
    try:
        # Importar DatabaseManager
        from database.db_manager import DatabaseManager
        
        # Carregar TODOS os dados por padrão conforme solicitado pelo usuário
        with st.spinner("🔄 Carregando todos os dados para comparação..."):
            df = DatabaseManager.get_dashboard_data()
            
            if not df.empty:
                st.success(f"✅ Todos os dados carregados: {len(df):,} registros")
                return df
        
        st.warning("⚠️ Nenhum dado encontrado na base de dados.")
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("📈 Comparação de Veículos")
    st.markdown("Análise comparativa detalhada entre veículos da frota")
    st.markdown("---")
    
    # Carregar dados
    df = load_data()
    
    if df.empty:
        st.warning("📁 Nenhum dado encontrado. Faça o upload de um arquivo CSV primeiro.")
        st.stop()
    
    # Inicializar analisador com dados carregados (mais eficiente)
    analyzer = DataAnalyzer(df)
    visualizer = FleetVisualizations(analyzer)
    
    # Sidebar com filtros
    st.sidebar.header("🔍 Filtros para Comparação")
    
    # Filtro por cliente
    clientes = ['Todos'] + sorted(df['cliente'].unique().tolist())
    cliente_selecionado = st.sidebar.selectbox("Cliente:", clientes)
    
    # Filtro por período
    min_date = df['data'].min().date()
    max_date = df['data'].max().date()
    
    data_range = st.sidebar.date_input(
        "Período:",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    if len(data_range) == 2:
        data_inicio, data_fim = data_range
    else:
        data_inicio = data_range[0]
        data_fim = max_date
    
    # Aplicar filtros iniciais
    filtered_df = analyzer.apply_filters(
        cliente=cliente_selecionado,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    if filtered_df.empty:
        st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados.")
        st.stop()
    
    # Seleção de veículos para comparação
    st.subheader("🚗 Seleção de Veículos para Comparação")
    
    # Mostrar estatísticas rápidas dos veículos disponíveis
    vehicle_stats = filtered_df.groupby('placa').agg({
        'velocidade_km': ['count', 'mean'],
        'odometro_periodo_km': 'sum',
        'gps': lambda x: (x.mean() * 100)
    }).round(2)
    
    vehicle_stats.columns = ['Registros', 'Vel. Média', 'KM Total', 'GPS (%)']
    vehicle_stats = vehicle_stats.sort_values('Registros', ascending=False)
    
    col_selection1, col_selection2 = st.columns([2, 1])
    
    with col_selection1:
        # Multiselect para escolher veículos
        veiculos_disponiveis = vehicle_stats.index.tolist()
        
        if len(veiculos_disponiveis) < 2:
            st.error("❌ Pelo menos 2 veículos são necessários para comparação.")
            st.stop()
        
        # Sugerir veículos com mais atividade como padrão
        default_vehicles = veiculos_disponiveis[:min(5, len(veiculos_disponiveis))]
        
        veiculos_selecionados = st.multiselect(
            "Selecione os veículos para comparar:",
            veiculos_disponiveis,
            default=default_vehicles,
            help="Selecione entre 2 e 10 veículos para comparação"
        )
        
        if len(veiculos_selecionados) < 2:
            st.warning("⚠️ Selecione pelo menos 2 veículos para comparação.")
            st.stop()
        
        if len(veiculos_selecionados) > 10:
            st.warning("⚠️ Máximo de 10 veículos permitidos para melhor visualização.")
            veiculos_selecionados = veiculos_selecionados[:10]
    
    with col_selection2:
        st.subheader("📊 Veículos Disponíveis")
        st.dataframe(
            vehicle_stats.head(10),
            width=None,
            height=300
        )
    
    # Filtrar dados para veículos selecionados
    comparison_df = filtered_df[filtered_df['placa'].isin(veiculos_selecionados)]
    analyzer.filtered_df = comparison_df
    
    # Executar comparação
    comparison_data = analyzer.compare_vehicles(veiculos_selecionados)
    
    if not comparison_data:
        st.error("❌ Não foi possível gerar dados de comparação.")
        st.stop()
    
    # Tabs para diferentes tipos de comparação
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Visão Geral",
        "⚡ Performance",
        "🛣️ Operacional",
        "📡 Qualidade",
        "📈 Gráficos Detalhados"
    ])
    
    with tab1:
        show_overview_comparison(comparison_data, comparison_df)
    
    with tab2:
        show_performance_comparison(comparison_data, comparison_df)
    
    with tab3:
        show_operational_comparison(comparison_data, comparison_df)
    
    with tab4:
        show_quality_comparison(comparison_data, comparison_df)
    
    with tab5:
        show_detailed_charts(comparison_data, comparison_df, analyzer)

def show_overview_comparison(comparison_data, df):
    """Mostra comparação geral entre veículos"""
    st.header("📊 Visão Geral Comparativa")
    
    # Converter dados para DataFrame
    comparison_df = pd.DataFrame(comparison_data).T
    comparison_df = comparison_df.round(2)
    
    # Métricas principais em colunas
    st.subheader("📈 Métricas Principais")
    
    metrics_to_show = [
        ('total_registros', 'Total de Registros'),
        ('velocidade_media', 'Velocidade Média (km/h)'),
        ('distancia_total', 'Distância Total (km)'),
        ('tempo_ativo', 'Tempo Ativo (h)'),
        ('cobertura_gps', 'Cobertura GPS (%)'),
        ('violacoes_velocidade', 'Violações de Velocidade'),
        ('bloqueios', 'Bloqueios')
    ]
    
    # Criar DataFrame para exibição
    display_data = []
    for placa, data in comparison_data.items():
        row = {'Placa': placa}
        for metric_key, metric_name in metrics_to_show:
            if metric_key in data:
                value = data[metric_key]
                if metric_key in ['velocidade_media', 'cobertura_gps']:
                    row[metric_name] = f"{value:.1f}"
                elif metric_key in ['distancia_total', 'tempo_ativo']:
                    row[metric_name] = f"{value:.1f}"
                else:
                    row[metric_name] = f"{int(value):,}"
            else:
                row[metric_name] = "N/A"
        display_data.append(row)
    
    display_df = pd.DataFrame(display_data)
    
    # Estilizar tabela com cores baseadas na performance
    def highlight_best_worst(s):
        """Destaca melhores e piores valores"""
        if s.name == 'Placa':
            return [''] * len(s)
        
        # Converter para numérico, ignorando strings
        numeric_values = []
        for val in s:
            try:
                numeric_values.append(float(val.replace(',', '')) if isinstance(val, str) and val != 'N/A' else float(val))
            except:
                numeric_values.append(0)
        
        if not numeric_values or all(v == 0 for v in numeric_values):
            return [''] * len(s)
        
        # Para violações e bloqueios, menor é melhor
        if 'Violações' in s.name or 'Bloqueios' in s.name:
            min_val = min(numeric_values)
            colors = ['background-color: #d4edda' if v == min_val and v == 0 
                     else 'background-color: #f8d7da' if v == max(numeric_values) and v > 0
                     else '' for v in numeric_values]
        else:
            # Para outras métricas, maior é melhor
            max_val = max(numeric_values)
            min_val = min(numeric_values)
            colors = ['background-color: #d4edda' if v == max_val 
                     else 'background-color: #fff3cd' if v == min_val
                     else '' for v in numeric_values]
        
        return colors
    
    styled_df = display_df.style.apply(highlight_best_worst, axis=0)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Ranking geral
    st.subheader("🏆 Ranking Geral")
    
    # Calcular score geral para cada veículo
    scores = {}
    for placa, data in comparison_data.items():
        # Normalizar métricas (0-100)
        vel_score = max(0, 100 - abs(data.get('velocidade_media', 50) - 50))  # Ideal ~50 km/h
        gps_score = data.get('cobertura_gps', 0)
        dist_score = min(100, (data.get('distancia_total', 0) / 1000) * 100)  # Normalizar por 1000km
        
        # Penalizar violações e bloqueios
        violation_penalty = min(50, data.get('violacoes_velocidade', 0) * 5)
        block_penalty = data.get('bloqueios', 0) * 20
        
        # Score final
        final_score = (vel_score * 0.2 + gps_score * 0.3 + dist_score * 0.3 + 
                      (100 - violation_penalty) * 0.1 + (100 - block_penalty) * 0.1)
        
        scores[placa] = max(0, min(100, final_score))
    
    # Ordenar por score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    col_rank1, col_rank2 = st.columns(2)
    
    with col_rank1:
        st.write("**🥇 Top Performers:**")
        for i, (placa, score) in enumerate(sorted_scores[:3]):
            medal = ["🥇", "🥈", "🥉"][i]
            st.success(f"{medal} **{placa}** - Score: {score:.1f}/100")
    
    with col_rank2:
        st.write("**⚠️ Necessitam Atenção:**")
        for placa, score in sorted_scores[-3:]:
            if score < 70:
                st.warning(f"⚠️ **{placa}** - Score: {score:.1f}/100")
            else:
                st.info(f"📊 **{placa}** - Score: {score:.1f}/100")
    
    # Gráfico de radar comparativo
    st.subheader("🎯 Comparação em Radar")
    
    # Preparar dados para gráfico de radar
    categories = ['Velocidade', 'Cobertura GPS', 'Produtividade', 'Conformidade']
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, (placa, data) in enumerate(comparison_data.items()):
        # Normalizar valores para 0-100
        vel_norm = max(0, 100 - abs(data.get('velocidade_media', 50) - 50))
        gps_norm = data.get('cobertura_gps', 0)
        prod_norm = min(100, (data.get('distancia_total', 0) / 1000) * 100)
        conf_norm = max(0, 100 - (data.get('violacoes_velocidade', 0) * 10))
        
        values = [vel_norm, gps_norm, prod_norm, conf_norm]
        
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],  # Fechar o polígono
            theta=categories + [categories[0]],
            fill='toself',
            name=placa,
            line_color=colors[i % len(colors)]
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Comparação Multidimensional de Performance",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_performance_comparison(comparison_data, df):
    """Mostra comparação de performance"""
    st.header("⚡ Comparação de Performance")
    
    # Gráficos de velocidade
    col_perf1, col_perf2 = st.columns(2)
    
    with col_perf1:
        st.subheader("📊 Velocidade Média")
        
        vel_data = {placa: data['velocidade_media'] for placa, data in comparison_data.items()}
        
        fig_vel = px.bar(
            x=list(vel_data.keys()),
            y=list(vel_data.values()),
            title='Velocidade Média por Veículo',
            labels={'x': 'Placa', 'y': 'Velocidade Média (km/h)'},
            color=list(vel_data.values()),
            color_continuous_scale='Viridis'
        )
        fig_vel.update_layout(height=400)
        st.plotly_chart(fig_vel, use_container_width=True)
    
    with col_perf2:
        st.subheader("🛣️ Distância Total")
        
        dist_data = {placa: data['distancia_total'] for placa, data in comparison_data.items()}
        
        fig_dist = px.bar(
            x=list(dist_data.keys()),
            y=list(dist_data.values()),
            title='Distância Total por Veículo',
            labels={'x': 'Placa', 'y': 'Distância Total (km)'},
            color=list(dist_data.values()),
            color_continuous_scale='Blues'
        )
        fig_dist.update_layout(height=400)
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # Análise de distribuição de velocidade por veículo
    st.subheader("📈 Distribuição de Velocidade por Veículo")
    
    fig_box = px.box(
        df,
        x='placa',
        y='velocidade_km',
        title='Distribuição de Velocidade (Box Plot)',
        labels={'placa': 'Placa', 'velocidade_km': 'Velocidade (km/h)'}
    )
    fig_box.update_layout(height=400)
    st.plotly_chart(fig_box, use_container_width=True)
    
    # Métricas de eficiência
    st.subheader("🎯 Métricas de Eficiência")
    
    efficiency_data = []
    for placa, data in comparison_data.items():
        if data['tempo_ativo'] > 0:
            km_por_hora = data['distancia_total'] / data['tempo_ativo']
        else:
            km_por_hora = 0
        
        efficiency_data.append({
            'Placa': placa,
            'KM por Hora': round(km_por_hora, 2),
            'Registros por Dia': round(data['total_registros'] / 30, 1),  # Assumindo ~30 dias
            'Utilização (%)': min(100, round((data['tempo_ativo'] / (30 * 24)) * 100, 1))
        })
    
    efficiency_df = pd.DataFrame(efficiency_data)
    efficiency_df = efficiency_df.sort_values('KM por Hora', ascending=False)
    
    st.dataframe(efficiency_df, use_container_width=True, hide_index=True)
    
    # Gráfico de eficiência
    fig_eff = px.scatter(
        efficiency_df,
        x='KM por Hora',
        y='Utilização (%)',
        text='Placa',
        title='Eficiência: KM/Hora vs Utilização',
        labels={'KM por Hora': 'Quilômetros por Hora', 'Utilização (%)': 'Utilização (%)'}
    )
    fig_eff.update_traces(textposition="top center")
    fig_eff.update_layout(height=400)
    st.plotly_chart(fig_eff, use_container_width=True)

def show_operational_comparison(comparison_data, df):
    """Mostra comparação operacional"""
    st.header("🛣️ Comparação Operacional")
    
    # Tempo ativo vs distância
    col_op1, col_op2 = st.columns(2)
    
    with col_op1:
        st.subheader("⏰ Tempo Ativo")
        
        tempo_data = {placa: data['tempo_ativo'] for placa, data in comparison_data.items()}
        
        fig_tempo = px.bar(
            x=list(tempo_data.keys()),
            y=list(tempo_data.values()),
            title='Tempo Ativo por Veículo',
            labels={'x': 'Placa', 'y': 'Tempo Ativo (horas)'},
            color=list(tempo_data.values()),
            color_continuous_scale='Oranges'
        )
        fig_tempo.update_layout(height=400)
        st.plotly_chart(fig_tempo, use_container_width=True)
    
    with col_op2:
        st.subheader("📊 Total de Registros")
        
        registros_data = {placa: data['total_registros'] for placa, data in comparison_data.items()}
        
        fig_reg = px.bar(
            x=list(registros_data.keys()),
            y=list(registros_data.values()),
            title='Total de Registros por Veículo',
            labels={'x': 'Placa', 'y': 'Total de Registros'},
            color=list(registros_data.values()),
            color_continuous_scale='Greens'
        )
        fig_reg.update_layout(height=400)
        st.plotly_chart(fig_reg, use_container_width=True)
    
    # Análise temporal de atividade
    st.subheader("⏰ Padrões de Atividade por Hora")
    
    # Atividade por hora para cada veículo
    hourly_activity = df.groupby(['placa', df['data'].dt.hour]).size().unstack(fill_value=0)
    
    # Criar heatmap
    fig_heatmap = px.imshow(
        hourly_activity,
        title='Atividade por Hora (Registros)',
        labels={'x': 'Hora do Dia', 'y': 'Placa', 'color': 'Número de Registros'},
        aspect='auto'
    )
    fig_heatmap.update_layout(height=500)
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Análise de picos de atividade
    st.subheader("📈 Análise de Picos de Atividade")
    
    peak_analysis = []
    for placa in df['placa'].unique():
        vehicle_data = df[df['placa'] == placa]
        hourly_counts = vehicle_data.groupby(vehicle_data['data'].dt.hour).size()
        
        if not hourly_counts.empty:
            peak_hour = hourly_counts.idxmax()
            peak_count = hourly_counts.max()
            avg_count = hourly_counts.mean()
            
            peak_analysis.append({
                'Placa': placa,
                'Hora de Pico': f"{peak_hour}h",
                'Registros no Pico': peak_count,
                'Média por Hora': round(avg_count, 1),
                'Intensidade do Pico': round(peak_count / avg_count, 1) if avg_count > 0 else 0
            })
    
    peak_df = pd.DataFrame(peak_analysis)
    peak_df = peak_df.sort_values('Intensidade do Pico', ascending=False)
    
    st.dataframe(peak_df, use_container_width=True, hide_index=True)

def show_quality_comparison(comparison_data, df):
    """Mostra comparação de qualidade dos dados"""
    st.header("📡 Comparação de Qualidade")
    
    # Métricas de qualidade
    col_qual1, col_qual2 = st.columns(2)
    
    with col_qual1:
        st.subheader("📡 Cobertura GPS")
        
        gps_data = {placa: data['cobertura_gps'] for placa, data in comparison_data.items()}
        
        fig_gps = px.bar(
            x=list(gps_data.keys()),
            y=list(gps_data.values()),
            title='Cobertura GPS por Veículo (%)',
            labels={'x': 'Placa', 'y': 'Cobertura GPS (%)'},
            color=list(gps_data.values()),
            color_continuous_scale='RdYlGn'
        )
        fig_gps.update_layout(height=400)
        # Adicionar linha de referência para 95%
        fig_gps.add_hline(y=95, line_dash="dash", line_color="red", 
                         annotation_text="Meta: 95%")
        st.plotly_chart(fig_gps, use_container_width=True)
    
    with col_qual2:
        st.subheader("🚨 Violações de Velocidade")
        
        violacoes_data = {placa: data['violacoes_velocidade'] for placa, data in comparison_data.items()}
        
        fig_viol = px.bar(
            x=list(violacoes_data.keys()),
            y=list(violacoes_data.values()),
            title='Violações de Velocidade por Veículo',
            labels={'x': 'Placa', 'y': 'Número de Violações'},
            color=list(violacoes_data.values()),
            color_continuous_scale='Reds'
        )
        fig_viol.update_layout(height=400)
        st.plotly_chart(fig_viol, use_container_width=True)
    
    # Score de qualidade combinado
    st.subheader("🎯 Score de Qualidade Geral")
    
    quality_scores = []
    for placa, data in comparison_data.items():
        # Calcular score de qualidade (0-100)
        gps_score = data['cobertura_gps']
        violation_penalty = min(50, data['violacoes_velocidade'] * 5)  # Máximo 50 pontos de penalidade
        block_penalty = data['bloqueios'] * 20  # 20 pontos por bloqueio
        
        final_score = max(0, gps_score - violation_penalty - block_penalty)
        
        quality_scores.append({
            'Placa': placa,
            'Cobertura GPS (%)': round(data['cobertura_gps'], 1),
            'Violações': data['violacoes_velocidade'],
            'Bloqueios': data['bloqueios'],
            'Score de Qualidade': round(final_score, 1)
        })
    
    quality_df = pd.DataFrame(quality_scores)
    quality_df = quality_df.sort_values('Score de Qualidade', ascending=False)
    
    # Colorir por score
    def color_quality_score(val):
        if val >= 90:
            return 'background-color: #d4edda'  # Verde
        elif val >= 70:
            return 'background-color: #fff3cd'  # Amarelo
        else:
            return 'background-color: #f8d7da'  # Vermelho
    
    styled_quality = quality_df.style.applymap(
        color_quality_score, 
        subset=['Score de Qualidade']
    )
    
    st.dataframe(styled_quality, use_container_width=True, hide_index=True)
    
    # Gráfico de score de qualidade
    fig_quality = px.bar(
        quality_df,
        x='Placa',
        y='Score de Qualidade',
        title='Score de Qualidade por Veículo',
        labels={'Score de Qualidade': 'Score de Qualidade (0-100)'},
        color='Score de Qualidade',
        color_continuous_scale='RdYlGn'
    )
    fig_quality.update_layout(height=400)
    # Linha de meta para 80%
    fig_quality.add_hline(y=80, line_dash="dash", line_color="orange", 
                         annotation_text="Meta: 80%")
    st.plotly_chart(fig_quality, use_container_width=True)

def show_detailed_charts(comparison_data, df, analyzer):
    """Mostra gráficos detalhados"""
    st.header("📈 Gráficos Detalhados")
    
    # Seletor de tipo de gráfico
    chart_type = st.selectbox(
        "Selecione o tipo de análise:",
        [
            "Evolução Temporal",
            "Comparação de Velocidade",
            "Análise de Correlação",
            "Dispersão Multivariada"
        ]
    )
    
    if chart_type == "Evolução Temporal":
        show_temporal_evolution(df)
    elif chart_type == "Comparação de Velocidade":
        show_speed_comparison_charts(df)
    elif chart_type == "Análise de Correlação":
        show_correlation_analysis(df)
    elif chart_type == "Dispersão Multivariada":
        show_multivariate_scatter(comparison_data)

def show_temporal_evolution(df):
    """Mostra evolução temporal dos veículos"""
    st.subheader("⏰ Evolução Temporal")
    
    # Agregar dados por dia
    daily_data = df.groupby(['placa', df['data'].dt.date]).agg({
        'velocidade_km': 'mean',
        'odometro_periodo_km': 'sum',
        'gps': lambda x: (x.mean() * 100)
    }).reset_index()
    
    # Gráfico de velocidade ao longo do tempo
    fig_temporal = px.line(
        daily_data,
        x='data',
        y='velocidade_km',
        color='placa',
        title='Evolução da Velocidade Média por Dia',
        labels={'data': 'Data', 'velocidade_km': 'Velocidade Média (km/h)'}
    )
    fig_temporal.update_layout(height=500)
    st.plotly_chart(fig_temporal, use_container_width=True)
    
    # Gráfico de quilometragem acumulada
    daily_data['km_acumulado'] = daily_data.groupby('placa')['odometro_periodo_km'].cumsum()
    
    fig_cumulative = px.line(
        daily_data,
        x='data',
        y='km_acumulado',
        color='placa',
        title='Quilometragem Acumulada por Dia',
        labels={'data': 'Data', 'km_acumulado': 'KM Acumulado'}
    )
    fig_cumulative.update_layout(height=500)
    st.plotly_chart(fig_cumulative, use_container_width=True)

def show_speed_comparison_charts(df):
    """Mostra gráficos de comparação de velocidade"""
    st.subheader("⚡ Comparação Detalhada de Velocidade")
    
    # Histograma comparativo
    fig_hist = px.histogram(
        df,
        x='velocidade_km',
        color='placa',
        nbins=30,
        title='Distribuição de Velocidade por Veículo',
        labels={'velocidade_km': 'Velocidade (km/h)', 'count': 'Frequência'},
        opacity=0.7
    )
    fig_hist.update_layout(height=500)
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Violin plot
    fig_violin = px.violin(
        df,
        x='placa',
        y='velocidade_km',
        title='Distribuição de Velocidade (Violin Plot)',
        labels={'placa': 'Placa', 'velocidade_km': 'Velocidade (km/h)'}
    )
    fig_violin.update_layout(height=500)
    st.plotly_chart(fig_violin, use_container_width=True)

def show_correlation_analysis(df):
    """Mostra análise de correlação"""
    st.subheader("🔗 Análise de Correlação")
    
    # Calcular correlações por veículo
    correlation_data = []
    
    for placa in df['placa'].unique():
        vehicle_data = df[df['placa'] == placa]
        
        if len(vehicle_data) > 10:  # Mínimo de dados para correlação
            # Adicionar variáveis temporais
            vehicle_data = vehicle_data.copy()
            vehicle_data['hora'] = vehicle_data['data'].dt.hour
            vehicle_data['dia_semana'] = vehicle_data['data'].dt.dayofweek
            
            # Correlação entre velocidade e hora
            corr_vel_hora = vehicle_data['velocidade_km'].corr(vehicle_data['hora'])
            
            # Correlação entre velocidade e GPS
            corr_vel_gps = vehicle_data['velocidade_km'].corr(vehicle_data['gps'].astype(int))
            
            correlation_data.append({
                'Placa': placa,
                'Velocidade vs Hora': round(corr_vel_hora, 3),
                'Velocidade vs GPS': round(corr_vel_gps, 3),
                'Registros': len(vehicle_data)
            })
    
    if correlation_data:
        corr_df = pd.DataFrame(correlation_data)
        st.dataframe(corr_df, use_container_width=True, hide_index=True)
        
        # Gráfico de scatter: velocidade vs hora para todos os veículos
        fig_scatter = px.scatter(
            df,
            x=df['data'].dt.hour,
            y='velocidade_km',
            color='placa',
            title='Velocidade vs Hora do Dia',
            labels={'x': 'Hora do Dia', 'velocidade_km': 'Velocidade (km/h)'},
            opacity=0.6
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)

def show_multivariate_scatter(comparison_data):
    """Mostra análise multivariada"""
    st.subheader("🎯 Análise Multivariada")
    
    # Converter para DataFrame
    multi_df = pd.DataFrame(comparison_data).T.reset_index()
    multi_df.columns = ['Placa'] + list(multi_df.columns[1:])
    
    # Scatter plot multidimensional
    x_axis = st.selectbox("Eixo X:", ['velocidade_media', 'distancia_total', 'tempo_ativo', 'cobertura_gps'])
    y_axis = st.selectbox("Eixo Y:", ['cobertura_gps', 'velocidade_media', 'distancia_total', 'tempo_ativo'])
    size_var = st.selectbox("Tamanho:", ['total_registros', 'distancia_total', 'tempo_ativo'])
    color_var = st.selectbox("Cor:", ['violacoes_velocidade', 'cobertura_gps', 'bloqueios'])
    
    fig_multi = px.scatter(
        multi_df,
        x=x_axis,
        y=y_axis,
        size=size_var,
        color=color_var,
        text='Placa',
        title=f'Análise Multivariada: {x_axis} vs {y_axis}',
        labels={
            x_axis: x_axis.replace('_', ' ').title(),
            y_axis: y_axis.replace('_', ' ').title()
        }
    )
    fig_multi.update_traces(textposition="top center")
    fig_multi.update_layout(height=600)
    st.plotly_chart(fig_multi, use_container_width=True)
    
    # Matriz de correlação
    st.subheader("📊 Matriz de Correlação")
    
    numeric_columns = ['velocidade_media', 'distancia_total', 'tempo_ativo', 
                      'cobertura_gps', 'violacoes_velocidade', 'bloqueios', 'total_registros']
    
    corr_matrix = multi_df[numeric_columns].corr()
    
    fig_corr = px.imshow(
        corr_matrix,
        title='Matriz de Correlação entre Métricas',
        labels={'color': 'Correlação'},
        color_continuous_scale='RdBu'
    )
    fig_corr.update_layout(height=500)
    st.plotly_chart(fig_corr, use_container_width=True)

if __name__ == "__main__":
    main()

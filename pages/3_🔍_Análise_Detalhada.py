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
    page_title="Análise Detalhada - Insight Hub",
    page_icon="🔍",
    layout="wide"
)

def load_data():
    """Carrega dados APENAS da base de dados (dados reais)"""
    try:
        # Importar DatabaseManager
        from database.db_manager import DatabaseManager
        
        # Carregar APENAS da base de dados - sem fallbacks fictícios
        if DatabaseManager.has_data():
            df = DatabaseManager.get_dashboard_data()
            if not df.empty:
                st.success(f"✅ Dados reais carregados: {len(df):,} registros da base de dados")
                return df
        
        # Se não há dados reais, mostrar mensagem clara
        st.warning("⚠️ Nenhum dado real encontrado na base de dados. Faça upload dos seus arquivos CSV.")
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erro ao carregar dados reais: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("🔍 Análise Detalhada da Frota")
    st.markdown("---")
    
    # Carregar dados
    df = load_data()
    
    if df.empty:
        st.warning("📁 Nenhum dado encontrado. Faça o upload de um arquivo CSV primeiro.")
        st.stop()
    
    # Inicializar analisador com dados da base de dados
    analyzer = DataAnalyzer.from_database()
    visualizer = FleetVisualizations(analyzer)
    
    # Sidebar com filtros avançados
    st.sidebar.header("🔍 Filtros Avançados")
    
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
    
    # Filtro por múltiplos veículos
    veiculos_disponiveis = []
    if cliente_selecionado != "Todos":
        veiculos_disponiveis = sorted(df[df['cliente'] == cliente_selecionado]['placa'].unique().tolist())
    else:
        veiculos_disponiveis = sorted(df['placa'].unique().tolist())
    
    veiculos_selecionados = st.sidebar.multiselect(
        "Veículos:",
        veiculos_disponiveis,
        default=veiculos_disponiveis[:5] if len(veiculos_disponiveis) > 5 else veiculos_disponiveis
    )
    
    # Filtros de velocidade
    st.sidebar.subheader("⚡ Filtros de Velocidade")
    velocidade_min = st.sidebar.number_input("Velocidade Mínima (km/h):", min_value=0, max_value=200, value=0)
    velocidade_max = st.sidebar.number_input("Velocidade Máxima (km/h):", min_value=0, max_value=200, value=200)
    
    # Aplicar filtros
    filtered_df = analyzer.apply_filters(
        cliente=cliente_selecionado,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    # Filtrar por veículos selecionados
    if veiculos_selecionados:
        filtered_df = filtered_df[filtered_df['placa'].isin(veiculos_selecionados)]
    
    # Filtrar por velocidade
    filtered_df = filtered_df[
        (filtered_df['velocidade_km'] >= velocidade_min) & 
        (filtered_df['velocidade_km'] <= velocidade_max)
    ]
    
    if filtered_df.empty:
        st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados.")
        st.stop()
    
    # Atualizar analyzer com dados filtrados
    analyzer.filtered_df = filtered_df
    
    # Tabs para diferentes análises
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Visão Geral",
        "⚡ Análise de Velocidade", 
        "🛣️ Análise Operacional",
        "📡 Compliance",
        "⏰ Padrões Temporais"
    ])
    
    with tab1:
        show_overview_analysis(analyzer)
    
    with tab2:
        show_speed_analysis(analyzer)
    
    with tab3:
        show_operational_analysis(analyzer)
    
    with tab4:
        show_compliance_analysis(analyzer)
    
    with tab5:
        show_temporal_patterns(analyzer)

def show_overview_analysis(analyzer):
    """Mostra análise geral"""
    st.header("📊 Visão Geral dos Dados Filtrados")
    
    kpis = analyzer.get_kpis()
    
    # Verificar se há KPIs válidos
    if not kpis:
        st.warning("⚠️ Não foi possível calcular métricas. Verifique se há dados para os filtros aplicados.")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🚗 Veículos", f"{kpis['total_veiculos']:,}")
    
    with col2:
        st.metric("📊 Registros", f"{kpis['total_registros']:,}")
    
    with col3:
        st.metric("⚡ Vel. Média", f"{kpis['velocidade_media']:.1f} km/h")
    
    with col4:
        st.metric("🛣️ Distância", f"{kpis['distancia_total']:.0f} km")
    
    # Gráficos de distribuição
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Atividade por Veículo")
        
        vehicle_activity = analyzer.filtered_df.groupby('placa').size().sort_values(ascending=False).head(15)
        
        fig_activity = px.bar(
            x=vehicle_activity.values,
            y=vehicle_activity.index,
            orientation='h',
            title='Top 15 Veículos por Atividade',
            labels={'x': 'Número de Registros', 'y': 'Placa'}
        )
        fig_activity.update_layout(height=500)
        st.plotly_chart(fig_activity, use_container_width=True)
    
    with col_right:
        st.subheader("🎯 Distribuição de Clientes")
        
        client_dist = analyzer.filtered_df['cliente'].value_counts()
        
        fig_clients = px.pie(
            values=client_dist.values,
            names=client_dist.index,
            title='Distribuição por Cliente'
        )
        fig_clients.update_layout(height=500)
        st.plotly_chart(fig_clients, use_container_width=True)
    
    # Estatísticas detalhadas por veículo
    st.subheader("📋 Estatísticas Detalhadas por Veículo")
    
    vehicle_stats = analyzer.filtered_df.groupby('placa').agg({
        'velocidade_km': ['count', 'mean', 'max', 'std'],
        'odometro_periodo_km': 'sum',
        'gps': lambda x: (x.sum() / len(x)) * 100,
        'bloqueado': lambda x: x.sum()
    }).round(2)
    
    # Achatar MultiIndex
    vehicle_stats.columns = [
        'Registros', 'Vel. Média', 'Vel. Máxima', 'Vel. Desvio',
        'KM Total', 'GPS (%)', 'Bloqueios'
    ]
    
    vehicle_stats = vehicle_stats.sort_values('Registros', ascending=False)
    
    # Adicionar classificação de performance
    vehicle_stats['Classificação'] = vehicle_stats.apply(
        lambda row: '🏆 Excelente' if row['GPS (%)'] > 95 and row['Vel. Média'] < 60 and row['Bloqueios'] == 0
        else '✅ Bom' if row['GPS (%)'] > 90 and row['Vel. Média'] < 70
        else '⚠️ Atenção' if row['GPS (%)'] > 80
        else '❌ Crítico', axis=1
    )
    
    st.dataframe(
        vehicle_stats,
        use_container_width=True,
        height=400
    )
    
    # Download dos dados
    csv_data = vehicle_stats.to_csv().encode('utf-8')
    st.download_button(
        label="📥 Download Estatísticas CSV",
        data=csv_data,
        file_name=f"estatisticas_veiculos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

def show_speed_analysis(analyzer):
    """Análise detalhada de velocidade"""
    st.header("⚡ Análise Detalhada de Velocidade")
    
    speed_analysis = analyzer.get_speed_analysis()
    
    if not speed_analysis:
        st.warning("Dados insuficientes para análise de velocidade.")
        return
    
    # Métricas de velocidade
    col1, col2, col3, col4 = st.columns(4)
    
    df = analyzer.filtered_df
    
    with col1:
        st.metric("⚡ Velocidade Média", f"{df['velocidade_km'].mean():.1f} km/h")
    
    with col2:
        st.metric("🏎️ Velocidade Máxima", f"{df['velocidade_km'].max():.0f} km/h")
    
    with col3:
        st.metric("🐌 Velocidade Mínima", f"{df['velocidade_km'].min():.0f} km/h")
    
    with col4:
        st.metric("📊 Desvio Padrão", f"{df['velocidade_km'].std():.1f} km/h")
    
    # Gráficos de velocidade
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Distribuição por Faixas")
        
        if 'distribuicao' in speed_analysis:
            dist_data = speed_analysis['distribuicao']
            
            fig_ranges = px.pie(
                values=dist_data.values,
                names=dist_data.index,
                title='Distribuição por Faixas de Velocidade'
            )
            st.plotly_chart(fig_ranges, use_container_width=True)
    
    with col_right:
        st.subheader("⏰ Velocidade por Hora")
        
        if 'velocidade_por_hora' in speed_analysis:
            hourly_speed = speed_analysis['velocidade_por_hora']
            
            fig_hourly = px.line(
                x=hourly_speed.index,
                y=hourly_speed.values,
                title='Velocidade Média por Hora do Dia',
                labels={'x': 'Hora', 'y': 'Velocidade Média (km/h)'}
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Top veículos por velocidade
    st.subheader("🏎️ Ranking de Velocidade por Veículo")
    
    col_speed1, col_speed2 = st.columns(2)
    
    with col_speed1:
        st.write("**Maiores Velocidades Médias:**")
        
        if 'velocidade_media_por_veiculo' in speed_analysis:
            top_speed_avg = speed_analysis['velocidade_media_por_veiculo'].head(10)
            
            fig_avg = px.bar(
                x=top_speed_avg.values,
                y=top_speed_avg.index,
                orientation='h',
                title='Top 10 - Velocidade Média',
                labels={'x': 'Velocidade Média (km/h)', 'y': 'Placa'}
            )
            st.plotly_chart(fig_avg, use_container_width=True)
    
    with col_speed2:
        st.write("**Maiores Velocidades Máximas:**")
        
        if 'velocidade_maxima_por_veiculo' in speed_analysis:
            top_speed_max = speed_analysis['velocidade_maxima_por_veiculo'].head(10)
            
            fig_max = px.bar(
                x=top_speed_max.values,
                y=top_speed_max.index,
                orientation='h',
                title='Top 10 - Velocidade Máxima',
                labels={'x': 'Velocidade Máxima (km/h)', 'y': 'Placa'},
                color=top_speed_max.values,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_max, use_container_width=True)
    
    # Análise de excesso de velocidade
    st.subheader("🚨 Análise de Excesso de Velocidade")
    
    speed_limit = st.slider("Definir Limite de Velocidade (km/h):", 40, 120, 80)
    
    violations = df[df['velocidade_km'] > speed_limit]
    
    col_viol1, col_viol2, col_viol3 = st.columns(3)
    
    with col_viol1:
        st.metric("🚨 Total de Violações", f"{len(violations):,}")
    
    with col_viol2:
        st.metric("📊 % do Total", f"{(len(violations)/len(df)*100):.1f}%")
    
    with col_viol3:
        violating_vehicles = violations['placa'].nunique()
        st.metric("🚗 Veículos Envolvidos", f"{violating_vehicles:,}")
    
    if not violations.empty:
        # Violações por veículo
        violations_by_vehicle = violations.groupby('placa').size().sort_values(ascending=False).head(10)
        
        fig_violations = px.bar(
            x=violations_by_vehicle.values,
            y=violations_by_vehicle.index,
            orientation='h',
            title=f'Top 10 - Violações acima de {speed_limit} km/h',
            labels={'x': 'Número de Violações', 'y': 'Placa'},
            color=violations_by_vehicle.values,
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_violations, use_container_width=True)

def show_operational_analysis(analyzer):
    """Análise operacional detalhada"""
    st.header("🛣️ Análise Operacional")
    
    operational = analyzer.get_operational_analysis()
    
    if not operational:
        st.warning("Dados insuficientes para análise operacional.")
        return
    
    # Estatísticas operacionais
    df = analyzer.filtered_df
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_km = df['odometro_periodo_km'].sum()
        st.metric("🛣️ Total KM", f"{total_km:.0f} km")
    
    with col2:
        if 'horimetro_periodo_horas' in df.columns:
            total_hours = df['horimetro_periodo_horas'].sum()
        else:
            total_hours = 0
        st.metric("⏰ Horas Ativas", f"{total_hours:.1f} h")
    
    with col3:
        avg_km_per_vehicle = total_km / df['placa'].nunique() if df['placa'].nunique() > 0 else 0
        st.metric("📊 KM por Veículo", f"{avg_km_per_vehicle:.1f} km")
    
    with col4:
        gps_coverage = (df['gps'].sum() / len(df)) * 100
        st.metric("📡 Cobertura GPS", f"{gps_coverage:.1f}%")
    
    # Gráficos operacionais
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Quilometragem por Veículo")
        
        km_by_vehicle = df.groupby('placa')['odometro_periodo_km'].sum().sort_values(ascending=False).head(15)
        
        fig_km = px.bar(
            x=km_by_vehicle.values,
            y=km_by_vehicle.index,
            orientation='h',
            title='Top 15 - Quilometragem Total',
            labels={'x': 'Quilometragem (km)', 'y': 'Placa'}
        )
        st.plotly_chart(fig_km, use_container_width=True)
    
    with col_right:
        st.subheader("⏰ Utilização por Hora")
        
        hourly_usage = df.groupby(df['data'].dt.hour).agg({
            'placa': 'nunique',
            'odometro_periodo_km': 'sum'
        }).reset_index()
        
        fig_hourly = px.bar(
            hourly_usage,
            x='data',
            y='placa',
            title='Veículos Ativos por Hora',
            labels={'data': 'Hora', 'placa': 'Número de Veículos'}
        )
        st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Análise de eficiência
    st.subheader("📊 Análise de Eficiência")
    
    efficiency_data = []
    for placa in df['placa'].unique():
        vehicle_data = df[df['placa'] == placa]
        
        total_records = len(vehicle_data)
        total_km = vehicle_data['odometro_periodo_km'].sum()
        avg_speed = vehicle_data['velocidade_km'].mean()
        gps_coverage = (vehicle_data['gps'].mean()) * 100
        
        # Tempo parado
        stopped_time = len(vehicle_data[vehicle_data['velocidade_km'] == 0]) / total_records * 100
        
        # Score de eficiência
        efficiency_score = (
            (avg_speed / 80 * 30) +  # Velocidade adequada (30%)
            (gps_coverage) * 0.3 +    # Cobertura GPS (30%)
            ((100 - stopped_time) * 0.2) + # Tempo ativo (20%)
            (min(total_km / 1000, 1) * 20)  # Produtividade KM (20%)
        )
        
        efficiency_data.append({
            'Placa': placa,
            'Registros': total_records,
            'Total KM': total_km,
            'Vel. Média': avg_speed,
            'GPS (%)': gps_coverage,
            'Tempo Parado (%)': stopped_time,
            'Score Eficiência': min(efficiency_score, 100)
        })
    
    efficiency_df = pd.DataFrame(efficiency_data)
    efficiency_df = efficiency_df.sort_values('Score Eficiência', ascending=False)
    
    # Colorir por score de eficiência
    def color_efficiency(val):
        if val >= 80:
            return 'background-color: #d4edda'  # Verde claro
        elif val >= 60:
            return 'background-color: #fff3cd'  # Amarelo claro
        else:
            return 'background-color: #f8d7da'  # Vermelho claro
    
    styled_df = efficiency_df.style.applymap(color_efficiency, subset=['Score Eficiência'])
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Top performers
    col_top1, col_top2 = st.columns(2)
    
    with col_top1:
        st.subheader("🏆 Mais Eficientes")
        top_efficient = efficiency_df.head(5)
        for _, row in top_efficient.iterrows():
            st.success(f"**{row['Placa']}** - Score: {row['Score Eficiência']:.1f}%")
    
    with col_top2:
        st.subheader("⚠️ Necessitam Atenção")
        low_efficient = efficiency_df.tail(5)
        for _, row in low_efficient.iterrows():
            st.warning(f"**{row['Placa']}** - Score: {row['Score Eficiência']:.1f}%")

def show_compliance_analysis(analyzer):
    """Análise de compliance"""
    st.header("📡 Análise de Compliance")
    
    compliance = analyzer.get_compliance_analysis()
    
    if not compliance:
        st.warning("Dados insuficientes para análise de compliance.")
        return
    
    # Métricas de compliance
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🚨 Violações Velocidade", f"{compliance.get('violacoes_velocidade', 0):,}")
    
    with col2:
        st.metric("📡 Problemas GPS", f"{compliance.get('veiculos_baixo_gps', 0):,}")
    
    with col3:
        st.metric("🔒 Veículos Bloqueados", f"{compliance.get('veiculos_bloqueados', 0):,}")
    
    with col4:
        if compliance.get('score_compliance'):
            avg_score = sum(compliance['score_compliance'].values()) / len(compliance['score_compliance'])
            st.metric("📊 Score Médio", f"{avg_score:.1f}%")
    
    # Gráficos de compliance
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🎯 Score de Compliance por Veículo")
        
        if compliance.get('score_compliance'):
            scores_df = pd.DataFrame(
                list(compliance['score_compliance'].items()),
                columns=['Placa', 'Score']
            ).sort_values('Score', ascending=True).tail(15)
            
            # Definir cores baseadas no score
            colors = ['#d62728' if score < 70 else '#ff7f0e' if score < 90 else '#2ca02c' 
                     for score in scores_df['Score']]
            
            fig_scores = px.bar(
                scores_df,
                x='Score',
                y='Placa',
                orientation='h',
                title='Score de Compliance (Bottom 15)',
                color=scores_df['Score'],
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_scores, use_container_width=True)
    
    with col_right:
        st.subheader("📡 Cobertura GPS por Veículo")
        
        if 'cobertura_gps_por_veiculo' in compliance:
            gps_coverage = compliance['cobertura_gps_por_veiculo'].head(15)
            
            fig_gps = px.bar(
                x=gps_coverage.values,
                y=gps_coverage.index,
                orientation='h',
                title='Cobertura GPS (Bottom 15)',
                color=gps_coverage.values,
                color_continuous_scale='RdYlGn',
                labels={'x': 'Cobertura GPS (%)', 'y': 'Placa'}
            )
            st.plotly_chart(fig_gps, use_container_width=True)
    
    # Detalhes de violações
    if 'detalhes_violacoes' in compliance and not compliance['detalhes_violacoes'].empty:
        st.subheader("🚨 Detalhes das Violações de Velocidade")
        
        violations_detail = compliance['detalhes_violacoes'].head(15).reset_index()
        violations_detail.columns = ['Placa', 'Número de Violações']
        
        fig_violations = px.bar(
            violations_detail,
            x='Número de Violações',
            y='Placa',
            orientation='h',
            title='Top 15 - Violações de Velocidade',
            color='Número de Violações',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_violations, use_container_width=True)
    
    # Recomendações de compliance
    st.subheader("💡 Recomendações de Melhoria")
    
    recommendations = []
    
    if compliance.get('violacoes_velocidade', 0) > 0:
        recommendations.append("🚨 **Controle de Velocidade**: Implementar treinamento de condutores sobre limites de velocidade")
    
    if compliance.get('veiculos_baixo_gps', 0) > 0:
        recommendations.append("📡 **Melhoria GPS**: Verificar equipamentos e cobertura de sinal GPS")
    
    if compliance.get('veiculos_bloqueados', 0) > 0:
        recommendations.append("🔒 **Revisão de Bloqueios**: Analisar motivos de bloqueio e normalizar situação")
    
    if compliance.get('score_compliance'):
        low_score_vehicles = [k for k, v in compliance['score_compliance'].items() if v < 70]
        if low_score_vehicles:
            recommendations.append(f"⚠️ **Atenção Especial**: {len(low_score_vehicles)} veículos com score baixo precisam de ação imediata")
    
    if recommendations:
        for rec in recommendations:
            st.info(rec)
    else:
        st.success("✅ **Excelente!** A frota está em conformidade com os padrões estabelecidos.")

def show_temporal_patterns(analyzer):
    """Análise de padrões temporais"""
    st.header("⏰ Padrões Temporais de Uso")
    
    patterns = analyzer.get_temporal_patterns()
    df = analyzer.filtered_df
    
    if not patterns or df.empty:
        st.warning("Dados insuficientes para análise temporal.")
        return
    
    # Padrões por hora do dia
    st.subheader("🕐 Padrões por Hora do Dia")
    
    hourly_data = df.groupby(df['data'].dt.hour).agg({
        'placa': 'nunique',
        'velocidade_km': 'mean',
        'odometro_periodo_km': 'sum'
    }).reset_index()
    
    col_hour1, col_hour2 = st.columns(2)
    
    with col_hour1:
        fig_hourly_vehicles = px.line(
            hourly_data,
            x='data',
            y='placa',
            title='Veículos Ativos por Hora',
            labels={'data': 'Hora', 'placa': 'Número de Veículos'}
        )
        st.plotly_chart(fig_hourly_vehicles, use_container_width=True)
    
    with col_hour2:
        fig_hourly_speed = px.line(
            hourly_data,
            x='data',
            y='velocidade_km',
            title='Velocidade Média por Hora',
            labels={'data': 'Hora', 'velocidade_km': 'Velocidade (km/h)'}
        )
        st.plotly_chart(fig_hourly_speed, use_container_width=True)
    
    # Padrões por dia da semana
    # Definir mapeamento de dias para português (usado em múltiplos lugares)
    dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    
    if len(df['data'].dt.date.unique()) > 7:  # Mais de uma semana de dados
        st.subheader("📅 Padrões por Dia da Semana")
        
        df['dia_semana'] = df['data'].dt.day_name()
        
        weekly_data = df.groupby('dia_semana').agg({
            'placa': 'nunique',
            'velocidade_km': 'mean',
            'odometro_periodo_km': 'sum'
        }).reindex(dias_ordem).reset_index()
        
        weekly_data['dia_semana'] = dias_pt
        
        col_week1, col_week2 = st.columns(2)
        
        with col_week1:
            fig_weekly_vehicles = px.bar(
                weekly_data,
                x='dia_semana',
                y='placa',
                title='Veículos Ativos por Dia da Semana',
                labels={'dia_semana': 'Dia da Semana', 'placa': 'Número de Veículos'}
            )
            st.plotly_chart(fig_weekly_vehicles, use_container_width=True)
        
        with col_week2:
            fig_weekly_km = px.bar(
                weekly_data,
                x='dia_semana',
                y='odometro_periodo_km',
                title='Quilometragem por Dia da Semana',
                labels={'dia_semana': 'Dia da Semana', 'odometro_periodo_km': 'KM Total'}
            )
            st.plotly_chart(fig_weekly_km, use_container_width=True)
    
    # Heatmap de atividade
    st.subheader("🔥 Mapa de Calor - Atividade por Hora e Dia")
    
    # Criar dados para heatmap
    df['hora'] = df['data'].dt.hour
    df['dia'] = df['data'].dt.day_name()
    
    heatmap_data = df.groupby(['dia', 'hora']).size().unstack(fill_value=0)
    
    # Reordenar dias da semana
    dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(dias_ordem)
    heatmap_data.index = dias_pt
    
    fig_heatmap = px.imshow(
        heatmap_data,
        title='Atividade da Frota (Registros por Hora/Dia)',
        labels={'x': 'Hora do Dia', 'y': 'Dia da Semana', 'color': 'Número de Registros'},
        aspect='auto'
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Insights temporais
    st.subheader("💡 Insights Temporais")
    
    # Pico de atividade
    peak_hour = hourly_data.loc[hourly_data['placa'].idxmax(), 'data']
    peak_vehicles = hourly_data['placa'].max()
    
    st.info(f"🕐 **Pico de Atividade**: {peak_hour}h com {peak_vehicles} veículos ativos")
    
    # Período de menor atividade
    low_hour = hourly_data.loc[hourly_data['placa'].idxmin(), 'data']
    low_vehicles = hourly_data['placa'].min()
    
    st.info(f"😴 **Menor Atividade**: {low_hour}h com {low_vehicles} veículos ativos")
    
    # Horário de maior velocidade média
    fastest_hour = hourly_data.loc[hourly_data['velocidade_km'].idxmax(), 'data']
    fastest_speed = hourly_data['velocidade_km'].max()
    
    st.info(f"🏎️ **Maior Velocidade Média**: {fastest_hour}h com {fastest_speed:.1f} km/h")

if __name__ == "__main__":
    main()

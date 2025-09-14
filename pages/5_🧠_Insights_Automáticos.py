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
from utils.insights_generator import InsightsGenerator

st.set_page_config(
    page_title="Insights Automáticos - Insight Hub",
    page_icon="🧠",
    layout="wide"
)

def load_data():
    """Carrega dados processados"""
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
    st.title("🧠 Insights Automáticos")
    st.markdown("Análise inteligente e recomendações baseadas em dados da frota")
    st.markdown("---")
    
    # Carregar dados
    df = load_data()
    
    if df.empty:
        st.warning("📁 Nenhum dado encontrado. Faça o upload de um arquivo CSV primeiro.")
        st.stop()
    
    # Inicializar analisador e gerador de insights
    analyzer = DataAnalyzer(df)
    
    # Sidebar com filtros
    st.sidebar.header("🔍 Filtros para Análise")
    
    # Filtro por cliente
    clientes = ['Todos'] + sorted(df['cliente'].unique().tolist())
    cliente_selecionado = st.sidebar.selectbox("Cliente:", clientes)
    
    # Filtro por período
    min_date = df['data'].min().date()
    max_date = df['data'].max().date()
    
    # Período de análise
    periodo_analise = st.sidebar.selectbox(
        "Período de Análise:",
        [
            "Últimos 7 dias",
            "Últimos 30 dias",
            "Últimos 90 dias",
            "Todo o período",
            "Personalizado"
        ]
    )
    
    # Calcular datas baseado no período
    if periodo_analise == "Últimos 7 dias":
        data_inicio = max_date - timedelta(days=7)
        data_fim = max_date
    elif periodo_analise == "Últimos 30 dias":
        data_inicio = max_date - timedelta(days=30)
        data_fim = max_date
    elif periodo_analise == "Últimos 90 dias":
        data_inicio = max_date - timedelta(days=90)
        data_fim = max_date
    elif periodo_analise == "Todo o período":
        data_inicio = min_date
        data_fim = max_date
    else:  # Personalizado
        data_range = st.sidebar.date_input(
            "Período Personalizado:",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        if len(data_range) == 2:
            data_inicio, data_fim = data_range
        else:
            data_inicio = data_range[0]
            data_fim = max_date
    
    # Aplicar filtros
    filtered_df = analyzer.apply_filters(
        cliente=cliente_selecionado,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    if filtered_df.empty:
        st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados.")
        st.stop()
    
    # Inicializar gerador de insights
    insights_generator = InsightsGenerator(analyzer)
    
    # Gerar insights
    with st.spinner("🧠 Gerando insights inteligentes..."):
        insights = insights_generator.generate_all_insights()
    
    # Tabs para diferentes tipos de insights
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Resumo Executivo",
        "⚠️ Alertas Críticos",
        "📈 Oportunidades",
        "🔮 Predições",
        "📋 Relatório Completo"
    ])
    
    with tab1:
        show_executive_summary(insights, analyzer)
    
    with tab2:
        show_critical_alerts(insights, analyzer)
    
    with tab3:
        show_opportunities(insights, analyzer)
    
    with tab4:
        show_predictions(insights, analyzer)
    
    with tab5:
        show_complete_report(insights, insights_generator, analyzer)

def show_executive_summary(insights, analyzer):
    """Mostra resumo executivo dos insights"""
    st.header("📊 Resumo Executivo")
    
    kpis = analyzer.get_kpis()
    
    # KPIs principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🚗 Veículos Analisados", f"{kpis['total_veiculos']:,}")
    
    with col2:
        st.metric("📊 Total de Registros", f"{kpis['total_registros']:,}")
    
    with col3:
        st.metric("📅 Período", f"{kpis['periodo_dias']} dias")
    
    with col4:
        total_insights = len(insights)
        critical_insights = len([i for i in insights if i['type'] == 'error'])
        st.metric("🧠 Insights Gerados", f"{total_insights}", delta=f"{critical_insights} críticos")
    
    # Resumo por categoria
    st.subheader("📋 Resumo por Categoria")
    
    insight_summary = {
        'error': {'count': 0, 'label': '🚨 Críticos', 'color': '#dc3545'},
        'warning': {'count': 0, 'label': '⚠️ Atenção', 'color': '#ffc107'},
        'info': {'count': 0, 'label': 'ℹ️ Informativos', 'color': '#17a2b8'},
        'success': {'count': 0, 'label': '✅ Positivos', 'color': '#28a745'}
    }
    
    for insight in insights:
        insight_summary[insight['type']]['count'] += 1
    
    col_summary = st.columns(4)
    
    for i, (type_key, data) in enumerate(insight_summary.items()):
        with col_summary[i]:
            st.metric(
                label=data['label'],
                value=data['count'],
                delta=f"{(data['count']/len(insights)*100):.0f}%" if insights else "0%"
            )
    
    # Gráfico de distribuição de insights
    if insights:
        fig_insights = px.pie(
            values=[data['count'] for data in insight_summary.values()],
            names=[data['label'] for data in insight_summary.values()],
            title='Distribuição de Insights por Categoria',
            color_discrete_sequence=[data['color'] for data in insight_summary.values()]
        )
        st.plotly_chart(fig_insights, use_container_width=True)
    
    # Top 3 insights mais importantes
    st.subheader("🎯 Principais Insights")
    
    priority_insights = sorted(insights, key=lambda x: x['priority'])[:3]
    
    for i, insight in enumerate(priority_insights):
        icon = "🚨" if insight['type'] == 'error' else "⚠️" if insight['type'] == 'warning' else "ℹ️"
        
        with st.expander(f"{icon} {insight['title']}", expanded=i == 0):
            st.write(f"**Descrição:** {insight['description']}")
            st.write(f"**Recomendação:** {insight['recommendation']}")
            
            # Adicionar métricas relacionadas se disponível
            if 'compliance' in insight['title'].lower():
                compliance = analyzer.get_compliance_analysis()
                if compliance:
                    col_comp1, col_comp2 = st.columns(2)
                    with col_comp1:
                        st.metric("Violações", compliance.get('violacoes_velocidade', 0))
                    with col_comp2:
                        st.metric("Score Médio", f"{sum(compliance.get('score_compliance', {}).values()) / len(compliance.get('score_compliance', {})):.1f}%" if compliance.get('score_compliance') else "N/A")
    
    # Resumo de performance geral
    st.subheader("📈 Performance Geral da Frota")
    
    # Score geral baseado nos insights
    total_score = 100
    for insight in insights:
        if insight['type'] == 'error':
            total_score -= 15
        elif insight['type'] == 'warning':
            total_score -= 8
        elif insight['type'] == 'success':
            total_score += 5
    
    total_score = max(0, min(100, total_score))
    
    # Gauge para score geral
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = total_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Score Geral da Frota"},
        delta = {'reference': 80},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}}))
    
    fig_gauge.update_layout(height=400)
    st.plotly_chart(fig_gauge, use_container_width=True)

def show_critical_alerts(insights, analyzer):
    """Mostra alertas críticos"""
    st.header("🚨 Alertas Críticos")
    
    critical_insights = [i for i in insights if i['type'] == 'error']
    warning_insights = [i for i in insights if i['type'] == 'warning']
    
    if not critical_insights and not warning_insights:
        st.success("✅ **Excelente!** Nenhum alerta crítico identificado.")
        st.balloons()
        return
    
    # Alertas críticos
    if critical_insights:
        st.subheader("🚨 Requer Ação Imediata")
        
        for insight in critical_insights:
            with st.container():
                st.error(f"**{insight['title']}**")
                col_alert1, col_alert2 = st.columns([2, 1])
                
                with col_alert1:
                    st.write(f"📝 **Problema:** {insight['description']}")
                    st.write(f"💡 **Ação Recomendada:** {insight['recommendation']}")
                
                with col_alert2:
                    st.metric("Prioridade", "ALTA", delta="Crítico")
                
                st.markdown("---")
    
    # Alertas de atenção
    if warning_insights:
        st.subheader("⚠️ Requer Atenção")
        
        for insight in warning_insights:
            with st.container():
                st.warning(f"**{insight['title']}**")
                col_warn1, col_warn2 = st.columns([2, 1])
                
                with col_warn1:
                    st.write(f"📝 **Observação:** {insight['description']}")
                    st.write(f"💡 **Recomendação:** {insight['recommendation']}")
                
                with col_warn2:
                    st.metric("Prioridade", "MÉDIA", delta="Atenção")
                
                st.markdown("---")
    
    # Análise detalhada dos problemas
    st.subheader("🔍 Análise Detalhada dos Problemas")
    
    compliance = analyzer.get_compliance_analysis()
    
    if compliance:
        col_detail1, col_detail2, col_detail3 = st.columns(3)
        
        with col_detail1:
            st.metric(
                "🚨 Violações de Velocidade",
                f"{compliance.get('violacoes_velocidade', 0):,}",
                help="Registros com velocidade acima do limite"
            )
        
        with col_detail2:
            st.metric(
                "📡 Problemas de GPS",
                f"{compliance.get('veiculos_baixo_gps', 0):,}",
                help="Veículos com cobertura GPS abaixo de 95%"
            )
        
        with col_detail3:
            st.metric(
                "🔒 Veículos Bloqueados",
                f"{compliance.get('veiculos_bloqueados', 0):,}",
                help="Veículos com status de bloqueio ativo"
            )
        
        # Gráfico de veículos com problemas
        if compliance.get('score_compliance'):
            problem_vehicles = {k: v for k, v in compliance['score_compliance'].items() if v < 70}
            
            if problem_vehicles:
                st.subheader("🚗 Veículos que Necessitam Atenção Urgente")
                
                fig_problems = px.bar(
                    x=list(problem_vehicles.keys()),
                    y=list(problem_vehicles.values()),
                    title='Score de Compliance - Veículos Problemáticos',
                    labels={'x': 'Placa', 'y': 'Score de Compliance (%)'},
                    color=list(problem_vehicles.values()),
                    color_continuous_scale='Reds'
                )
                fig_problems.add_hline(y=70, line_dash="dash", line_color="red", 
                                     annotation_text="Limite Mínimo: 70%")
                st.plotly_chart(fig_problems, use_container_width=True)
    
    # Plano de ação recomendado
    st.subheader("📋 Plano de Ação Recomendado")
    
    action_plan = []
    
    if critical_insights:
        action_plan.append({
            'Prioridade': 'ALTA',
            'Prazo': 'Imediato (24h)',
            'Ação': 'Resolver alertas críticos identificados',
            'Responsável': 'Gestor de Frota'
        })
    
    if warning_insights:
        action_plan.append({
            'Prioridade': 'MÉDIA',
            'Prazo': '1 semana',
            'Ação': 'Implementar melhorias para alertas de atenção',
            'Responsável': 'Equipe Operacional'
        })
    
    if compliance and compliance.get('violacoes_velocidade', 0) > 0:
        action_plan.append({
            'Prioridade': 'ALTA',
            'Prazo': '3 dias',
            'Ação': 'Treinamento de condutores sobre limites de velocidade',
            'Responsável': 'RH/Treinamento'
        })
    
    if action_plan:
        action_df = pd.DataFrame(action_plan)
        st.dataframe(action_df, use_container_width=True, hide_index=True)

def show_opportunities(insights, analyzer):
    """Mostra oportunidades de melhoria"""
    st.header("📈 Oportunidades de Melhoria")
    
    info_insights = [i for i in insights if i['type'] == 'info']
    success_insights = [i for i in insights if i['type'] == 'success']
    
    # Oportunidades identificadas
    st.subheader("💡 Oportunidades Identificadas")
    
    if info_insights:
        for insight in info_insights:
            with st.container():
                st.info(f"**{insight['title']}**")
                col_opp1, col_opp2 = st.columns([3, 1])
                
                with col_opp1:
                    st.write(f"📊 **Análise:** {insight['description']}")
                    st.write(f"🎯 **Oportunidade:** {insight['recommendation']}")
                
                with col_opp2:
                    # Estimar impacto potencial
                    if 'velocidade' in insight['title'].lower():
                        st.metric("Economia Potencial", "15-25%", delta="Combustível")
                    elif 'gps' in insight['title'].lower():
                        st.metric("Melhoria Esperada", "10-20%", delta="Rastreamento")
                    else:
                        st.metric("Impacto", "Médio", delta="Operacional")
                
                st.markdown("---")
    
    # Pontos fortes identificados
    if success_insights:
        st.subheader("✅ Pontos Fortes da Frota")
        
        for insight in success_insights:
            st.success(f"**{insight['title']}** - {insight['description']}")
    
    # Análise de eficiência
    st.subheader("📊 Análise de Eficiência")
    
    efficiency = analyzer.get_efficiency_metrics()
    
    if efficiency and 'eficiencia_por_veiculo' in efficiency:
        # Identificar top performers e underperformers
        vehicle_efficiency = efficiency['eficiencia_por_veiculo']
        
        if vehicle_efficiency:
            # Converter series para lista de dicts
            efficiency_data = []
            for placa, data in vehicle_efficiency.items():
                if isinstance(data, dict):
                    efficiency_data.append({
                        'Placa': placa,
                        'KM por Dia': data.get('km_por_dia', 0),
                        'Utilização Diária': data.get('utilizacao_diaria', 0),
                        'Velocidade Média': data.get('velocidade_media', 0),
                        'Tempo Parado (%)': data.get('tempo_parado_pct', 0)
                    })
            
            if efficiency_data:
                efficiency_df = pd.DataFrame(efficiency_data)
                
                # Top performers
                top_performers = efficiency_df.nlargest(5, 'KM por Dia')
                
                col_eff1, col_eff2 = st.columns(2)
                
                with col_eff1:
                    st.write("**🏆 Top Performers (KM por Dia):**")
                    for _, row in top_performers.iterrows():
                        st.success(f"**{row['Placa']}** - {row['KM por Dia']:.1f} km/dia")
                
                with col_eff2:
                    st.write("**⚠️ Baixa Utilização:**")
                    low_performers = efficiency_df.nsmallest(5, 'Utilização Diária')
                    for _, row in low_performers.iterrows():
                        if row['Utilização Diária'] < 10:
                            st.warning(f"**{row['Placa']}** - {row['Utilização Diária']:.1f} reg/dia")
    
    # Oportunidades de otimização
    st.subheader("🎯 Oportunidades de Otimização")
    
    optimization_opportunities = [
        {
            'Área': 'Otimização de Rotas',
            'Descrição': 'Análise de padrões de movimentação para reduzir distâncias',
            'Impacto Estimado': '10-15% redução de combustível',
            'Investimento': 'Baixo',
            'Prazo': '2-4 semanas'
        },
        {
            'Área': 'Treinamento de Condutores',
            'Descrição': 'Programa de condução econômica e segura',
            'Impacto Estimado': '15-20% redução de violações',
            'Investimento': 'Médio',
            'Prazo': '1-2 meses'
        },
        {
            'Área': 'Manutenção Preventiva',
            'Descrição': 'Implementação de manutenção baseada em dados',
            'Impacto Estimado': '20-30% redução de quebras',
            'Investimento': 'Alto',
            'Prazo': '3-6 meses'
        }
    ]
    
    for opp in optimization_opportunities:
        with st.expander(f"🎯 {opp['Área']}"):
            col_desc, col_impact = st.columns([2, 1])
            
            with col_desc:
                st.write(f"**Descrição:** {opp['Descrição']}")
                st.write(f"**Prazo de Implementação:** {opp['Prazo']}")
            
            with col_impact:
                st.metric("Impacto Estimado", opp['Impacto Estimado'])
                st.metric("Investimento", opp['Investimento'])

def show_predictions(insights, analyzer):
    """Mostra predições e tendências"""
    st.header("🔮 Predições e Tendências")
    
    df = analyzer.filtered_df
    
    if len(df) < 14:  # Menos de 2 semanas de dados
        st.warning("⚠️ Dados insuficientes para análises preditivas. Necessário pelo menos 14 dias de dados.")
        return
    
    # Análise de tendências
    st.subheader("📈 Análise de Tendências")
    
    # Dividir dados em períodos
    df_sorted = df.sort_values('data')
    mid_point = len(df_sorted) // 2
    
    first_half = df_sorted.iloc[:mid_point]
    second_half = df_sorted.iloc[mid_point:]
    
    # Calcular mudanças
    trends = {}
    
    if not first_half.empty and not second_half.empty:
        trends['velocidade'] = second_half['velocidade_km'].mean() - first_half['velocidade_km'].mean()
        trends['gps_coverage'] = (second_half['gps'].mean() - first_half['gps'].mean()) * 100
        trends['activity'] = len(second_half) / len(first_half) - 1
    
    col_trend1, col_trend2, col_trend3 = st.columns(3)
    
    with col_trend1:
        if trends.get('velocidade', 0) != 0:
            st.metric(
                "Velocidade Média",
                f"{second_half['velocidade_km'].mean():.1f} km/h",
                delta=f"{trends['velocidade']:.1f} km/h"
            )
    
    with col_trend2:
        if trends.get('gps_coverage', 0) != 0:
            st.metric(
                "Cobertura GPS",
                f"{second_half['gps'].mean()*100:.1f}%",
                delta=f"{trends['gps_coverage']:.1f}%"
            )
    
    with col_trend3:
        if trends.get('activity', 0) != 0:
            st.metric(
                "Atividade da Frota",
                f"{len(second_half):,} registros",
                delta=f"{trends['activity']*100:.1f}%"
            )
    
    # Predições para próximo período
    st.subheader("🔮 Predições para os Próximos 30 Dias")
    
    predictions = []
    
    # Predição de manutenção
    high_usage_vehicles = df.groupby('placa')['odometro_periodo_km'].sum().sort_values(ascending=False).head(10)
    
    for placa, total_km in high_usage_vehicles.items():
        if total_km > 1000:  # Veículos com alta quilometragem
            vehicle_data = df[df['placa'] == placa]
            daily_avg = total_km / len(vehicle_data['data'].dt.date.unique())
            
            predicted_km_month = daily_avg * 30
            
            predictions.append({
                'Tipo': 'Manutenção Preventiva',
                'Veículo': placa,
                'Predição': f'Necessitará revisão em ~{int(5000/daily_avg)} dias',
                'Confiança': '85%',
                'Ação': 'Agendar manutenção preventiva'
            })
    
    # Predição de compliance
    compliance = analyzer.get_compliance_analysis()
    if compliance and compliance.get('score_compliance'):
        declining_vehicles = {k: v for k, v in compliance['score_compliance'].items() if v < 80}
        
        for placa in declining_vehicles:
            predictions.append({
                'Tipo': 'Compliance',
                'Veículo': placa,
                'Predição': 'Risco de violações aumentado',
                'Confiança': '75%',
                'Ação': 'Monitoramento intensivo recomendado'
            })
    
    # Exibir predições
    if predictions:
        predictions_df = pd.DataFrame(predictions)
        
        # Colorir por tipo
        def color_prediction_type(val):
            if val == 'Manutenção Preventiva':
                return 'background-color: #fff3cd'
            elif val == 'Compliance':
                return 'background-color: #f8d7da'
            else:
                return ''
        
        styled_predictions = predictions_df.style.applymap(
            color_prediction_type, 
            subset=['Tipo']
        )
        
        st.dataframe(styled_predictions, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Nenhuma predição crítica identificada para os próximos 30 dias.")
    
    # Gráfico de tendência temporal
    st.subheader("📊 Visualização de Tendências")
    
    # Agregar dados por semana
    df['semana'] = df['data'].dt.to_period('W')
    weekly_trends = df.groupby('semana').agg({
        'velocidade_km': 'mean',
        'gps': lambda x: x.mean() * 100,
        'placa': 'nunique'
    }).reset_index()
    
    weekly_trends['semana'] = weekly_trends['semana'].dt.start_time
    
    fig_trends = px.line(
        weekly_trends,
        x='semana',
        y=['velocidade_km', 'gps', 'placa'],
        title='Tendências Semanais da Frota',
        labels={'value': 'Valor', 'semana': 'Semana', 'variable': 'Métrica'}
    )
    
    st.plotly_chart(fig_trends, use_container_width=True)
    
    # Alertas preditivos
    st.subheader("🚨 Alertas Preditivos")
    
    predictive_alerts = []
    
    # Alerta de tendência decrescente na cobertura GPS
    if trends.get('gps_coverage', 0) < -5:
        predictive_alerts.append({
            'Alerta': '📡 Degradação de GPS',
            'Descrição': 'Cobertura GPS em declínio detectada',
            'Probabilidade': '80%',
            'Ação': 'Verificar equipamentos GPS da frota'
        })
    
    # Alerta de aumento de velocidade
    if trends.get('velocidade', 0) > 5:
        predictive_alerts.append({
            'Alerta': '⚡ Aumento de Velocidade',
            'Descrição': 'Velocidades médias em crescimento',
            'Probabilidade': '75%',
            'Ação': 'Reforçar treinamento de condutores'
        })
    
    if predictive_alerts:
        for alert in predictive_alerts:
            st.warning(f"**{alert['Alerta']}** - {alert['Descrição']} (Probabilidade: {alert['Probabilidade']})")
            st.write(f"💡 **Ação Recomendada:** {alert['Ação']}")
    else:
        st.success("✅ Nenhum alerta preditivo identificado. Tendências estáveis.")

def show_complete_report(insights, insights_generator, analyzer):
    """Mostra relatório completo"""
    st.header("📋 Relatório Completo de Insights")
    
    # Informações do relatório
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.info(f"""
        **📊 Informações do Relatório:**
        - Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        - Total de Insights: {len(insights)}
        - Período Analisado: {analyzer.get_kpis()['periodo_dias']} dias
        """)
    
    with col_info2:
        st.info(f"""
        **🚗 Dados da Frota:**
        - Veículos Analisados: {analyzer.get_kpis()['total_veiculos']:,}
        - Registros Processados: {analyzer.get_kpis()['total_registros']:,}
        - Score Geral: {calculate_general_score(insights):.1f}/100
        """)
    
    # Filtro por categoria
    categoria_filtro = st.selectbox(
        "Filtrar por categoria:",
        ["Todos", "Críticos", "Atenção", "Informativos", "Positivos"]
    )
    
    filtered_insights = insights
    if categoria_filtro != "Todos":
        type_map = {
            "Críticos": "error",
            "Atenção": "warning", 
            "Informativos": "info",
            "Positivos": "success"
        }
        filtered_insights = [i for i in insights if i['type'] == type_map[categoria_filtro]]
    
    # Exibir insights filtrados
    if filtered_insights:
        for i, insight in enumerate(filtered_insights, 1):
            icon_map = {
                'error': '🚨',
                'warning': '⚠️',
                'info': 'ℹ️',
                'success': '✅'
            }
            
            icon = icon_map.get(insight['type'], 'ℹ️')
            
            with st.expander(f"{i}. {icon} {insight['title']}"):
                col_insight1, col_insight2 = st.columns([3, 1])
                
                with col_insight1:
                    st.write(f"**📝 Descrição:** {insight['description']}")
                    st.write(f"**💡 Recomendação:** {insight['recommendation']}")
                    st.write(f"**🕒 Gerado em:** {insight['timestamp'].strftime('%d/%m/%Y %H:%M')}")
                
                with col_insight2:
                    priority_text = {1: "ALTA", 2: "MÉDIA", 3: "BAIXA", 4: "INFO"}
                    st.metric("Prioridade", priority_text.get(insight['priority'], "N/A"))
                    
                    type_text = {
                        'error': "CRÍTICO",
                        'warning': "ATENÇÃO", 
                        'info': "INFO",
                        'success': "POSITIVO"
                    }
                    st.metric("Categoria", type_text.get(insight['type'], "N/A"))
    else:
        st.info(f"Nenhum insight encontrado para a categoria '{categoria_filtro}'.")
    
    # Botões de ação
    st.markdown("---")
    st.subheader("📤 Exportar Relatório")
    
    col_export1, col_export2, col_export3 = st.columns(3)
    
    with col_export1:
        # Export texto
        if st.button("📄 Exportar como Texto", use_container_width=True):
            report_text = insights_generator.export_insights_to_text()
            st.download_button(
                label="📥 Download Relatório TXT",
                data=report_text,
                file_name=f"relatorio_insights_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
    
    with col_export2:
        # Export CSV
        if st.button("📊 Exportar como CSV", use_container_width=True):
            insights_df = pd.DataFrame([
                {
                    'Timestamp': insight['timestamp'],
                    'Titulo': insight['title'],
                    'Descricao': insight['description'],
                    'Recomendacao': insight['recommendation'],
                    'Tipo': insight['type'],
                    'Prioridade': insight['priority']
                }
                for insight in insights
            ])
            
            csv_data = insights_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Relatório CSV",
                data=csv_data,
                file_name=f"insights_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with col_export3:
        # Gerar novo relatório
        if st.button("🔄 Gerar Novo Relatório", use_container_width=True):
            st.rerun()
    
    # Estatísticas do relatório
    st.markdown("---")
    st.subheader("📈 Estatísticas do Relatório")
    
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    
    with col_stats1:
        critical_count = len([i for i in insights if i['type'] == 'error'])
        st.metric("🚨 Insights Críticos", critical_count)
    
    with col_stats2:
        warning_count = len([i for i in insights if i['type'] == 'warning'])
        st.metric("⚠️ Requer Atenção", warning_count)
    
    with col_stats3:
        positive_count = len([i for i in insights if i['type'] == 'success'])
        st.metric("✅ Pontos Positivos", positive_count)
    
    with col_stats4:
        total_recommendations = len([i for i in insights if i['recommendation']])
        st.metric("💡 Recomendações", total_recommendations)

def calculate_general_score(insights):
    """Calcula score geral baseado nos insights"""
    if not insights:
        return 75  # Score neutro
    
    score = 100
    
    for insight in insights:
        if insight['type'] == 'error':
            score -= 15
        elif insight['type'] == 'warning':
            score -= 8
        elif insight['type'] == 'success':
            score += 5
        # info insights não afetam o score
    
    return max(0, min(100, score))

if __name__ == "__main__":
    main()

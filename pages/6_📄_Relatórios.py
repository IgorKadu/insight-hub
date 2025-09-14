"""Página de Relatórios Avançados"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.pdf_reports import PDFReportGenerator
from utils.data_analyzer import DataAnalyzer
import os

st.set_page_config(page_title="Relatórios", page_icon="📄", layout="wide")
st.title("📄 Relatórios Avançados")
st.markdown("*Sistema completo de geração de relatórios com dados consolidados de todos os painéis*")

# Carregar dados diretamente da base de dados
df_inicial = DatabaseManager.get_dashboard_data()
if df_inicial.empty:
    st.warning("⚠️ Nenhum dado encontrado. Faça upload de arquivos CSV primeiro.")
    st.stop()
else:
    st.success(f"✅ Dados carregados: {len(df_inicial):,} registros para geração de relatórios")

# Carregar dados com cache para performance
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_report_data():
    """Carrega dados otimizados para relatórios"""
    try:
        df = DatabaseManager.get_dashboard_data()
        summary = DatabaseManager.get_fleet_summary()
        
        if df.empty:
            return None, None
            
        return df, summary
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None, None

# Configurações do relatório
st.sidebar.header("⚙️ Configurações do Relatório")

# Filtros de período
periodo_opcoes = {
    "Últimos 7 dias": 7,
    "Últimos 30 dias": 30,
    "Últimos 90 dias": 90,
    "Todos os dados": None
}

periodo_selecionado = st.sidebar.selectbox(
    "📅 Período:",
    options=list(periodo_opcoes.keys()),
    index=1  # Padrão: últimos 30 dias
)

# Tipos de relatório
tipo_relatorio = st.sidebar.selectbox(
    "📊 Tipo de Relatório:",
    [
        "📋 Relatório Executivo Completo",
        "🚗 Análise Detalhada por Veículo", 
        "⚡ Relatório de Performance",
        "🚨 Relatório de Conformidade",
        "📈 Análise de Tendências",
        "🔍 Relatório Personalizado"
    ]
)

# Opções de formato
formato_saida = st.sidebar.selectbox(
    "📄 Formato:",
    ["PDF Profissional", "Visualização Web", "Dados CSV", "Relatório Completo (PDF + CSV)"]
)

# Incluir gráficos
incluir_graficos = st.sidebar.checkbox("📊 Incluir Gráficos", value=True)
incluir_mapas = st.sidebar.checkbox("🗺️ Incluir Mapas", value=False)

# Carregar dados
df, summary = load_report_data()

if df is None or df.empty:
    st.error("❌ Não foi possível carregar os dados para o relatório.")
    st.stop()

# Filtrar dados por período se especificado - com validação de tipo
df_filtered = df.copy()

# Converter coluna de data para datetime de forma segura
if 'data' in df_filtered.columns:
    df_filtered['data'] = pd.to_datetime(df_filtered['data'], errors='coerce')
    df_filtered = df_filtered.dropna(subset=['data'])

if periodo_opcoes[periodo_selecionado] is not None:
    dias = periodo_opcoes[periodo_selecionado]
    cutoff_date = datetime.now() - timedelta(days=dias)
    
    # Filtrar apenas se a coluna de data está disponível e foi convertida com sucesso
    if 'data' in df_filtered.columns and not df_filtered.empty:
        # Verificar se a coluna de data tem timezone e ajustar a comparação
        if hasattr(df_filtered['data'].dtype, 'tz') and df_filtered['data'].dtype.tz is not None:
            # Se dados têm timezone, converter cutoff_date para timezone-aware
            from datetime import timezone
            cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)
        else:
            # Se dados são naive, garantir que cutoff_date também seja naive
            cutoff_date = cutoff_date.replace(tzinfo=None)
        
        df_filtered = df_filtered[df_filtered['data'] >= cutoff_date]
        st.info(f"📅 Dados filtrados: {len(df_filtered):,} registros dos últimos {dias} dias")
    else:
        st.warning("⚠️ Não foi possível filtrar por período - dados de data indisponíveis")
else:
    st.info(f"📅 Usando todos os dados: {len(df_filtered):,} registros")

# Análise preliminar para o relatório
analyzer = DataAnalyzer(df_filtered)

# ========== DEFINIÇÕES DAS FUNÇÕES ==========

def show_report_preview(df, summary, analyzer, tipo_relatorio):
    """Mostra pré-visualização do relatório"""
    st.subheader("👁️ Pré-visualização do Relatório")
    
    # Estatísticas gerais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de Registros", f"{len(df):,}")
    with col2:
        st.metric("🚗 Veículos", f"{df['placa'].nunique()}")
    with col3:
        st.metric("🏢 Clientes", f"{df['cliente'].nunique()}")
    with col4:
        st.metric("📅 Período", f"{(df['data'].max() - df['data'].min()).days} dias")
    
    # Conteúdo baseado no tipo de relatório
    if "Executivo" in tipo_relatorio:
        show_executive_preview(df, summary, analyzer)
    elif "Veículo" in tipo_relatorio:
        show_vehicle_preview(df, analyzer)
    elif "Performance" in tipo_relatorio:
        show_performance_preview(df, analyzer)
    elif "Conformidade" in tipo_relatorio:
        show_compliance_preview(df, analyzer)
    elif "Tendências" in tipo_relatorio:
        show_trends_preview(df, analyzer)
    else:
        show_custom_preview(df, analyzer)

def show_executive_preview(df, summary, analyzer):
    """Preview do relatório executivo"""
    st.markdown("### 📋 Resumo Executivo")
    
    # KPIs principais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        velocidade_media = df['velocidade_km'].mean()
        st.metric("⚡ Velocidade Média", f"{velocidade_media:.1f} km/h")
        
    with col2:
        gps_coverage = (df['gps'].sum() / len(df)) * 100
        st.metric("📡 Cobertura GPS", f"{gps_coverage:.1f}%")
        
    with col3:
        utilizacao = len(df[df['velocidade_km'] > 0]) / len(df) * 100
        st.metric("🚗 Taxa de Utilização", f"{utilizacao:.1f}%")
    
    # Gráfico de utilização por veículo
    vehicle_usage = df.groupby('placa').agg({
        'velocidade_km': 'mean',
        'data': 'count'
    }).reset_index()
    vehicle_usage.columns = ['Veículo', 'Velocidade Média', 'Registros']
    
    fig = px.bar(vehicle_usage, x='Veículo', y='Registros', 
                 title="📊 Registros por Veículo")
    st.plotly_chart(fig, use_container_width=True)

def show_vehicle_preview(df, analyzer):
    """Preview da análise por veículo"""
    st.markdown("### 🚗 Análise por Veículo")
    
    # Seleção de veículo
    veiculos = sorted(df['placa'].unique())
    veiculo_selecionado = st.selectbox("Selecione um veículo:", veiculos)
    
    df_veiculo = df[df['placa'] == veiculo_selecionado]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Registros", f"{len(df_veiculo):,}")
    with col2:
        vel_media = df_veiculo['velocidade_km'].mean()
        st.metric("⚡ Velocidade Média", f"{vel_media:.1f} km/h")
    with col3:
        vel_max = df_veiculo['velocidade_km'].max()
        st.metric("🏎️ Velocidade Máxima", f"{vel_max:.1f} km/h")
    with col4:
        utilizacao = len(df_veiculo[df_veiculo['velocidade_km'] > 0]) / len(df_veiculo) * 100
        st.metric("📈 Utilização", f"{utilizacao:.1f}%")
    
    # Gráfico de velocidade ao longo do tempo
    df_veiculo_sample = df_veiculo.sample(min(500, len(df_veiculo)))
    fig = px.line(df_veiculo_sample, x='data', y='velocidade_km',
                  title=f"📈 Velocidade ao Longo do Tempo - {veiculo_selecionado}")
    st.plotly_chart(fig, use_container_width=True)

def show_performance_preview(df, analyzer):
    """Preview do relatório de performance"""
    st.markdown("### ⚡ Análise de Performance")
    
    # Top performers
    performance = df.groupby('placa').agg({
        'velocidade_km': 'mean',
        'odometro_periodo_km': 'sum',
        'data': 'count'
    }).reset_index()
    performance.columns = ['Veículo', 'Velocidade Média', 'KM Total', 'Registros']
    performance = performance.sort_values('KM Total', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏆 Top 5 - Maior Quilometragem**")
        top_km = performance.head(5)
        st.dataframe(top_km[['Veículo', 'KM Total']], hide_index=True)
        
    with col2:
        st.markdown("**⚡ Top 5 - Maior Velocidade Média**")
        top_speed = performance.sort_values('Velocidade Média', ascending=False).head(5)
        st.dataframe(top_speed[['Veículo', 'Velocidade Média']], hide_index=True)
    
    # Gráfico de eficiência
    fig = px.scatter(performance, x='Velocidade Média', y='KM Total', 
                     size='Registros', text='Veículo',
                     title="📊 Matriz de Performance: Velocidade vs Quilometragem")
    st.plotly_chart(fig, use_container_width=True)

def show_compliance_preview(df, analyzer):
    """Preview do relatório de conformidade"""
    st.markdown("### 🚨 Análise de Conformidade")
    
    # Análise de velocidade
    excesso_velocidade = df[df['velocidade_km'] > 80]
    violacoes_criticas = df[df['velocidade_km'] > 100]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("⚠️ Excessos de Velocidade", len(excesso_velocidade))
    with col2:
        st.metric("🚨 Violações Críticas", len(violacoes_criticas))
    with col3:
        conformidade = (1 - len(excesso_velocidade) / len(df)) * 100
        st.metric("✅ Taxa de Conformidade", f"{conformidade:.1f}%")
    
    if len(excesso_velocidade) > 0:
        # Veículos com mais violações
        violacoes_por_veiculo = excesso_velocidade.groupby('placa').size().reset_index(name='Violações')
        violacoes_por_veiculo = violacoes_por_veiculo.sort_values('Violações', ascending=False)
        
        fig = px.bar(violacoes_por_veiculo.head(10), x='placa', y='Violações',
                     title="🚨 Veículos com Mais Violações de Velocidade")
        st.plotly_chart(fig, use_container_width=True)

def show_trends_preview(df, analyzer):
    """Preview da análise de tendências"""
    st.markdown("### 📈 Análise de Tendências")
    
    # Tendências por dia
    df['dia'] = df['data'].dt.date
    tendencias_diarias = df.groupby('dia').agg({
        'velocidade_km': 'mean',
        'data': 'count'
    }).reset_index()
    tendencias_diarias.columns = ['Data', 'Velocidade Média', 'Registros']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.line(tendencias_diarias, x='Data', y='Velocidade Média',
                       title="📈 Tendência de Velocidade Média")
        st.plotly_chart(fig1, use_container_width=True)
        
    with col2:
        fig2 = px.line(tendencias_diarias, x='Data', y='Registros',
                       title="📊 Tendência de Atividade")
        st.plotly_chart(fig2, use_container_width=True)

def show_custom_preview(df, analyzer):
    """Preview do relatório personalizado"""
    st.markdown("### 🔍 Relatório Personalizado")
    st.info("Configure suas métricas personalizadas na aba Configurações")

def show_report_dashboard(df, analyzer):
    """Dashboard interativo do relatório"""
    st.subheader("📊 Dashboard Interativo")
    
    # Filtros interativos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        veiculos_selecionados = st.multiselect(
            "🚗 Veículos:",
            options=sorted(df['placa'].unique()),
            default=sorted(df['placa'].unique())[:5]  # Primeiros 5 por padrão
        )
    
    with col2:
        data_inicio = st.date_input("📅 Data Início:", value=df['data'].min().date())
    
    with col3:
        data_fim = st.date_input("📅 Data Fim:", value=df['data'].max().date())
    
    # Filtrar dados
    df_filtered = df[
        (df['placa'].isin(veiculos_selecionados)) &
        (df['data'].dt.date >= data_inicio) &
        (df['data'].dt.date <= data_fim)
    ]
    
    if df_filtered.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Registros Filtrados", f"{len(df_filtered):,}")
    with col2:
        vel_media = df_filtered['velocidade_km'].mean()
        st.metric("⚡ Velocidade Média", f"{vel_media:.1f} km/h")
    with col3:
        km_total = df_filtered['odometro_periodo_km'].sum()
        st.metric("🛣️ KM Total", f"{km_total:.1f}")
    with col4:
        gps_coverage = (df_filtered['gps'].sum() / len(df_filtered)) * 100
        st.metric("📡 GPS Coverage", f"{gps_coverage:.1f}%")
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição de velocidade
        fig1 = px.histogram(df_filtered, x='velocidade_km', nbins=30,
                           title="📊 Distribuição de Velocidade")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Atividade por hora
        df_filtered['hora'] = df_filtered['data'].dt.hour
        atividade_hora = df_filtered.groupby('hora').size().reset_index(name='Registros')
        fig2 = px.bar(atividade_hora, x='hora', y='Registros',
                      title="📈 Atividade por Hora do Dia")
        st.plotly_chart(fig2, use_container_width=True)

def show_advanced_settings():
    """Configurações avançadas do relatório"""
    st.subheader("⚙️ Configurações Avançadas")
    
    # Configurações de métricas
    st.markdown("### 📊 Métricas Personalizadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("📈 Incluir análise de tendências", value=True)
        st.checkbox("🚨 Incluir alertas de segurança", value=True)
        st.checkbox("⚡ Incluir métricas de performance", value=True)
        st.checkbox("🗺️ Incluir análise geográfica", value=False)
    
    with col2:
        st.number_input("🏎️ Limite de velocidade (km/h):", min_value=50, max_value=120, value=80)
        st.number_input("🔋 Bateria baixa (V):", min_value=10.0, max_value=15.0, value=12.0)
        st.slider("📊 Número de veículos no top ranking:", 5, 20, 10)
        
    # Configurações de formato
    st.markdown("### 📄 Formatação do Relatório")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox("🎨 Tema do relatório:", ["Profissional", "Moderno", "Clássico"])
        st.selectbox("📊 Estilo dos gráficos:", ["Plotly", "Matplotlib", "Seaborn"])
    
    with col2:
        st.selectbox("📄 Tamanho da página:", ["A4", "Letter", "A3"])
        st.selectbox("🔤 Idioma:", ["Português", "English", "Español"])

def show_download_options(df, summary, analyzer, tipo_relatorio, formato_saida, incluir_graficos):
    """Opções de download do relatório"""
    st.subheader("📥 Download do Relatório")
    
    # Informações do relatório a ser gerado
    st.markdown(f"**📊 Tipo:** {tipo_relatorio}")
    st.markdown(f"**📄 Formato:** {formato_saida}")
    st.markdown(f"**📅 Período:** {len(df):,} registros")
    st.markdown(f"**🚗 Veículos:** {df['placa'].nunique()}")
    
    # Botões de geração
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Gerar PDF Profissional", type="primary"):
            with st.spinner("🔄 Gerando relatório PDF..."):
                try:
                    generator = PDFReportGenerator()
                    # Usar método existente até implementar o avançado
                    pdf_path = generator.generate_fleet_report()
                    
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as file:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"relatorio_{tipo_relatorio.split()[1].lower()}_{timestamp}.pdf"
                            
                            st.download_button(
                                label="⬇️ Baixar PDF",
                                data=file.read(),
                                file_name=filename,
                                mime="application/pdf"
                            )
                        st.success("✅ Relatório PDF gerado com sucesso!")
                    else:
                        st.error("❌ Erro ao gerar relatório PDF")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
    
    with col2:
        if st.button("📊 Exportar Dados CSV"):
            csv_data = df.to_csv(index=False)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dados_frota_{timestamp}.csv"
            
            st.download_button(
                label="⬇️ Baixar CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )
            st.success("✅ Dados CSV prontos para download!")
    
    with col3:
        if st.button("📈 Relatório Completo"):
            st.info("🚧 Gerando relatório completo (PDF + CSV + Gráficos)...")
            st.markdown("*Funcionalidade em desenvolvimento*")
    
    # Histórico de relatórios
    st.markdown("### 📋 Histórico de Relatórios")
    st.info("📁 Últimos relatórios gerados aparecerão aqui")

# ========== SEÇÃO PRINCIPAL - EXECUTADA APÓS DEFINIÇÕES ==========
# Seção principal de geração de relatórios
st.header("📊 Geração de Relatórios")

# Tabs para diferentes visualizações
tab1, tab2, tab3, tab4 = st.tabs(["📋 Pré-visualização", "📊 Dashboard", "⚙️ Configurações", "📥 Download"])

with tab1:
    show_report_preview(df_filtered, summary, analyzer, tipo_relatorio)

with tab2:
    show_report_dashboard(df_filtered, analyzer)

with tab3:
    show_advanced_settings()

with tab4:
    show_download_options(df_filtered, summary, analyzer, tipo_relatorio, formato_saida, incluir_graficos)
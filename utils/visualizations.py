import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class FleetVisualizations:
    """Classe para criar visualizações de dados de frota"""
    
    def __init__(self, analyzer):
        """Inicializa com um analisador de dados"""
        self.analyzer = analyzer
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd'
        }
    
    def create_kpi_charts(self):
        """Cria gráficos de KPIs"""
        kpis = self.analyzer.get_kpis()
        
        if not kpis:
            return {}
        
        charts = {}
        
        # Gráfico de velocidade média por veículo
        speed_by_vehicle = self.analyzer.filtered_df.groupby('placa')['velocidade_km'].mean().sort_values(ascending=False)
        
        charts['speed_by_vehicle'] = px.bar(
            x=speed_by_vehicle.values[:15],  # Top 15
            y=speed_by_vehicle.index[:15],
            orientation='h',
            title='Velocidade Média por Veículo (Top 15)',
            labels={'x': 'Velocidade Média (km/h)', 'y': 'Placa'}
        )
        
        # Gráfico de distribuição de velocidade
        charts['speed_distribution'] = px.histogram(
            self.analyzer.filtered_df,
            x='velocidade_km',
            nbins=30,
            title='Distribuição de Velocidade',
            labels={'x': 'Velocidade (km/h)', 'y': 'Frequência'}
        )
        
        return charts
    
    def create_temporal_charts(self):
        """Cria gráficos temporais"""
        df = self.analyzer.filtered_df
        
        if df.empty:
            return {}
        
        charts = {}
        
        # Atividade por hora do dia
        hourly_activity = df.groupby(df['data'].dt.hour).agg({
            'placa': 'nunique',
            'velocidade_km': 'mean'
        }).reset_index()
        
        charts['hourly_activity'] = px.line(
            hourly_activity,
            x='data',
            y='placa',
            title='Veículos Ativos por Hora do Dia',
            labels={'data': 'Hora', 'placa': 'Número de Veículos Ativos'}
        )
        
        # Velocidade média por hora
        charts['hourly_speed'] = px.line(
            hourly_activity,
            x='data',
            y='velocidade_km',
            title='Velocidade Média por Hora do Dia',
            labels={'data': 'Hora', 'velocidade_km': 'Velocidade Média (km/h)'}
        )
        
        # Atividade diária
        daily_activity = df.groupby(df['data'].dt.date).agg({
            'placa': 'nunique',
            'odometro_periodo_km': 'sum',
            'velocidade_km': 'mean'
        }).reset_index()
        
        charts['daily_activity'] = px.line(
            daily_activity,
            x='data',
            y='placa',
            title='Veículos Ativos por Dia',
            labels={'data': 'Data', 'placa': 'Número de Veículos Ativos'}
        )
        
        return charts
    
    def create_compliance_charts(self):
        """Cria gráficos de compliance"""
        compliance = self.analyzer.get_compliance_analysis()
        
        if not compliance:
            return {}
        
        charts = {}
        
        # Score de compliance por veículo
        if compliance['score_compliance']:
            scores_df = pd.DataFrame(list(compliance['score_compliance'].items()), 
                                   columns=['Placa', 'Score'])
            scores_df = scores_df.sort_values('Score', ascending=False)
            
            # Definir cores baseadas no score
            colors = ['#2ca02c' if score >= 90 else '#ff7f0e' if score >= 70 else '#d62728' 
                     for score in scores_df['Score']]
            
            charts['compliance_scores'] = go.Figure(data=[
                go.Bar(
                    x=scores_df['Placa'],
                    y=scores_df['Score'],
                    marker_color=colors,
                    text=scores_df['Score'].round(1),
                    textposition='outside'
                )
            ])
            charts['compliance_scores'].update_layout(
                title='Score de Compliance por Veículo',
                xaxis_title='Placa',
                yaxis_title='Score (%)',
                yaxis=dict(range=[0, 100])
            )
        
        # Violações de velocidade
        if 'detalhes_violacoes' in compliance and not compliance['detalhes_violacoes'].empty:
            violations_df = compliance['detalhes_violacoes'].head(10).reset_index()
            
            charts['speed_violations'] = px.bar(
                violations_df,
                x='placa',
                y=0,  # A coluna de contagem
                title='Top 10 Veículos com Violações de Velocidade',
                labels={'placa': 'Placa', '0': 'Número de Violações'}
            )
        
        return charts
    
    def create_comparison_chart(self, comparison_data):
        """Cria gráfico de comparação entre veículos"""
        if not comparison_data:
            return None
        
        # Converter dados para DataFrame
        df_comparison = pd.DataFrame(comparison_data).T.reset_index()
        df_comparison.columns = ['Placa'] + list(df_comparison.columns[1:])
        
        # Criar gráfico de radar/spider
        categories = ['Velocidade Média', 'Distância Total', 'Tempo Ativo', 'Cobertura GPS']
        
        fig = go.Figure()
        
        for _, row in df_comparison.iterrows():
            fig.add_trace(go.Scatterpolar(
                r=[
                    row['velocidade_media'],
                    row['distancia_total'] / 100,  # Normalizar
                    row['tempo_ativo'] / 10,  # Normalizar
                    row['cobertura_gps']
                ],
                theta=categories,
                fill='toself',
                name=row['Placa']
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Comparação de Performance entre Veículos"
        )
        
        return fig
    
    def create_efficiency_charts(self):
        """Cria gráficos de eficiência"""
        efficiency = self.analyzer.get_efficiency_metrics()
        
        if not efficiency:
            return {}
        
        charts = {}
        
        # Top veículos por quilometragem
        if 'top_veiculos_km' in efficiency:
            top_km = efficiency['top_veiculos_km'].head(10)
            
            charts['top_km'] = px.bar(
                x=top_km.values,
                y=top_km.index,
                orientation='h',
                title='Top 10 Veículos por Quilometragem Total',
                labels={'x': 'Quilometragem Total (km)', 'y': 'Placa'}
            )
        
        # Veículos mais utilizados
        if 'veiculos_mais_utilizados' in efficiency:
            most_used = efficiency['veiculos_mais_utilizados'].head(10)
            
            charts['most_used'] = px.bar(
                x=most_used.values,
                y=most_used.index,
                orientation='h',
                title='Top 10 Veículos Mais Utilizados',
                labels={'x': 'Número de Registros', 'y': 'Placa'}
            )
        
        return charts
    
    def create_speed_analysis_charts(self):
        """Cria gráficos de análise de velocidade"""
        speed_analysis = self.analyzer.get_speed_analysis()
        
        if not speed_analysis:
            return {}
        
        charts = {}
        
        # Distribuição por faixas de velocidade
        if 'distribuicao' in speed_analysis:
            dist_data = speed_analysis['distribuicao']
            
            charts['speed_ranges'] = px.pie(
                values=dist_data.values,
                names=dist_data.index,
                title='Distribuição por Faixas de Velocidade'
            )
        
        # Velocidade por hora do dia
        if 'velocidade_por_hora' in speed_analysis:
            hourly_speed = speed_analysis['velocidade_por_hora']
            
            charts['speed_by_hour'] = px.line(
                x=hourly_speed.index,
                y=hourly_speed.values,
                title='Velocidade Média por Hora do Dia',
                labels={'x': 'Hora', 'y': 'Velocidade Média (km/h)'}
            )
        
        return charts
    
    def create_map_visualization(self, sample_size=1000):
        """Cria visualização de mapa com as localizações"""
        df = self.analyzer.filtered_df
        
        if df.empty or 'localizacao' not in df.columns:
            return None
        
        # Filtrar apenas uma amostra para performance
        if len(df) > sample_size:
            df_sample = df.sample(n=sample_size)
        else:
            df_sample = df
        
        # Extrair coordenadas (assumindo formato "lat,lng")
        coords_data = []
        for _, row in df_sample.iterrows():
            try:
                if pd.notna(row['localizacao']) and ',' in str(row['localizacao']):
                    lat, lng = map(float, str(row['localizacao']).split(','))
                    coords_data.append({
                        'lat': lat,
                        'lng': lng,
                        'placa': row['placa'],
                        'velocidade': row['velocidade_km'],
                        'data': row['data']
                    })
            except:
                continue
        
        if not coords_data:
            return None
        
        coords_df = pd.DataFrame(coords_data)
        
        # Criar mapa
        fig = px.scatter_mapbox(
            coords_df,
            lat='lat',
            lon='lng',
            color='velocidade',
            size='velocidade',
            hover_data=['placa', 'data'],
            color_continuous_scale='Viridis',
            mapbox_style='open-street-map',
            title='Localização dos Veículos (Amostra)',
            zoom=10
        )
        
        fig.update_layout(height=500)
        
        return fig
    
    def create_dashboard_summary(self):
        """Cria resumo visual para dashboard"""
        kpis = self.analyzer.get_kpis()
        
        if not kpis:
            return None
        
        # Criar gráfico de gauge para métricas principais
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Cobertura GPS (%)', 'Utilização da Frota', 
                          'Velocidade Média', 'Eficiência Operacional'),
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}]]
        )
        
        # Gauge para cobertura GPS
        fig.add_trace(go.Indicator(
            mode = "gauge+number",
            value = kpis['cobertura_gps'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "GPS"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90}}
        ), row=1, col=1)
        
        # Mais indicadores podem ser adicionados aqui...
        
        fig.update_layout(height=400)
        
        return fig

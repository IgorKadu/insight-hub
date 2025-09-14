import streamlit as st
import pandas as pd
import os
from datetime import datetime
import sys

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.csv_processor import CSVProcessor
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="Upload CSV - Insight Hub",
    page_icon="📁",
    layout="wide"
)

def main():
    st.title("📁 Upload e Processamento de Dados CSV")
    st.markdown("---")
    
    # Informações sobre o formato esperado
    with st.expander("📋 Formato do Arquivo CSV", expanded=False):
        st.markdown("""
        ### Campos Obrigatórios (25 campos):
        
        1. **Cliente** - Nome do cliente/empresa
        2. **Placa** - Placa do veículo
        3. **Ativo** - Identificador do ativo
        4. **Data** - Data/hora do evento
        5. **Data (GPRS)** - Data/hora de comunicação GPRS
        6. **Velocidade (Km)** - Velocidade em km/h
        7. **Ignição** - Status da ignição (D/L)
        8. **Motorista** - Identificação do motorista
        9. **GPS** - Status do GPS (0/1)
        10. **Gprs** - Status do GPRS (0/1)
        11. **Localização** - Coordenadas do veículo
        12. **Endereço** - Endereço convertido
        13. **Tipo do Evento** - Tipo do evento registrado
        14. **Cerca** - Informações de cerca eletrônica
        15. **Saida** - Status das saídas digitais
        16. **Entrada** - Status das entradas digitais
        17. **Pacote** - Informações de pacotes de dados
        18. **Odômetro do período (Km)** - Km percorridos
        19. **Horímetro do período** - Tempo de funcionamento
        20. **Horímetro embarcado** - Contador de horas
        21. **Odômetro embarcado (Km)** - Odômetro embarcado
        22. **Bateria** - Nível de bateria
        23. **Imagem** - Link para imagem (opcional)
        24. **Tensão** - Tensão elétrica
        25. **Bloqueado** - Status de bloqueio (0/1)
        
        ### Observações:
        - O arquivo deve estar em formato CSV com separador vírgula (,)
        - Todos os 25 campos são obrigatórios
        - Tamanho máximo: 50MB
        - Até 100.000 registros por arquivo
        """)
    
    # Área de upload
    st.subheader("📤 Fazer Upload do Arquivo CSV")
    
    uploaded_files = st.file_uploader(
        "Selecione os arquivos CSV:",
        type=['csv'],
        help="Múltiplos arquivos CSV com dados telemáticos da frota",
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Mostrar informações dos arquivos
        st.info(f"📁 **{len(uploaded_files)} arquivo(s) selecionado(s)**")
        
        total_size = sum(f.size for f in uploaded_files)
        if total_size > 200 * 1024 * 1024:  # 200MB total
            st.error("❌ Total de arquivos muito grande! Tamanho máximo: 200MB")
            st.stop()
        
        # Mostrar lista de arquivos
        for i, file in enumerate(uploaded_files):
            size_mb = file.size / 1024 / 1024
            st.write(f"{i+1}. **{file.name}** - {size_mb:.2f} MB")
        
        # Preview do primeiro arquivo
        try:
            first_file = uploaded_files[0]
            preview_df = None
            separators = [';', ',']
            encodings = ['latin-1', 'utf-8', 'iso-8859-1', 'windows-1252', 'cp1252']
            
            for sep in separators:
                for enc in encodings:
                    try:
                        first_file.seek(0)
                        preview_df = pd.read_csv(first_file, sep=sep, encoding=enc, nrows=5)
                        st.success(f"📄 Formato detectado: separador '{sep}', encoding '{enc}'")
                        break
                    except:
                        continue
                if preview_df is not None:
                    break
            
            if preview_df is not None:
                st.subheader("👀 Preview dos Dados")
                st.dataframe(preview_df, width='stretch')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Colunas encontradas", len(preview_df.columns))
                with col2:
                    st.metric("Total de arquivos", len(uploaded_files))
            
            first_file.seek(0)
            
            # Botão para processar todos os arquivos
            if st.button("🚀 Processar Todos os Arquivos", type="primary"):
                # Ordenar arquivos por tamanho (menor para maior) para processamento mais eficiente
                sorted_files = sorted(uploaded_files, key=lambda f: f.size)
                st.info(f"📊 Arquivos ordenados por tamanho: menor → maior para otimizar processamento")
                process_multiple_csv_files(sorted_files)
                
        except Exception as e:
            st.error(f"❌ Erro ao ler os arquivos: {str(e)}")
    
    # Mostrar histórico de arquivos processados
    show_processing_history()

def process_multiple_csv_files(uploaded_files):
    """Processa múltiplos arquivos CSV com progresso detalhado"""
    
    # Container principal para progresso
    progress_container = st.container()
    
    with progress_container:
        st.markdown("### 📊 Progresso de Processamento")
        
        # Progresso geral
        overall_progress = st.progress(0)
        overall_status = st.empty()
        
        # Progresso do arquivo atual
        current_file_info = st.empty()
        file_progress_bar = st.progress(0)
        file_status = st.empty()
        
        # Métricas em tempo real
        metrics_cols = st.columns(3)
        with metrics_cols[0]:
            files_metric = st.empty()
        with metrics_cols[1]:
            records_metric = st.empty()
        with metrics_cols[2]:
            speed_metric = st.empty()
    
    total_files = len(uploaded_files)
    processed_files = 0
    total_records = 0
    failed_files = 0
    
    import time
    start_time = time.time()
    
    for i, uploaded_file in enumerate(uploaded_files):
        file_start_time = time.time()
        
        # Atualizar progresso geral
        overall_progress.progress(i / total_files)
        overall_status.markdown(f"📂 **Processando arquivo {i+1} de {total_files}**")
        
        # Informações do arquivo atual
        file_size_mb = uploaded_file.size / (1024 * 1024)
        current_file_info.markdown(f"""
        📄 **{uploaded_file.name}**  
        📏 Tamanho: {file_size_mb:.1f} MB
        """)
        
        # Resetar progresso do arquivo
        file_progress_bar.progress(0)
        file_status.markdown("🔄 Iniciando processamento...")
        
        # Atualizar métricas
        files_metric.metric(
            label="📁 Arquivos",
            value=f"{processed_files + failed_files}/{total_files}",
            delta=f"{i}/{total_files}"
        )
        records_metric.metric(
            label="📊 Registros",
            value=f"{total_records:,}",
            delta="Processando..."
        )
        
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            files_per_min = (i / elapsed_time) * 60
            speed_metric.metric(
                label="⚡ Velocidade",
                value=f"{files_per_min:.1f}",
                delta="arquivos/min"
            )
        
        # Processar arquivo com callback de progresso
        result = process_single_csv_file_with_progress(
            uploaded_file, 
            file_progress_bar, 
            file_status
        )
        
        # Finalizar progresso do arquivo
        file_progress_bar.progress(1.0)
        file_processing_time = time.time() - file_start_time
        
        if result['success']:
            processed_files += 1
            records_processed = result.get('records_processed', 0)
            total_records += records_processed
            
            file_status.markdown(f"✅ **Concluído!** {records_processed:,} registros em {file_processing_time:.1f}s")
            
            # Log de sucesso
            with st.expander(f"✅ {uploaded_file.name}", expanded=False):
                st.success(f"Processado com sucesso: {records_processed:,} registros")
                st.info(f"Tempo: {file_processing_time:.1f}s | Velocidade: {records_processed/file_processing_time:.0f} reg/s")
        else:
            failed_files += 1
            file_status.markdown("❌ **Erro no processamento**")
            
            # Log de erro
            with st.expander(f"❌ {uploaded_file.name}", expanded=True):
                st.error(f"Erro: {result.get('error', 'Erro desconhecido')}")
        
        # Pequena pausa para visualização
        time.sleep(0.1)
    
    # Finalizar progresso geral
    overall_progress.progress(1.0)
    total_time = time.time() - start_time
    
    overall_status.markdown("🎉 **Processamento Finalizado!**")
    current_file_info.markdown("📁 **Todos os arquivos processados**")
    file_status.markdown(f"⏱️ Tempo total: {total_time:.1f}s")
    
    # Métricas finais
    files_metric.metric(
        label="📁 Arquivos",
        value=f"{processed_files}/{total_files}",
        delta=f"{failed_files} erros" if failed_files > 0 else "Todos OK"
    )
    records_metric.metric(
        label="📊 Registros",
        value=f"{total_records:,}",
        delta="Processados"
    )
    speed_metric.metric(
        label="⚡ Velocidade média",
        value=f"{total_records/total_time:.0f}" if total_time > 0 else "0",
        delta="registros/s"
    )
    
    # Resumo final
    if processed_files == total_files:
        st.success(f"""
        🎉 **Processamento 100% concluído!**
        - ✅ {processed_files} arquivos processados com sucesso
        - 📊 {total_records:,} registros inseridos na base de dados
        - ⏱️ Tempo total: {total_time:.1f} segundos
        - ⚡ Velocidade média: {total_records/total_time:.0f} registros/segundo
        """)
    else:
        st.warning(f"""
        ⚠️ **Processamento concluído com erros**
        - ✅ {processed_files} arquivos processados com sucesso
        - ❌ {failed_files} arquivos com erro
        - 📊 {total_records:,} registros inseridos na base de dados
        - ⏱️ Tempo total: {total_time:.1f} segundos
        """)

def process_single_csv_file_with_progress(uploaded_file, progress_bar, status_display):
    """Processa um único arquivo CSV com progresso em tempo real"""
    
    try:
        import tempfile
        import time
        
        # Fase 1: Salvando arquivo temporário
        status_display.markdown("📥 Salvando arquivo temporário...")
        progress_bar.progress(0.1)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Fase 2: Analisando estrutura
        status_display.markdown("🔍 Analisando estrutura do arquivo...")
        progress_bar.progress(0.2)
        time.sleep(0.1)
        
        # Contagem estimada de linhas para melhor progresso
        try:
            with open(tmp_path, 'r', encoding='latin-1') as f:
                estimated_rows = sum(1 for _ in f) - 1  # -1 para header
        except:
            estimated_rows = 1000  # Fallback
        
        status_display.markdown(f"📊 Arquivo com ~{estimated_rows:,} registros detectados")
        progress_bar.progress(0.3)
        
        # Fase 3: Processando dados
        status_display.markdown("⚙️ Processando e validando dados...")
        progress_bar.progress(0.5)
        time.sleep(0.2)
        
        # Fase 4: Inserindo na base de dados
        status_display.markdown("💾 Inserindo registros na base de dados...")
        progress_bar.progress(0.7)
        
        # Usar DatabaseManager para migrar com progresso
        def update_progress(current, total, phase):
            progress = 0.7 + (current / total) * 0.2  # 70% até 90%
            progress_bar.progress(progress)
            if phase == "preparando":
                status_display.markdown(f"⚙️ Preparando dados: {current:,}/{total:,}")
            elif phase == "inserindo":
                status_display.markdown(f"💾 Inserindo registros: {current:,}/{total:,}")
        
        result = DatabaseManager.migrate_csv_to_database_with_progress(tmp_path, update_progress)
        
        # Fase 5: Finalizando
        status_display.markdown("🔄 Finalizando processamento...")
        progress_bar.progress(0.9)
        time.sleep(0.1)
        
        # Limpar arquivo temporário
        import os
        os.unlink(tmp_path)
        
        return result
        
    except Exception as e:
        status_display.markdown(f"❌ Erro: {str(e)}")
        return {
            'success': False,
            'error': f'Erro no processamento: {str(e)}',
            'records_processed': 0
        }

def process_single_csv_file(uploaded_file):
    """Processa um único arquivo CSV (versão simplificada para compatibilidade)"""
    
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        result = DatabaseManager.migrate_csv_to_database(tmp_path)
        
        import os
        os.unlink(tmp_path)
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Erro no processamento: {str(e)}',
            'records_processed': 0
        }

def show_processing_summary(summary, filename):
    """Mostra resumo do processamento"""
    
    st.subheader("📊 Resumo do Processamento")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📁 Total de Registros",
            value=f"{summary.get('total_registros', 0):,}"
        )
    
    with col2:
        st.metric(
            label="🚗 Total de Veículos",
            value=f"{summary.get('total_veiculos', 0):,}"
        )
    
    with col3:
        st.metric(
            label="🏢 Total de Clientes",
            value=f"{summary.get('total_clientes', 0):,}"
        )
    
    with col4:
        st.metric(
            label="📅 Período",
            value=f"{(summary.get('periodo_fim', datetime.now()) - summary.get('periodo_inicio', datetime.now())).days + 1} dias"
        )
    
    # Métricas adicionais
    st.markdown("### 📈 Métricas dos Dados")
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric(
            label="⚡ Velocidade Média",
            value=f"{summary.get('velocidade_media', 0):.1f} km/h"
        )
    
    with col6:
        st.metric(
            label="🏎️ Velocidade Máxima",
            value=f"{summary.get('velocidade_maxima', 0):.0f} km/h"
        )
    
    with col7:
        st.metric(
            label="🛣️ Total KM",
            value=f"{summary.get('total_km_periodo', 0):.0f} km"
        )
    
    with col8:
        st.metric(
            label="📡 Com GPS",
            value=f"{summary.get('registros_com_gps', 0):,}"
        )

def save_processing_record(filename, summary):
    """Salva registro do processamento"""
    try:
        os.makedirs('data', exist_ok=True)
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'summary': summary
        }
        
        # Carregar histórico existente
        history_file = 'data/processing_history.csv'
        
        if os.path.exists(history_file):
            history_df = pd.read_csv(history_file)
        else:
            history_df = pd.DataFrame()
        
        # Adicionar novo registro
        new_record = pd.DataFrame([{
            'timestamp': record['timestamp'],
            'filename': filename,
            'total_registros': summary.get('total_registros', 0),
            'total_veiculos': summary.get('total_veiculos', 0),
            'total_clientes': summary.get('total_clientes', 0),
            'periodo_inicio': summary.get('periodo_inicio', ''),
            'periodo_fim': summary.get('periodo_fim', ''),
            'velocidade_media': summary.get('velocidade_media', 0),
            'total_km': summary.get('total_km_periodo', 0)
        }])
        
        history_df = pd.concat([history_df, new_record], ignore_index=True)
        history_df.to_csv(history_file, index=False)
        
    except Exception as e:
        st.warning(f"⚠️ Não foi possível salvar o registro: {str(e)}")

def show_processing_history():
    """Mostra histórico de processamentos da base de dados"""
    try:
        # Tentar buscar histórico da base de dados com retry
        history_records = None
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                history_records = DatabaseManager.get_processing_history()
                break  # Success - exit retry loop
            except Exception as retry_e:
                retry_count += 1
                if retry_count >= max_retries:
                    # Se todas as tentativas falharam, mostrar mensagem amigável
                    st.warning("⚠️ Problema temporário de conexão com a base de dados. O histórico não pode ser carregado no momento.")
                    if st.button("🔄 Tentar Novamente"):
                        st.rerun()
                    return
                else:
                    # Aguardar um pouco antes da próxima tentativa
                    import time
                    time.sleep(0.5)
        
        if not history_records:
            st.info("📋 Nenhum histórico de processamento encontrado.")
            return
        
        st.markdown("### 📋 Histórico de Processamento")
        
        # Converter para DataFrame para exibição
        history_df = pd.DataFrame(history_records)
        
        # Formatação dos dados
        if not history_df.empty:
            # Renomear colunas para português
            history_df = history_df.rename(columns={
                'filename': 'Nome do Arquivo',
                'upload_timestamp': 'Data/Hora',
                'records_processed': 'Registros',
                'unique_vehicles': 'Veículos',
                'unique_clients': 'Clientes',
                'processing_status': 'Status',
                'file_size_bytes': 'Tamanho (bytes)'
            })
            
            # Formatar a coluna de data/hora
            if 'Data/Hora' in history_df.columns:
                history_df['Data/Hora'] = pd.to_datetime(history_df['Data/Hora']).dt.strftime('%d/%m/%Y %H:%M:%S')
            
            # Formatar status
            if 'Status' in history_df.columns:
                history_df['Status'] = history_df['Status'].map({
                    'completed': '✅ Concluído',
                    'failed': '❌ Erro',
                    'processing': '🔄 Processando'
                }).fillna('❓ Desconhecido')
            
            # Formatar números
            for col in ['Registros', 'Veículos', 'Clientes']:
                if col in history_df.columns:
                    history_df[col] = history_df[col].apply(lambda x: f"{x:,}" if pd.notnull(x) else "0")
            
            # Ordenar por data mais recente
            if 'Data/Hora' in history_df.columns:
                history_df = history_df.sort_values('Data/Hora', ascending=False)
            
            # Mostrar tabela
            st.dataframe(
                history_df[['Nome do Arquivo', 'Data/Hora', 'Registros', 'Veículos', 'Clientes', 'Status']], 
                use_container_width=True,
                hide_index=True
            )
            
            # Estatísticas gerais do histórico
            total_records = sum([int(r.get('records_processed', 0)) for r in history_records])
            total_files = len(history_records)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📁 Arquivos Processados", total_files)
            with col2:
                st.metric("📊 Total de Registros", f"{total_records:,}")
            with col3:
                successful_files = len([r for r in history_records if r.get('processing_status') == 'completed'])
                st.metric("✅ Taxa de Sucesso", f"{(successful_files/total_files*100):.1f}%" if total_files > 0 else "0%")
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar histórico: {str(e)}")
        
    # Botões de ação  
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Limpar Histórico", type="secondary", help="Remove apenas os registros do histórico (mantém os dados)"):
            # Implementar limpeza do histórico se necessário
            st.info("Funcionalidade de limpeza de histórico será implementada.")
    
    with col2:
        # Inicializar session state se não existir
        if "confirm_clear_data" not in st.session_state:
            st.session_state.confirm_clear_data = False
        
        if st.button("🗂️ Limpar Todos os Dados", type="secondary", help="Remove TODOS os dados da base (histórico + registros)"):
            st.session_state.confirm_clear_data = True
        
        # Mostrar confirmação se solicitada
        if st.session_state.confirm_clear_data:
            st.warning("⚠️ **ATENÇÃO**: Esta ação irá remover TODOS os dados da base de dados!")
            
            col_conf1, col_conf2 = st.columns(2)
            
            with col_conf1:
                if st.button("✅ SIM, Limpar Tudo", type="primary"):
                    try:
                        with st.spinner("🔄 Limpando todos os dados..."):
                            # Clear all data from database
                            result = DatabaseManager.clear_all_data()
                        
                        st.success(f"""
                        🎉 **Limpeza completa realizada com sucesso!**
                        
                        **Dados removidos:**
                        - 🗂️ {result.get('telematics_data', 0):,} registros telemétricos
                        - 📋 {result.get('processing_history', 0)} registros de histórico  
                        - 🚗 {result.get('vehicles', 0)} veículos
                        - 🏢 {result.get('clients', 0)} clientes
                        
                        **Sistema resetado!** Agora você pode fazer novos uploads.
                        """)
                        
                        # Reset session state
                        st.session_state.confirm_clear_data = False
                        
                        # Recarregar a página para refletir mudanças
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao limpar dados: {str(e)}")
                        st.session_state.confirm_clear_data = False
            
            with col_conf2:
                if st.button("❌ Cancelar", type="secondary"):
                    st.session_state.confirm_clear_data = False
                    st.rerun()

def show_processing_history_old():
    """Mostra histórico de processamentos (versão antiga usando arquivo)"""
    history_file = 'data/processing_history.csv'
    
    if not os.path.exists(history_file):
        st.info("📋 Nenhum histórico de processamento encontrado.")
        return
    
    try:
        history_df = pd.read_csv(history_file)
        
        if history_df.empty:
            st.info("📋 Nenhum arquivo processado ainda.")
            return
        
        st.subheader("📋 Histórico de Processamentos")
        
        # Ordenar por timestamp mais recente
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        history_df = history_df.sort_values('timestamp', ascending=False)
        
        # Formatar para exibição
        display_df = history_df.copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%d/%m/%Y %H:%M')
        display_df = display_df.rename(columns={
            'timestamp': 'Data/Hora',
            'filename': 'Arquivo',
            'total_registros': 'Registros',
            'total_veiculos': 'Veículos',
            'total_clientes': 'Clientes',
            'velocidade_media': 'Vel. Média',
            'total_km': 'Total KM'
        })
        
        # Selecionar colunas para exibição
        display_columns = ['Data/Hora', 'Arquivo', 'Registros', 'Veículos', 'Clientes', 'Vel. Média', 'Total KM']
        
        st.dataframe(
            display_df[display_columns].head(10),
            use_container_width=True,
            hide_index=True
        )
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🗑️ Limpar Histórico", type="secondary"):
                if os.path.exists(history_file):
                    os.remove(history_file)
                    st.success("✅ Histórico limpo com sucesso!")
                    st.rerun()
        
        with col_btn2:
            # Botão para limpar todos os dados da base PostgreSQL
            if st.button("🗂️ Limpar Todos os Dados", type="secondary"):
                if 'confirm_clear_all' not in st.session_state:
                    st.session_state.confirm_clear_all = False
                
                if not st.session_state.confirm_clear_all:
                    st.warning("⚠️ Isso removerá TODOS os dados da base PostgreSQL!")
                    if st.button("⚠️ CONFIRMAR LIMPEZA TOTAL", type="primary"):
                        st.session_state.confirm_clear_all = True
                        st.rerun()
                else:
                    # Executar limpeza da base PostgreSQL
                    result = DatabaseManager.clear_all_data()
                    if result:
                        st.success("✅ Todos os dados foram removidos da base PostgreSQL!")
                        st.session_state.confirm_clear_all = False
                        st.rerun()
                    else:
                        st.error("❌ Erro ao limpar dados da base PostgreSQL")
        
    except Exception as e:
        error_message = str(e)
        if "SSL connection has been closed unexpectedly" in error_message:
            st.warning("⚠️ Problema temporário de conexão SSL com a base de dados. Tente recarregar a página.")
            if st.button("🔄 Recarregar Página"):
                st.rerun()
        elif "psycopg2.OperationalError" in error_message:
            st.warning("⚠️ Problema de conexão com a base de dados PostgreSQL. Verifique se o sistema está funcionando corretamente.")
            if st.button("🔄 Tentar Novamente"):
                st.rerun()
        else:
            st.error(f"❌ Erro ao carregar histórico: {error_message}")
            if st.button("🔄 Tentar Novamente"):
                st.rerun()

if __name__ == "__main__":
    main()

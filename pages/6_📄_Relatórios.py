"""Página de Relatórios PDF"""
import streamlit as st
from database.db_manager import DatabaseManager
from utils.pdf_reports import PDFReportGenerator
import os

st.set_page_config(page_title="Relatórios", page_icon="📄", layout="wide")
st.title("📄 Relatórios PDF")

if not DatabaseManager.has_data():
    st.warning("⚠️ Nenhum dado encontrado.")
    st.stop()

st.header("📊 Gerar Relatórios")

col1, col2 = st.columns(2)

with col1:
    if st.button("📋 Relatório Completo da Frota", type="primary"):
        with st.spinner("Gerando relatório..."):
            generator = PDFReportGenerator()
            pdf_path = generator.generate_fleet_report()
            
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as file:
                    st.download_button(
                        label="⬇️ Baixar Relatório PDF",
                        data=file.read(),
                        file_name=f"relatorio_frota_{DatabaseManager.get_fleet_summary()['total_vehicles']}_veiculos.pdf",
                        mime="application/pdf"
                    )
                st.success("✅ Relatório gerado com sucesso!")

with col2:
    st.info("📋 **Conteúdo do Relatório:**\n- Resumo executivo\n- Estatísticas da frota\n- Análise por veículo\n- Indicadores de performance")

st.header("📅 Agendamento Automático")
st.info("🚧 Funcionalidade em desenvolvimento: agendamento de relatórios mensais automáticos")
import pandas as pd
import plotly.express as px
import streamlit as st
from config.ai_config import call_ai_service

def render_metrics_dashboard(
    test_cases: list[dict],
    bug_reports: list[dict],
    risk_matrix: list[dict],
    user_stories: list[dict],
):
    st.title("📊 Dashboard de Métricas & Exportação")

    df_tc = pd.DataFrame(test_cases)
    df_bugs = pd.DataFrame(bug_reports)
    df_risks = pd.DataFrame(risk_matrix)
    df_stories = pd.DataFrame(user_stories)

    # ------------------------------------------
    # 1. ANÁLISE DE QUALIDADE COM IA
    # ------------------------------------------
    st.subheader("🤖 Análise Preditiva de Qualidade via IA")
    
    # Inicializa estado da análise no session_state
    if "ai_analysis_result" not in st.session_state:
        st.session_state["ai_analysis_result"] = None

    if st.button("✨ Analisar Saúde da Release com IA", type="primary"):
        with st.spinner("IA consolidando métricas e avaliando os riscos da release..."):
            total_tc = len(df_tc)
            passed = len(df_tc[df_tc["status"] == "Passou"]) if not df_tc.empty and "status" in df_tc.columns else 0
            failed = len(df_tc[df_tc["status"] == "Falhou"]) if not df_tc.empty and "status" in df_tc.columns else 0
            bugs_open = len(df_bugs[df_bugs["status"] == "Aberto"]) if not df_bugs.empty and "status" in df_bugs.columns else 0

            prompt = f"""
            Atue como um QA Lead especialista. Analise estes dados do projeto e faça um resumo executivo sobre os riscos de deploy desta release:

            - Total de Casos de Teste: {total_tc} (Passaram: {passed}, Falharam: {failed})
            - Bugs Abertos: {bugs_open}
            - Histórias de Usuário Cadastradas: {len(df_stories)}

            Forneça:
            1. Parecer de Risco (Baixo, Médio ou Alto).
            2. 3 Principais recomendações para a equipe de QA/Dev antes do Go-Live.
            """
            try:
                res = call_ai_service(prompt)
                st.session_state["ai_analysis_result"] = res
            except Exception as e:
                st.error(f"Erro ao gerar análise da IA: {e}")

    # Exibe a análise se ela tiver sido gerada
    if st.session_state["ai_analysis_result"]:
        st.info(st.session_state["ai_analysis_result"])

    st.divider()

    # ------------------------------------------
    # 2. KPIS E GRÁFICOS
    # ------------------------------------------
    st.subheader("🚀 Indicadores Chave (KPIs)")
    c1, c2, c3 = st.columns(3)
    
    total_tc = len(df_tc)
    c1.metric("Total Casos de Teste", total_tc)
    
    passed_tc = len(df_tc[df_tc["status"] == "Passou"]) if not df_tc.empty and "status" in df_tc.columns else 0
    rate = (passed_tc / total_tc * 100) if total_tc > 0 else 0.0
    c2.metric("Taxa de Sucesso", f"{rate:.1f}%")
    
    bugs_cnt = len(df_bugs)
    c3.metric("Bugs Registrados", bugs_cnt)

    st.markdown("---")
    
    # Gráficos Visuais
    g1, g2 = st.columns(2)
    with g1:
        if not df_tc.empty and "status" in df_tc.columns:
            fig_tc = px.pie(df_tc, names="status", title="Casos de Teste por Status", hole=0.4)
            st.plotly_chart(fig_tc, use_container_width=True)
        else:
            st.info("Sem dados de testes para o gráfico.")

    with g2:
        if not df_bugs.empty and "severity" in df_bugs.columns:
            fig_bugs = px.bar(df_bugs, x="severity", title="Bugs por Severidade", color="severity")
            st.plotly_chart(fig_bugs, use_container_width=True)
        else:
            st.info("Sem dados de bugs para o gráfico.")

    st.divider()

    # ------------------------------------------
    # 3. EXPORTAÇÃO E DOWNLOADS
    # ------------------------------------------
    st.subheader("📥 Exportação de Relatórios")
    
    # Download do Relatório Completo (Métricas + Análise de IA)
    report_text = f"""# Relatório Executivo de QA & Qualidade

## KPIs Gerais
- **Total de Casos de Teste:** {total_tc}
- **Taxa de Sucesso:** {rate:.1f}%
- **Bugs Registrados:** {bugs_cnt}
- **Histórias de Usuário:** {len(df_stories)}

## Avaliação Preditiva da IA
{st.session_state['ai_analysis_result'] or 'Análise de IA ainda não executada.'}
"""

    st.download_button(
        label="📄 Baixar Relatório Executivo Completo (Markdown)",
        data=report_text,
        file_name="relatorio_executivo_qa.md",
        mime="text/markdown",
        use_container_width=True
    )
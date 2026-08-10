import streamlit as st
from modules import auth, projects, requirements, testing, metrics
from config.database import supabase
from config.ai_config import render_ai_provider_selector

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="QA & Requisitos Hub",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# 2. CONTROLE DE AUTENTICAÇÃO
# ==============================================================================
# Renderiza a tela de login/registro se o usuário não estiver autenticado
if not auth.is_authenticated():
    auth.render_auth_page()
    st.stop()  # Interrompe a execução do restante da aplicação

# ==============================================================================
# 3. SIDEBAR (PERFIL, SELEÇÃO DE PROJETO, SELETOR DE IA E NAVEGAÇÃO)
# ==============================================================================
with st.sidebar:
    st.title("🎯 QA Hub")
    
    # Informações do Usuário & Logout
    user_info = auth.get_logged_user()
    st.write(f"👤 **Usuário:** {user_info.get('name', 'Usuário')}")
    st.caption(f"📧 {user_info.get('email', '')}")
    
    if st.button("🚪 Sair / Logout", use_container_width=True):
        auth.logout()
        st.rerun()
        
    st.divider()

    # Seleção do Projeto Ativo
    st.subheader("📌 Projeto Ativo")
    active_project = projects.render_project_selector()

    st.divider()

    # Painel de Seleção do Provedor de IA (Groq, OpenRouter, Gemini ou Auto)
    render_ai_provider_selector()

    st.divider()

    # Menu de Navegação Principal
    st.subheader("🧭 Navegação")
    page = st.radio(
        "Selecione o módulo:",
        options=[
            "📁 Gestão de Projetos",
            "📝 Requisitos",
            "🧪 Módulo de Testes",
            "📊 Métricas & Exportação"
        ],
        index=0
    )

# ==============================================================================
# 4. ROTEAMENTO DE PÁGINAS E VALIDAÇÃO DE CONTEXTO
# ==============================================================================

# Páginas que exigem um projeto ativo selecionado
PROJECT_REQUIRED_PAGES = [
    "📝 Requisitos",
    "🧪 Módulo de Testes",
    "📊 Métricas & Exportação"
]

# Trava de segurança / Tratamento amigável
if page in PROJECT_REQUIRED_PAGES and not active_project:
    st.warning("⚠️ **Nenhum projeto selecionado!**")
    st.info("Por favor, selecione ou crie um projeto no menu lateral (ou no módulo **Gestão de Projetos**) para prosseguir.")
    st.stop()

# Execução do Módulo Selecionado
if page == "📁 Gestão de Projetos":
    projects.render_projects_page()

elif page == "📝 Requisitos":
    requirements.render_requirements_module()

elif page == "🧪 Módulo de Testes":
    # Passa o ID do projeto ativo para o módulo de testes
    testing.render_testing_module(active_project["id"])

elif page == "📊 Métricas & Exportação":
    # Obtém o ID do projeto ativo
    project_id = active_project["id"]
    
    # Busca os dados necessários no Supabase para montar o Dashboard
    try:
        test_cases = supabase.table("test_cases").select("*").eq("project_id", project_id).execute().data or []
        bug_reports = supabase.table("bug_reports").select("*").eq("project_id", project_id).execute().data or []
        risk_matrix = supabase.table("risk_matrix").select("*").eq("project_id", project_id).execute().data or []
        user_stories = supabase.table("user_stories").select("*").eq("project_id", project_id).execute().data or []
    except Exception as e:
        st.error(f"Erro ao carregar métricas do Supabase: {e}")
        test_cases, bug_reports, risk_matrix, user_stories = [], [], [], []

    # Chama o dashboard de métricas com as listas carregadas
    metrics.render_metrics_dashboard(test_cases, bug_reports, risk_matrix, user_stories)
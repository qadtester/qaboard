import streamlit as st
from config.database import supabase

def get_user_projects(team_id: str):
    res = supabase.table("projects").select("*").eq("team_id", team_id).execute()
    return res.data or []

def render_project_selector():
    user_info = st.session_state.get("user")
    if not user_info or "team_id" not in user_info:
        return None

    projects = get_user_projects(user_info["team_id"])
    if not projects:
        st.info("Nenhum projeto encontrado.")
        return None

    project_options = {p["name"]: p for p in projects}
    selected_name = st.selectbox("Selecione o Projeto:", options=list(project_options.keys()))
    
    active_project = project_options[selected_name]
    st.session_state["current_project_id"] = active_project["id"]
    return active_project

def render_projects_page():
    st.title("📁 Gestão de Projetos")
    user_info = st.session_state.get("user")
    if not user_info or "team_id" not in user_info:
        st.error("Usuário sem time vinculado.")
        return

    team_id = user_info["team_id"]
    tab_list, tab_create = st.tabs(["📌 Meus Projetos", "➕ Criar Novo Projeto"])

    with tab_list:
        projects = get_user_projects(team_id)
        if not projects:
            st.info("Nenhum projeto cadastrado ainda.")
        else:
            for proj in projects:
                with st.expander(f"📁 {proj['name']}"):
                    st.write(f"**Descrição:** {proj.get('description', 'Sem descrição')}")
                    st.caption(f"ID: `{proj['id']}`")
                    
                    col_edit, col_del = st.columns(2)
                    
                    # --- EDITAR PROJETO ---
                    with col_edit:
                        with st.popover("✏️ Editar Projeto"):
                            new_name = st.text_input("Novo Nome", value=proj['name'], key=f"edit_p_name_{proj['id']}")
                            new_desc = st.text_area("Nova Descrição", value=proj.get('description', ''), key=f"edit_p_desc_{proj['id']}")
                            if st.button("Salvar Alterações", key=f"btn_save_p_{proj['id']}"):
                                supabase.table("projects").update({"name": new_name, "description": new_desc}).eq("id", proj['id']).execute()
                                st.success("Projeto atualizado!")
                                st.rerun()

                    # --- EXCLUIR PROJETO ---
                    with col_del:
                        with st.popover("🗑️ Excluir Projeto"):
                            st.warning("⚠️ **Atenção:** Esta ação excluirá permanentemente este projeto e TODOS os requisitos, testes e bugs associados a ele!")
                            confirm_text = st.text_input("Digite 'EXCLUIR' para confirmar:", key=f"conf_del_p_{proj['id']}")
                            if st.button("Confirmar Exclusão", type="primary", key=f"btn_del_p_{proj['id']}"):
                                if confirm_text == "EXCLUIR":
                                    supabase.table("projects").delete().eq("id", proj['id']).execute()
                                    if st.session_state.get("current_project_id") == proj['id']:
                                        st.session_state["current_project_id"] = None
                                    st.success("Projeto e seus dados associados foram excluídos com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Palavra de confirmação incorreta.")

    with tab_create:
        with st.form("create_project_form", clear_on_submit=True):
            p_name = st.text_input("Nome do Projeto:")
            p_desc = st.text_area("Descrição do Projeto:")
            if st.form_submit_button("🚀 Criar Projeto"):
                if p_name:
                    supabase.table("projects").insert({"team_id": team_id, "name": p_name, "description": p_desc}).execute()
                    st.success("Projeto criado com sucesso!")
                    st.rerun()
                else:
                    st.error("O nome do projeto é obrigatório.")
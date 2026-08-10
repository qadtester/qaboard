import streamlit as st
from config.database import supabase
from config.ai_config import generate_istqb_content

def render_requirements_module():
    st.header("📋 QA & Requisitos Hub - Gerenciamento de Requisitos")

    project_id = st.session_state.get('current_project_id')
    if not project_id:
        st.warning("Nenhum projeto ativo selecionado.")
        return

    tab_unified, tab_personas, tab_stories = st.tabs([
        "✨ Especificação Completa (IA)", 
        "👤 Personas", 
        "📖 Histórias de Usuário"
    ])

    # ------------------------------------------
    # ABA 0: IA UNIFICADA (PADRÃO ISTQB)
    # ------------------------------------------
    with tab_unified:
        st.subheader("Gerar Persona e User Story Integradas (Padrão ISTQB)")
        context_unificado = st.text_area("Descreva a funcionalidade ou o contexto do sistema:", height=120)

        if st.button("🚀 Gerar Especificação Completa com IA", type="primary"):
            if context_unificado.strip():
                with st.spinner("IA criando Persona e User Story no padrão ISTQB..."):
                    data = generate_istqb_content("user_story", context_unificado)
                    
                    if data and isinstance(data, dict):
                        p_data = data.get("persona", {})
                        supabase.table('personas').insert({
                            "project_id": project_id, 
                            "name": p_data.get("name"), 
                            "role": p_data.get("role"),
                            "goals": p_data.get("goals"), 
                            "pain_points": p_data.get("pain_points"), 
                            "generated_by_ai": True
                        }).execute()

                        us_data = data.get("user_story", {})
                        
                        # Limpa repetições de prefixos caso a IA tenha enviado
                        as_a = us_data.get("as_a", "").replace("Como um ", "").replace("Como uma ", "").strip()
                        i_want = us_data.get("i_want_to", "").replace("Eu quero ", "").replace("eu quero ", "").strip()
                        so_that = us_data.get("so_that", "").replace("Para que ", "").replace("para que ", "").strip()

                        supabase.table('user_stories').insert({
                            "project_id": project_id, 
                            "title": us_data.get("title"), 
                            "as_a": as_a,
                            "i_want_to": i_want, 
                            "so_that": so_that,
                            "acceptance_criteria": us_data.get("acceptance_criteria"), 
                            "generated_by_ai": True
                        }).execute()

                        st.success("Gerados e salvos no padrão ISTQB com sucesso!")
                        st.rerun()
                    else:
                        st.error("Falha ao gerar os requisitos. Tente novamente.")

    # ------------------------------------------
    # ABA 1: PERSONAS
    # ------------------------------------------
    with tab_personas:
        st.subheader("Personas do Projeto")
        with st.form("form_persona_manual", clear_on_submit=True):
            name = st.text_input("Nome:")
            role = st.text_input("Papel / Função:")
            goals = st.text_area("Objetivos:")
            pain_points = st.text_area("Dores:")
            if st.form_submit_button("Salvar Persona"):
                supabase.table('personas').insert({
                    "project_id": project_id, "name": name, "role": role, "goals": goals, "pain_points": pain_points, "generated_by_ai": False
                }).execute()
                st.rerun()

        st.divider()
        personas = supabase.table('personas').select('*').eq('project_id', project_id).execute().data or []
        for p in personas:
            badge = "🤖 IA" if p.get('generated_by_ai') else "✍️ Manual"
            with st.expander(f"👤 {p['name']} - {p['role']} [{badge}]"):
                st.markdown(f"**🎯 Objetivos:**\n{p.get('goals') or 'N/A'}")
                st.markdown(f"**⚡ Dores / Frustrações:**\n{p.get('pain_points') or 'N/A'}")
                
                c_edit, c_del = st.columns(2)
                with c_edit:
                    with st.popover("✏️ Editar Persona"):
                        e_name = st.text_input("Nome", value=p['name'], key=f"e_p_name_{p['id']}")
                        e_role = st.text_input("Papel", value=p['role'], key=f"e_p_role_{p['id']}")
                        e_goals = st.text_area("Objetivos", value=p.get('goals', ''), key=f"e_p_goals_{p['id']}")
                        e_pain = st.text_area("Dores", value=p.get('pain_points', ''), key=f"e_p_pain_{p['id']}")
                        if st.button("Salvar Alterações", key=f"btn_p_edit_{p['id']}"):
                            supabase.table('personas').update({"name": e_name, "role": e_role, "goals": e_goals, "pain_points": e_pain}).eq('id', p['id']).execute()
                            st.rerun()
                with c_del:
                    if st.button("🗑️ Excluir Persona", key=f"btn_p_del_{p['id']}", type="primary"):
                        supabase.table('personas').delete().eq('id', p['id']).execute()
                        st.rerun()

    # ------------------------------------------
    # ABA 2: HISTÓRIAS DE USUÁRIO
    # ------------------------------------------
    with tab_stories:
        st.subheader("Histórias de Usuário")
        with st.form("form_us_manual", clear_on_submit=True):
            title = st.text_input("Título:")
            as_a = st.text_input("Como um(a)...")
            i_want_to = st.text_input("Eu quero...")
            so_that = st.text_input("Para que...")
            acceptance_criteria = st.text_area("Critérios de Aceite (Dado que... Quando... Então...):")
            if st.form_submit_button("Salvar User Story"):
                supabase.table('user_stories').insert({
                    "project_id": project_id, "title": title, "as_a": as_a, "i_want_to": i_want_to, "so_that": so_that, "acceptance_criteria": acceptance_criteria, "generated_by_ai": False
                }).execute()
                st.rerun()

        st.divider()
        stories = supabase.table('user_stories').select('*').eq('project_id', project_id).execute().data or []
        for us in stories:
            badge = "🤖 IA" if us.get('generated_by_ai') else "✍️ Manual"
            with st.expander(f"📌 {us.get('title')} [{badge}]"):
                # Exibição estruturada e separada por tópicos
                st.markdown(f"**👤 Como um(a):** {us.get('as_a')}")
                st.markdown(f"**🎯 Eu quero:** {us.get('i_want_to')}")
                st.markdown(f"**💡 Para que:** {us.get('so_that')}")
                
                st.markdown("---")
                st.markdown("**✅ Critérios de Aceite (BDD):**")
                
                # Trata as quebras de linha e formatação do BDD em negrito por linha
                crit = us.get('acceptance_criteria', 'Sem critérios.')
                if isinstance(crit, str) and crit.strip():
                    formatted = crit
                    
                    # 1. Garante quebras de linha antes de cada palavra-chave BDD
                    keywords = [
                        ("Dado que ", "\n\n**Dado que** "),
                        ("dado que ", "\n\n**Dado que** "),
                        (" Quando ", "\n**Quando** "),
                        (" quando ", "\n**Quando** "),
                        (" Então ", "\n**Então** "),
                        (" então ", "\n**Então** "),
                        (" E ", "\n**E** "),
                        (" e ", "\n**E** ")
                    ]
                    
                    for old, new in keywords:
                        formatted = formatted.replace(old, new)
                    
                    # 2. Garante formatação inicial se começar direto com Dado que/Quando/Então sem espaço
                    if formatted.startswith("Dado que"):
                        formatted = formatted.replace("Dado que", "**Dado que**", 1)
                    elif formatted.startswith("Quando"):
                        formatted = formatted.replace("Quando", "**Quando**", 1)
                    elif formatted.startswith("Então"):
                        formatted = formatted.replace("Então", "**Então**", 1)

                    st.markdown(formatted.strip())
                else:
                    st.write(crit)

                c_edit, c_del = st.columns(2)
                with c_edit:
                    with st.popover("✏️ Editar User Story"):
                        e_title = st.text_input("Título", value=us['title'], key=f"e_us_t_{us['id']}")
                        e_as_a = st.text_input("Como um", value=us.get('as_a', ''), key=f"e_us_a_{us['id']}")
                        e_want = st.text_input("Eu quero", value=us.get('i_want_to', ''), key=f"e_us_w_{us['id']}")
                        e_so = st.text_input("Para que", value=us.get('so_that', ''), key=f"e_us_s_{us['id']}")
                        e_crit = st.text_area("Critérios de Aceite", value=us.get('acceptance_criteria', ''), key=f"e_us_c_{us['id']}")
                        if st.button("Salvar Alterações", key=f"btn_us_edit_{us['id']}"):
                            supabase.table('user_stories').update({
                                "title": e_title, "as_a": e_as_a, "i_want_to": e_want, "so_that": e_so, "acceptance_criteria": e_crit
                            }).eq('id', us['id']).execute()
                            st.rerun()
                with c_del:
                    if st.button("🗑️ Excluir User Story", key=f"btn_us_del_{us['id']}", type="primary"):
                        supabase.table('user_stories').delete().eq('id', us['id']).execute()
                        st.rerun()

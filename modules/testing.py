import streamlit as st
from config.database import supabase
from config.ai_config import generate_istqb_content

# ==========================================
# ABA 1: CASOS DE TESTE (ISTQB)
# ==========================================

def render_test_cases_tab(project_id: str):
    st.subheader("📋 Gestão e Execução de Casos de Teste")
    
    with st.expander("➕ Criar Novo Caso de Teste", expanded=False):
        mode = st.radio("Modo de Criação", ["Sem IA (Manual)", "Com IA (Automático)"], horizontal=True)
        test_type = st.selectbox("Tipo de Teste", ["Funcional", "Regressão", "Smoke", "Não-Funcional"])
        
        if mode == "Com IA (Automático)":
            user_story = st.text_area("História de Usuário ou Funcionalidade:", placeholder="Como usuário...")
            if st.button("✨ Gerar e Salvar Caso de Teste via IA", type="primary"):
                if user_story:
                    with st.spinner("IA gerando caso de teste no padrão ISTQB..."):
                        # Chama a geração usando as regras do ISTQB
                        data = generate_istqb_content("test_case", f"Tipo de Teste: {test_type}. Contexto: {user_story}")
                        
                        if data and isinstance(data, dict):
                            payload = {
                                "project_id": project_id, 
                                "type": test_type, 
                                "test_type": test_type,
                                "title": data.get("title"), 
                                "preconditions": data.get("preconditions"),
                                "steps": data.get("steps"), 
                                "expected_result": data.get("expected_result"),
                                "status": "Não Executado", 
                                "gerado_por_ia": True
                            }
                            supabase.table("test_cases").insert(payload).execute()
                            st.success("Caso de teste ISTQB salvo com sucesso!")
                            st.rerun()
                        else:
                            st.error("Falha ao gerar o caso de teste. Tente novamente.")
        else:
            with st.form("manual_tc_form", clear_on_submit=True):
                title = st.text_input("Título do Caso de Teste")
                preconditions = st.text_area("Pré-condições")
                steps = st.text_area("Passos")
                expected_result = st.text_area("Resultado Esperado")
                if st.form_submit_button("💾 Salvar Caso de Teste"):
                    payload = {
                        "project_id": project_id, "type": test_type, "test_type": test_type,
                        "title": title, "preconditions": preconditions, "steps": steps,
                        "expected_result": expected_result, "status": "Não Executado", "gerado_por_ia": False
                    }
                    supabase.table("test_cases").insert(payload).execute()
                    st.success("Salvo com sucesso!")
                    st.rerun()

    st.divider()
    
    # --- FILTRO E LISTAGEM EXPANSÍVEL ---
    st.markdown("### Suíte de Testes")
    filter_type = st.selectbox("Filtrar por Tipo:", ["Todos", "Funcional", "Regressão", "Smoke", "Não-Funcional"])
    
    query = supabase.table("test_cases").select("*").eq("project_id", project_id)
    if filter_type != "Todos":
        query = query.eq("type", filter_type)
    
    test_cases = query.execute().data or []
        
    if not test_cases:
        st.info("Nenhum caso de teste encontrado.")
    else:
        for tc in test_cases:
            badge_ia = "🤖 IA" if tc.get("gerado_por_ia") else "✍️ Manual"
            status = tc.get("status", "Não Executado")
            status_icon = "🟢" if status == "Passou" else ("🔴" if status == "Falhou" else ("🟡" if status == "Bloqueado" else "⚪"))

            with st.expander(f"{status_icon} [{tc.get('type', 'Teste')}] {tc.get('title')} ({badge_ia})"):
                col_det, col_act = st.columns([3, 1])
                
                with col_det:
                    st.markdown(f"**Pré-condições:** {tc.get('preconditions') or 'N/A'}")
                    st.markdown(f"**Passos:**\n\n{tc.get('steps') or 'N/A'}")
                    st.markdown(f"**Resultado Esperado:**\n\n{tc.get('expected_result') or 'N/A'}")
                    
                    st.divider()
                    c_edit, c_del = st.columns(2)
                    
                    # EDITAR CASO DE TESTE
                    with c_edit:
                        with st.popover("✏️ Editar Caso de Teste"):
                            e_title = st.text_input("Título", value=tc['title'], key=f"e_tc_t_{tc['id']}")
                            e_pre = st.text_area("Pré-condições", value=tc.get('preconditions', ''), key=f"e_tc_p_{tc['id']}")
                            e_steps = st.text_area("Passos", value=tc.get('steps', ''), key=f"e_tc_s_{tc['id']}")
                            e_exp = st.text_area("Esperado", value=tc.get('expected_result', ''), key=f"e_tc_e_{tc['id']}")
                            if st.button("Salvar Alterações", key=f"btn_tc_edit_{tc['id']}"):
                                supabase.table("test_cases").update({
                                    "title": e_title, "preconditions": e_pre, "steps": e_steps, "expected_result": e_exp
                                }).eq('id', tc['id']).execute()
                                st.rerun()
                    
                    # EXCLUIR CASO DE TESTE
                    with c_del:
                        if st.button("🗑️ Excluir Caso de Teste", key=f"btn_tc_del_{tc['id']}", type="primary"):
                            supabase.table("test_cases").delete().eq('id', tc['id']).execute()
                            st.rerun()

                with col_act:
                    st.write(f"**Status:** {status}")
                    st.write("**Atualizar:**")
                    if st.button("🟢 Passou", key=f"p_{tc['id']}", use_container_width=True):
                        supabase.table("test_cases").update({"status": "Passou"}).eq("id", tc['id']).execute()
                        st.rerun()
                    if st.button("🔴 Falhou", key=f"f_{tc['id']}", use_container_width=True):
                        supabase.table("test_cases").update({"status": "Falhou"}).eq("id", tc['id']).execute()
                        st.rerun()
                    if st.button("🟡 Bloqueado", key=f"b_{tc['id']}", use_container_width=True):
                        supabase.table("test_cases").update({"status": "Bloqueado"}).eq("id", tc['id']).execute()
                        st.rerun()

# ==========================================
# ABA 2: BUG REPORTS (ISTQB / IEEE 829)
# ==========================================

def render_bug_reports_tab(project_id: str):
    st.subheader("🐛 Registro e Gestão de Bugs")
    
    with st.expander("🚨 Registrar Novo Bug", expanded=False):
        bug_mode = st.radio("Modo de Registro:", ["Sem IA (Manual)", "Com IA (Automático)"], horizontal=True)
        
        if bug_mode == "Com IA (Automático)":
            raw_bug = st.text_area("Descreva o problema encontrado:")
            if st.button("✨ Gerar e Salvar Bug Report via IA", type="primary"):
                if raw_bug:
                    with st.spinner("IA criando o Bug Report no padrão ISTQB..."):
                        # Chama a geração usando o schema de Bug Report do ISTQB
                        data = generate_istqb_content("bug_report", raw_bug)
                        
                        if data and isinstance(data, dict):
                            steps_content = data.get("steps_to_reproduce") or ""
                            payload = {
                                "project_id": project_id, 
                                "title": data.get("title"), 
                                "severity": data.get("severity", "Média"),
                                "steps": steps_content, 
                                "steps_to_reproduce": steps_content,
                                "expected_behavior": data.get("expected_behavior"), 
                                "actual_behavior": data.get("actual_behavior"),
                                "status": "Aberto", 
                                "gerado_por_ia": True
                            }
                            supabase.table("bug_reports").insert(payload).execute()
                            st.success("Bug ISTQB registrado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Falha ao gerar o bug report. Tente novamente.")
        else:
            with st.form("bug_report_form", clear_on_submit=True):
                title = st.text_input("Título do Bug")
                severity = st.selectbox("Severidade", ["Baixa", "Média", "Alta", "Crítica"])
                steps = st.text_area("Passos para Reproduzir")
                expected_behavior = st.text_area("Comportamento Esperado")
                actual_behavior = st.text_area("Comportamento Atual")
                if st.form_submit_button("🚨 Registrar Bug"):
                    payload = {
                        "project_id": project_id, "title": title, "severity": severity,
                        "steps": steps, "steps_to_reproduce": steps,
                        "expected_behavior": expected_behavior, "actual_behavior": actual_behavior,
                        "status": "Aberto", "gerado_por_ia": False
                    }
                    supabase.table("bug_reports").insert(payload).execute()
                    st.success("Bug registrado!")
                    st.rerun()

    st.divider()
    bugs = supabase.table("bug_reports").select("*").eq("project_id", project_id).execute().data or []
    
    if not bugs:
        st.info("Nenhum bug registrado.")
    else:
        for bug in bugs:
            badge_ia = "🤖 IA" if bug.get("gerado_por_ia") else "✍️ Manual"
            sev = bug.get("severity", "Média")
            sev_color = "🔴" if sev in ["Alta", "Crítica"] else ("🟡" if sev == "Média" else "🟢")
            
            with st.expander(f"{sev_color} [{sev}] {bug.get('title')} ({badge_ia})"):
                st.markdown(f"**Status Atual:** `{bug.get('status', 'Aberto')}`")
                st.markdown(f"**Passos:**\n\n{bug.get('steps') or bug.get('steps_to_reproduce') or 'N/A'}")
                st.markdown(f"**Esperado:** {bug.get('expected_behavior') or 'N/A'}")
                st.markdown(f"**Atual:** {bug.get('actual_behavior') or 'N/A'}")
                
                st.divider()
                c_edit, c_del = st.columns(2)
                
                # EDITAR BUG
                with c_edit:
                    with st.popover("✏️ Editar Bug"):
                        e_title = st.text_input("Título", value=bug['title'], key=f"e_b_t_{bug['id']}")
                        e_sev = st.selectbox("Severidade", ["Baixa", "Média", "Alta", "Crítica"], index=["Baixa", "Média", "Alta", "Crítica"].index(sev) if sev in ["Baixa", "Média", "Alta", "Crítica"] else 1, key=f"e_b_s_{bug['id']}")
                        e_steps = st.text_area("Passos", value=bug.get('steps', ''), key=f"e_b_st_{bug['id']}")
                        e_exp = st.text_area("Esperado", value=bug.get('expected_behavior', ''), key=f"e_b_ex_{bug['id']}")
                        e_act = st.text_area("Atual", value=bug.get('actual_behavior', ''), key=f"e_b_ac_{bug['id']}")
                        if st.button("Salvar Alterações", key=f"btn_bug_edit_{bug['id']}"):
                            supabase.table("bug_reports").update({
                                "title": e_title, "severity": e_sev, "steps": e_steps, "steps_to_reproduce": e_steps,
                                "expected_behavior": e_exp, "actual_behavior": e_act
                            }).eq('id', bug['id']).execute()
                            st.rerun()
                
                # EXCLUIR BUG
                with c_del:
                    if st.button("🗑️ Excluir Bug", key=f"btn_bug_del_{bug['id']}", type="primary"):
                        supabase.table("bug_reports").delete().eq('id', bug['id']).execute()
                        st.rerun()

def render_testing_module(project_id: str):
    if not project_id:
        st.warning("Selecione um projeto para acessar o Módulo de Testes.")
        return

    st.title("🧪 Módulo de Testes & Qualidade")
    tab1, tab2 = st.tabs(["Casos de Teste & Execução", "Bug Reports"])
    with tab1:
        render_test_cases_tab(project_id)
    with tab2:
        render_bug_reports_tab(project_id)
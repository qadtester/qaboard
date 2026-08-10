import streamlit as st
import hashlib
from config.database import supabase


def hash_password(password: str) -> str:
    """Gera um hash SHA-256 para a senha."""
    return hashlib.sha256(password.encode()).hexdigest()


def logout():
    """Limpa os dados do usuário da sessão e reinicia a aplicação."""
    st.session_state["user"] = None
    st.session_state["team_id"] = None
    st.session_state["logged_in"] = False
    st.rerun()


def render_auth_page():
    """Exibe a interface gráfica de autenticação (Login e Cadastro)."""
    st.title("🔐 QA & Requisitos Hub")

    # Inicialização do estado da sessão
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "team_id" not in st.session_state:
        st.session_state["team_id"] = None

    # Se já estiver logado, exibe mensagem e botão de logout
    if st.session_state["logged_in"]:
        st.success(f"Bem-vindo(a), {st.session_state['user']['name']}!")
        if st.button("Sair / Logout"):
            logout()
        return

    # Abas de Login e Cadastro
    tab_login, tab_register = st.tabs(["🔑 Login", "➕ Criar Conta / Equipe"])

    # -------------------------------------------------------------------------
    # TAB 1: LOGIN
    # -------------------------------------------------------------------------
    with tab_login:
        st.subheader("Acessar sua Conta")
        
        email = st.text_input("E-mail", key="login_email")
        password = st.text_input("Senha", type="password", key="login_password")

        if st.button("Entrar", type="primary"):
            if not email or not password:
                st.warning("Por favor, preencha todos os campos.")
            else:
                hashed_pw = hash_password(password)

                try:
                    # Consulta o usuário no Supabase
                    response = (
                        supabase.table("users")
                        .select("*, teams(name)")
                        .eq("email", email)
                        .eq("password_hash", hashed_pw)
                        .execute()
                    )

                    if response.data and len(response.data) > 0:
                        user_data = response.data[0]

                        # Armazena as informações na sessão
                        st.session_state["logged_in"] = True
                        st.session_state["user"] = user_data
                        st.session_state["team_id"] = user_data["team_id"]

                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")

                except Exception as e:
                    st.error(f"Erro ao conectar com o banco de dados: {str(e)}")

    # -------------------------------------------------------------------------
    # TAB 2: CRIAR CONTA / EQUIPE
    # -------------------------------------------------------------------------
    with tab_register:
        st.subheader("Nova Conta e Equipe")

        team_option = st.radio(
            "Vincular Equipe:", 
            ["Criar Nova Equipe", "Entrar em Equipe Existente"]
        )

        team_id_to_assign = None

        if team_option == "Criar Nova Equipe":
            new_team_name = st.text_input("Nome da Nova Equipe")
        else:
            # Busca as equipes existentes para seleção
            try:
                teams_response = supabase.table("teams").select("id, name").execute()
                teams_list = teams_response.data or []
                
                if teams_list:
                    team_map = {t["name"]: t["id"] for t in teams_list}
                    selected_team_name = st.selectbox("Selecione a Equipe", list(team_map.keys()))
                    team_id_to_assign = team_map[selected_team_name]
                else:
                    st.warning("Nenhuma equipe encontrada. Crie uma nova equipe.")
            except Exception as e:
                st.error(f"Erro ao buscar equipes: {str(e)}")

        st.divider()

        user_name = st.text_input("Seu Nome")
        user_email = st.text_input("Seu E-mail")
        user_password = st.text_input("Sua Senha", type="password", key="reg_password")
        user_role = st.selectbox("Cargo / Função", ["QA Engineer", "Product Owner", "Desenvolvedor", "Líder Técnico"])

        if st.button("Cadastrar", type="primary"):
            if not user_name or not user_email or not user_password:
                st.warning("Por favor, preencha todos os campos obrigatórios.")
            else:
                try:
                    # 1. Trata a criação/associação da equipe
                    if team_option == "Criar Nova Equipe":
                        if not new_team_name:
                            st.warning("Por favor, informe o nome da nova equipe.")
                            st.stop()
                        
                        # Insere a nova equipe no Supabase
                        team_response = (
                            supabase.table("teams")
                            .insert({"name": new_team_name})
                            .execute()
                        )
                        if team_response.data:
                            team_id_to_assign = team_response.data[0]["id"]
                        else:
                            st.error("Erro ao criar equipe.")
                            st.stop()

                    if not team_id_to_assign:
                        st.error("Equipe não identificada. Verifique os dados.")
                        st.stop()

                    # 2. Cria o novo usuário com o hash da senha
                    hashed_pw = hash_password(user_password)
                    new_user_payload = {
                        "team_id": team_id_to_assign,
                        "name": user_name,
                        "email": user_email,
                        "password_hash": hashed_pw,
                        "role": user_role,
                    }

                    user_response = (
                        supabase.table("users")
                        .insert(new_user_payload)
                        .execute()
                    )

                    if user_response.data:
                        st.success("Conta criada com sucesso! Faça o login na aba ao lado.")
                    else:
                        st.error("Não foi possível criar o usuário.")

                except Exception as e:
                    st.error(f"Erro ao realizar cadastro: {str(e)}")

def is_authenticated() -> bool:
    """Verifica se existe um usuário autenticado na sessão do Streamlit."""
    return st.session_state.get("logged_in", False) and st.session_state.get("user") is not None

def get_logged_user():
    """Retorna o dicionário com os dados do usuário logado na sessão ou None."""
    return st.session_state.get("user", None)
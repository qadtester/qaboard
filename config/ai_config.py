import os
# import re
import json
from typing import Optional, Dict, Any, Union
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# ------------------------------------------------------------------------------
# MODELOS GRATUITOS DISPONÍVEIS (REORDENADOS COM OS MELHORES NO TOPO)
# ------------------------------------------------------------------------------
FREE_MODELS = {
    "groq": [
        "llama-3.3-70b-versatile",    # 🏆 Melhor performance geral e raciocínio
        "llama-3.1-8b-instant",       # Ultra rápido
        "qwen/qwen3.6-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b"
    ],
    "openrouter": [
        "google/gemma-4-31b:free",       # 🏆 Excelente para JSON estrito e BDD
        "google/gemma-4-26b-a4b:free",   # Excelente alternativa leve
        "nvidia/nemotron-nano-9b-v2:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "nvidia/nemotron-3-ultra:free",
        "poolside/laguna-s-2.1:free",
        "nvidia/nemotron-3-super:free",
        "cohere/north-mini-code:free",
        "poolside/laguna-xs-2.1:free",
        "inclusionai/ling-3.0-tiny:free",
        "nvidia/nemotron-3-nano-omni:free",
        "openai/gpt-oss-20b:free",
        "nvidia/nemotron-nano-12b-2-vl:free"
    ],
    "gemini": [
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]
}

# ------------------------------------------------------------------------------
# LÓGICA DE SEGURANÇA E LEITURA HÍBRIDA (.ENV + ST.SECRETS)
# ------------------------------------------------------------------------------

def _get_secret_or_env(key: str) -> Optional[str]:
    """
    Busca a chave de forma segura:
    1. Tenta no arquivo .env (Local)
    2. Se não encontrar, tenta no st.secrets (Streamlit Cloud) sem estourar erro localmente.
    """
    val = os.getenv(key)
    if val:
        return val

    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass  # Evita o StreamlitSecretNotFoundError ao rodar sem secrets.toml local

    return None


def is_admin_user() -> bool:
    """Verifica se o usuário logado atualmente é o Administrador do sistema."""
    user_info = st.session_state.get("user", {})
    logged_email = user_info.get("email", "").strip().lower()
    admin_email = (_get_secret_or_env("ADMIN_EMAIL") or "").strip().lower()
    
    return bool(logged_email and admin_email and logged_email == admin_email)


def get_active_api_key(provider: str) -> Optional[str]:
    """
    Recupera a chave de API respeitando as regras de isolamento:
    1. Tenta buscar a chave individual informada pelo usuário na UI.
    2. Se não houver chave na UI, verifica se é o ADMIN. Apenas o ADMIN acessa as chaves salvas.
    """
    user_keys = st.session_state.get("user_api_keys", {})
    user_provided_key = user_keys.get(provider)

    # 1. Chave digitada temporariamente pelo próprio usuário na UI
    if user_provided_key:
        return user_provided_key

    # 2. Se for o USUÁRIO ADMINISTRADOR, libera as chaves globais salvas no .env ou st.secrets
    if is_admin_user():
        if provider == "groq":
            return _get_secret_or_env("GROQ_API_KEY")
        elif provider == "openrouter":
            return _get_secret_or_env("OPENROUTER_API_KEY")
        elif provider == "gemini":
            return _get_secret_or_env("GEMINI_API_KEY")

    # 3. Usuários comuns sem chave digitada -> Retorna None (Execução via IA desabilitada)
    return None

# ------------------------------------------------------------------------------
# INTERFACE: PAINEL DE CONFIGURAÇÃO NA SIDEBAR
# ------------------------------------------------------------------------------

def render_ai_provider_selector():
    """Renderiza o seletor de IA, modelos e a gestão de chaves na barra lateral."""
    st.subheader("🤖 Configuração de IA")

    if "user_api_keys" not in st.session_state:
        st.session_state["user_api_keys"] = {}

    options = {
        "⚡ Automático (Fallback)": "auto",
        "🚀 Groq": "groq",
        "🌐 OpenRouter": "openrouter",
        "✨ Google Gemini": "gemini"
    }

    selected_label = st.selectbox("Provedor de IA:", options=list(options.keys()), index=0)
    provider = options[selected_label]
    st.session_state["selected_ai_provider"] = provider

    # 💡 AJUSTE INTELIGENTE DO MODO AUTOMÁTICO
    if provider == "auto":
        # Identifica qual chave está disponível para direcionar a lista de modelos na UI
        active_p = None
        for p in ["groq", "openrouter", "gemini"]:
            if get_active_api_key(p):
                active_p = p
                break
        
        # Se nenhuma chave for encontrada, usa a lista do OpenRouter por padrão
        target_provider = active_p if active_p else "openrouter"
        available_models = FREE_MODELS.get(target_provider, [])
        
        selected_model = st.sidebar.selectbox(
            "Modelo Inicial (Fallback):",
            options=available_models,
            index=0,
            help="O sistema usará este modelo como ponto de partida. Se falhar, usará as alternativas."
        )
        st.session_state["selected_ai_model"] = selected_model
        
        if active_p:
            st.caption(f"ℹ️ *Fallback ativo usando `{active_p.upper()}` (`{selected_model}`).*")
        else:
            st.caption("⚠️ *Insira uma chave de API para ativar a IA.*")

    elif provider in FREE_MODELS:
        available_models = FREE_MODELS[provider]
        selected_model = st.selectbox(
            "Modelo Disponível:",
            options=available_models,
            index=0,
            help="Modelos com cota gratuita disponíveis neste provedor."
        )
        st.session_state["selected_ai_model"] = selected_model
    else:
        st.session_state["selected_ai_model"] = None

    # Badge de identificação do perfil de acesso
    if is_admin_user():
        st.caption("👑 **Perfil Admin:** Suas chaves salvas (.env / Secrets) estão ativas.")
    else:
        st.caption("👤 **Perfil Usuário:** Insira sua chave de API pessoal para usar a IA.")

    # Popover para inclusão de chave pessoal
    with st.popover("🔑 Minhas Chaves de API"):
        st.caption("Insira suas chaves para usar as funções de IA. Elas ficam salvas temporariamente apenas na sessão do seu navegador.")
        
        for p_key, p_name in [("groq", "Groq"), ("openrouter", "OpenRouter"), ("gemini", "Gemini")]:
            current_val = st.session_state["user_api_keys"].get(p_key, "")
            new_val = st.text_input(f"Chave {p_name}:", value=current_val, type="password", key=f"input_key_{p_key}")
            if new_val != current_val:
                st.session_state["user_api_keys"][p_key] = new_val.strip()
                st.toast(f"Chave do {p_name} atualizada!")
                st.rerun()

# ------------------------------------------------------------------------------
# EXECUTOR DE IA
# ------------------------------------------------------------------------------

def generate_ai_content(
    prompt: str, 
    provider: Optional[str] = None, 
    model_name: Optional[str] = None
) -> Optional[str]:
    """Gera conteúdo via IA usando exclusivamente a chave autorizada e o modelo selecionado."""
    
    if provider is None:
        provider = st.session_state.get("selected_ai_provider", "auto")

    if model_name is None:
        model_name = st.session_state.get("selected_ai_model")

    # 1. EXECUÇÃO VIA GROQ
    if provider == "groq":
        key = get_active_api_key("groq")
        if not key:
            st.warning("⚠️ Nenhuma chave do Groq configurada. Insira sua chave no menu lateral para usar a IA.")
            return None
        try:
            client = Groq(api_key=key)
            target_model = model_name or FREE_MODELS["groq"][0]
            res = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=target_model,
                response_format={"type": "json_object"} if "JSON" in prompt or "json" in prompt else None
            )
            return res.choices[0].message.content
        except Exception as e:
            st.error(f"Erro no Groq ({model_name}): {e}")
            return None

    # 2. EXECUÇÃO VIA OPENROUTER
    elif provider == "openrouter":
        key = get_active_api_key("openrouter")
        if not key:
            st.warning("⚠️ Nenhuma chave do OpenRouter configurada. Insira sua chave no menu lateral para usar a IA.")
            return None
        try:
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
            target_model = model_name or FREE_MODELS["openrouter"][0]
            res = client.chat.completions.create(
                model=target_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return res.choices[0].message.content
        except Exception as e:
            st.error(f"Erro no OpenRouter ({model_name}): {e}")
            return None

    # 3. EXECUÇÃO VIA GEMINI
    elif provider == "gemini":
        key = get_active_api_key("gemini")
        if not key:
            st.warning("⚠️ Nenhuma chave do Gemini configurada. Insira sua chave no menu lateral para usar a IA.")
            return None
        try:
            genai.configure(api_key=key)
            target_model = model_name or FREE_MODELS["gemini"][0]
            model = genai.GenerativeModel(target_model)
            res = model.generate_content(prompt)
            return res.text if res else None
        except Exception as e:
            st.error(f"Erro no Gemini ({model_name}): {e}")
            return None

    # 4. MODO AUTOMÁTICO (FALLBACK INTELIGENTE)
    elif provider == "auto":
        # Fila de tentativa de provedores respeitando o modelo selecionado pelo usuário quando aplicável
        fallback_order = ["groq", "openrouter", "gemini"]
        
        for p in fallback_order:
            if get_active_api_key(p):
                # Se o provedor ativo bater com o que foi configurado na UI, usa o modelo selecionado pelo usuário
                chosen_m = model_name if model_name in FREE_MODELS.get(p, []) else FREE_MODELS[p][0]
                output = generate_ai_content(prompt, provider=p, model_name=chosen_m)
                if output:
                    return output

        st.warning("⚠️ Você precisa cadastrar ao menos uma Chave de API no menu lateral para gerar conteúdos via IA.")
        return None

call_ai_service = generate_ai_content

# ------------------------------------------------------------------------------
# PARSER DE JSON E MOTOR DE REGRAS ISTQB
# ------------------------------------------------------------------------------

def parse_ai_json(raw_text: str) -> Optional[Union[Dict[str, Any], list]]:
    """
    Trata respostas de IA para converter em JSON válido com segurança.
    Fatia o texto direto do primeiro '{' ou '[' até o último '}' ou ']'.
    """
    if not raw_text:
        return None

    texto = raw_text.strip()

    # Pega o primeiro índice de abertura ({ ou [)
    indices_inicio = [i for i in [texto.find('{'), texto.find('[')] if i != -1]
    # Pega o último índice de fechamento (} ou ])
    indices_fim = [texto.rfind('}'), texto.rfind(']')]

    if not indices_inicio:
        return None

    start_idx = min(indices_inicio)
    end_idx = max(indices_fim)

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        texto = texto[start_idx:end_idx + 1]

    try:
        return json.loads(texto)
    except Exception as e:
        st.error(f"⚠️ Erro ao converter resposta da IA em JSON válido: {e}")
        return None


# SCHEMAS ISTQB DE QUALIDADE
ISTQB_SCHEMAS = {
    "test_case": """
    REGRAS DE RESPOSTA (ISTQB):
    Responda EXCLUSIVAMENTE com um JSON estrito contendo:
    {
      "title": "Título objetivo e direto",
      "type": "Funcional | Regressão | Smoke",
      "preconditions": "Pré-condições necessárias para o teste",
      "test_data": "Dados de entrada necessários",
      "steps": "1. Passo um\\n2. Passo dois",
      "expected_result": "Comportamento esperado do sistema"
    }
    """,
    "bug_report": """
    REGRAS DE RESPOSTA (ISTQB / IEEE 829):
    Responda EXCLUSIVAMENTE com um JSON estrito contendo:
    {
      "title": "[Módulo] Resumo do problema",
      "severity": "Baixa | Média | Alta | Crítica",
      "environment": "Ambiente onde ocorreu o defeito",
      "steps_to_reproduce": "1. Passo um\\n2. Passo dois",
      "expected_behavior": "Comportamento correto esperado",
      "actual_behavior": "Comportamento incorreto observado"
    }
    """,
    "user_story": """
    REGRAS DE RESPOSTA (ISTQB):
    Responda EXCLUSIVAMENTE com um JSON estrito contendo:
    {
      "persona": {
        "name": "Nome da persona",
        "role": "Papel/Cargo no sistema",
        "goals": "Objetivo principal resumido",
        "pain_points": "Frustração ou dor principal"
      },
      "user_story": {
        "title": "Título resumido da funcionalidade",
        "as_a": "Apenas a persona/papel (Ex: Compradora online)",
        "i_want_to": "Apenas a ação desejada (Ex: Efetuar pagamento via chave Pix cadastrada)",
        "so_that": "Apenas o benefício (Ex: Concluir a compra rapidamente sem digitar dados)",
        "acceptance_criteria": "Dado que a chave Pix está cadastrada...\\nQuando eu selecionar a opção Pix...\\nEntão o pagamento é processado.\\n\\nDado que a chave não está cadastrada...\\nQuando acessar o checkout...\\nEntão a opção Pix não é exibida."
      }
    }
    ATENÇÃO: Nos campos 'as_a', 'i_want_to' e 'so_that', NÃO inclua os prefixos 'Como um', 'Eu quero' ou 'Para que'. Escreva apenas o texto complementar.
    """
}


def generate_istqb_content(entity_type: str, user_context: str) -> Optional[Union[Dict[str, Any], list]]:
    """
    Função genérica para criar documentos de QA (test_case, bug_report ou user_story)
    seguindo rigorosamente os padrões ISTQB.
    """
    schema_instruction = ISTQB_SCHEMAS.get(entity_type, "")
    
    full_prompt = f"""
    Você é um Engenheiro de Qualidade de Software (QA) Especialista certificado pelo ISTQB.
    Analise o contexto fornecido e atenda ao pedido seguindo rigorosamente os padrões de QA.

    CONTEXTO INFORMADO:
    {user_context}

    {schema_instruction}
    
    ATENÇÃO: Retorne APENAS o JSON. Não inclua conversas, saudações ou explicações fora do JSON.
    """
    
    raw_response = generate_ai_content(full_prompt)
    return parse_ai_json(raw_response)
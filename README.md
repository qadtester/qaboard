# QA & Requisitos Hub (qaboard)

## Sobre este projeto

O **QA & Requisitos Hub** (repositório `qaboard`) representa o primeiro registro de implementação do sistema de apoio à engenharia de requisitos e garantia da qualidade de software (QA).

O projeto foi estruturado em Python utilizando **Streamlit** para a interface web e o **Supabase** (PostgreSQL) como serviço de persistência de dados, integrando recursos de Inteligência Artificial generativa voltados às diretrizes do **ISTQB**.

---

## Contexto

- **Evidência no histórico Git:** O repositório registra commits em 10 de agosto de 2026, entre 18:47:52 (-03:00) e 19:15:48 (-03:00), totalizando 5 commits na branch `main`. O título configurado no código-fonte (`app.py`) é `"QA & Requisitos Hub"` (com a identificação visual `"🎯 QA Hub"`).
- **Contexto fornecido pelo proprietário:** Representa o estágio inicial de experimentação para reunir requisitos e testes de qualidade em uma única interface conectada a modelos de linguagem.
- **Observação técnica:** Esta etapa funcionou como uma prova de conceito funcional, verificando a viabilidade de integrar Streamlit, banco de dados relacional e chamadas a LLMs para criação de artefatos de teste.

---

## Funcionalidades identificadas

Com base no código-fonte disponível em `app.py` e no diretório `modules/`:

1. **Autenticação Básica (`modules/auth.py`):**
   - Criação de conta e login com armazenamento de hash de senha (`SHA-256`).
   - Gerenciamento de sessão local via `st.session_state`.
2. **Gestão de Projetos (`modules/projects.py`):**
   - Cadastro e seleção de projetos ativos associados ao usuário.
   - Extração básica de texto a partir de arquivos `.txt`, `.pdf` e `.docx`.
3. **Módulo de Requisitos (`modules/requirements.py`):**
   - Registro e geração assistida por IA de Personas.
   - Especificação de Histórias de Usuário (*User Stories*).
   - Elaboração de Matriz de Risco preliminar vinculada ao projeto.
4. **Módulo de Testes Unificado (`modules/testing.py`):**
   - Casos de teste estruturados segundo padrões ISTQB (Tipo, Pré-condições, Passos, Resultados Esperados).
   - Relatórios de defeitos (*Bug Reports*) com severidade e passos para reprodução, agrupados no mesmo módulo.
5. **Métricas e Exportação Inicial (`modules/metrics.py`, `utils/export.py`):**
   - Contadores visuais de casos de teste, defeitos e itens de risco cadastrados.
   - Estrutura inicial de exportação.
6. **Integração com Inteligência Artificial (`config/ai_config.py`):**
   - Suporte a provedores de IA (Groq e Google Gemini) para geração automatizada de artefatos.

---

## Tecnologias

Tecnologias identificadas no arquivo `requirements.txt` e no código:

- **Linguagem:** Python
- **Interface:** Streamlit (`>=1.30.0`)
- **Banco de Dados & Autenticação:** Supabase Client (`>=2.0.0`)
- **Provedores de IA:** Groq SDK (`>=0.4.0`), Google Generative AI (`>=0.3.0`), OpenAI Python SDK (`>=1.10.0`)
- **Processamento de Dados e Visualização:** Pandas (`>=2.0.0`), Plotly (`>=5.18.0`), Tabulate (`>=0.9.0`)
- **Variáveis de Ambiente:** Python-dotenv (`>=1.0.0`)

---

## Estrutura

```text
qaboard/
├── app.py                      # Roteamento inicial e interface
├── requirements.txt            # Dependências Python
├── config/
│   ├── ai_config.py            # Integração com provedores de IA
│   └── database.py             # Conexão com o Supabase
├── modules/
│   ├── auth.py                 # Fluxo de login e cadastro
│   ├── metrics.py              # Exibição de contadores e gráficos
│   ├── projects.py             # Cadastro e alternância de projetos
│   ├── requirements.py         # Personas, User Stories e Riscos
│   └── testing.py              # Casos de teste e bugs agrupados
└── utils/
    └── export.py               # Utilitário de exportação inicial
```

---

## Histórico

- **Primeiro commit registrado:** `00a5760` — `2026-08-10T18:47:52-03:00`
- **Último commit registrado:** `27ef555` — `2026-08-10T19:15:48-03:00`
- **Total de commits:** 5 commits
- **Identidade nos commits:** `qadtester`
- **Tabelas do banco de dados identificadas no código:** `users`, `teams`, `projects`, `personas`, `user_stories`, `risk_matrix`, `test_cases`, `bug_reports`.

---

## Papel na evolução do projeto

O repositório `qaboard` estabeleceu o conceito inicial de unir o levantamento de requisitos e a engenharia de qualidade dentro de uma ferramenta integrada com IA.

---

## Repositórios relacionados no desenvolvimento

- [hubv2](https://github.com/qadtester/hubv2) — Repositório utilizado para experimentação de gestão de organizações e equipes.
- [qahub](https://github.com/qadtester/qahub) — Repositório criado no período seguinte onde o desenvolvimento do conceito QA Hub continuou.

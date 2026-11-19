import json
from datetime import datetime
from urllib import error, request

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Agentic System Builder",
    page_icon="AS",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    :root {
        --bg: #080808;
        --panel: #101010;
        --border: #292929;
        --text: #fffaf1;
        --muted: #aaa69f;
        --accent: #fffaf1;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        background: var(--bg);
        color: var(--text);
        font-family: Inter, system-ui, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background: #0b0b0b;
        border-right: 1px solid var(--border);
        width: 330px;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stMainBlockContainer"] { max-width: 1120px; }
    h1, h2, h3 { color: var(--text); }
    p, label, [data-testid="stCaptionContainer"] { color: var(--muted); }
    .demo-card {
        border: 1px solid var(--border);
        border-radius: 12px;
        background: var(--panel);
        padding: 18px;
        margin-bottom: 12px;
    }
    .demo-title {
        font-size: 32px;
        line-height: 1.12;
        letter-spacing: -0.04em;
        margin: 8px 0 4px 0;
    }
    .stButton > button {
        border-radius: 8px;
        min-height: 42px;
        background: #111111;
        border: 1px solid var(--border);
        color: var(--text);
    }
    .stButton > button[kind="primary"] {
        background: var(--accent);
        border-color: var(--accent);
        color: #111111;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if "demo_systems" not in st.session_state:
    st.session_state.demo_systems = {}
if "demo_messages" not in st.session_state:
    st.session_state.demo_messages = {}


def openrouter_chat(api_key, model, messages):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 2000,
    }
    http_request = request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter returned HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach OpenRouter: {exc.reason}") from exc

    content = result.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        raise RuntimeError("OpenRouter returned no response.")
    return str(content).strip()


def run_public_team(system, api_key, model, user_input):
    agents = [
        agent for agent in system["agents"]
        if str(agent.get("Role", "")).strip()
    ]
    if not agents:
        return "No agents are configured."

    agent_names = [str(agent["Role"]).strip() for agent in agents]
    conversation = [
        {
            "role": "system",
            "content": (
                "You are a coordinator for a public agent-system demo. "
                "Do not execute code or claim that tools ran. "
                "Choose and answer from exactly one of these roles: "
                + ", ".join(agent_names)
            ),
        }
    ]

    for message in system.get("history", []):
        role = "assistant" if message.get("role") == "assistant" else "user"
        conversation.append({
            "role": role,
            "content": str(message.get("content", "")),
        })
    conversation.append({"role": "user", "content": user_input})

    route_prompt = conversation + [{
        "role": "system",
        "content": (
            f"Configured roles: {', '.join(agent_names)}. "
            "Return exactly one configured role name. "
            "Choose the best role for the latest user request."
        ),
    }]

    try:
        route = openrouter_chat(api_key, model, route_prompt)
    except Exception:
        route = ""

    selected = next(
        (
            name for name in agent_names
            if name.lower() in route.lower()
        ),
        agent_names[0],
    )
    agent = next(
        item for item in agents
        if str(item["Role"]).strip() == selected
    )

    worker_messages = conversation + [{
        "role": "system",
        "content": (
            f"You are {selected}. {agent.get('Instructions', '')}\n"
            "Public demo restriction: do not execute code, access files, "
            "use tools, claim to have run tools, or expose secrets. "
            "Answer directly and clearly."
        ),
    }]
    result = openrouter_chat(api_key, model, worker_messages)
    return f"**{selected}**\n\n{result}"


with st.sidebar:
    st.markdown("## Agentic System Builder")
    st.caption(
        "Public demo: code is not executed, and systems and chats "
        "are kept only for this session."
    )
    api_key = st.text_input("OpenRouter API Key", type="password")
    st.caption("For testing without paid credits, use openrouter/free.")
    model = st.text_input("OpenRouter Model", value="openrouter/free")

    st.markdown("---")
    system_names = list(st.session_state.demo_systems.keys())
    selected_name = st.selectbox(
        "Select Active System",
        ["-- Create New --"] + system_names,
    )

    if selected_name == "-- Create New --":
        st.markdown("### Create New System")
        new_name = st.text_input(
            "System Name",
            placeholder="e.g. Market Research Team",
        )
        uploaded_csv = st.file_uploader(
            "Upload Instructions (CSV)",
            type=["csv"],
            help="Maximum file size: 200 MB. Columns: Role, Instructions",
        )
        st.caption("200MB per file • CSV")

        if st.button("Create System", type="primary"):
            if not new_name or uploaded_csv is None:
                st.warning("Provide a system name and CSV file.")
            else:
                try:
                    df = pd.read_csv(uploaded_csv)
                    if not {"Role", "Instructions"}.issubset(df.columns):
                        st.error("CSV must contain Role and Instructions columns.")
                    else:
                        df["Role"] = df["Role"].fillna("").astype(str).str.strip()
                        df["Instructions"] = df["Instructions"].fillna("").astype(str).str.strip()
                        agents = [
                            {"Role": row["Role"], "Instructions": row["Instructions"]}
                            for row in df.to_dict(orient="records")
                            if row["Role"]
                        ]
                        if not agents:
                            st.error("The CSV must contain at least one role.")
                        else:
                            st.session_state.demo_systems[new_name] = {
                                "created_at": str(datetime.now()),
                                "agents": agents,
                                "history": [],
                            }
                            st.session_state.demo_messages[new_name] = []
                            st.success(f"Created {new_name}.")
                            st.rerun()
                except Exception as exc:
                    st.error(f"Could not parse CSV: {exc}")


if selected_name == "-- Create New --" or selected_name not in st.session_state.demo_systems:
    st.markdown('<div class="demo-title">Agentic System Builder</div>', unsafe_allow_html=True)
    st.markdown("Connecting")
    st.info("Use the sidebar to create your first Agentic System.")
else:
    system = st.session_state.demo_systems[selected_name]
    st.markdown(f'<div class="demo-title">{selected_name}</div>', unsafe_allow_html=True)

    with st.expander("View Agent Team"):
        for agent in system["agents"]:
            st.markdown(f"**{agent['Role']}**")
            st.caption(str(agent["Instructions"]))

    messages = st.session_state.demo_messages.setdefault(selected_name, [])
    for message in messages:
        role = "assistant" if message["role"] == "assistant" else "user"
        with st.chat_message(role):
            st.markdown(str(message["content"]))

    user_input = st.chat_input("Enter your request")
    if user_input:
        if not api_key:
            st.error("Please enter your OpenRouter API Key.")
        elif not model.strip():
            st.error("Please enter an OpenRouter Model.")
        else:
            messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            try:
                result = run_public_team(
                    system,
                    api_key,
                    model.strip(),
                    user_input,
                )
                messages.append({"role": "assistant", "content": result})
                system["history"] = messages
                with st.chat_message("assistant"):
                    st.markdown(result)
            except Exception as exc:
                st.error(f"Execution Error: {exc}")

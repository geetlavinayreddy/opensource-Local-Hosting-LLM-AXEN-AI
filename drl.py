# Dynamic agentic system builder
# Uses direct HTTP APIs so native LangChain DLL dependencies are not required.
import glob
import json
import os
import subprocess
import sys
from datetime import datetime
from urllib import request, error

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="AXEN Agent System",
    page_icon="J",
    layout="wide",
)

if "theme_name" not in st.session_state:
    st.session_state.theme_name = "Mercury black"

voice_text = st.query_params.get("voice", "")
if voice_text:
    text = str(voice_text).strip()
    lower = text.lower()

    theme_commands = {
        "mercury": "Mercury black",
        "pure black": "Mercury black",
        "warm white": "Warm ivory",
        "ivory": "Warm ivory",
        "blue": "Blue",
        "red": "Red",
        "green": "Green",
        "purple": "Purple",
    }
    theme_match = next(
        (theme for word, theme in theme_commands.items() if word in lower),
        None,
    )
    if theme_match:
        st.session_state.theme_name = theme_match
        st.session_state.pending_speech = f"{theme_match} theme applied."
    elif "open axen" in lower or "open workspace" in lower:
        st.session_state.pending_speech = "AXEN workspace is ready."
    else:
        st.session_state.pending_voice_request = text
    st.query_params.clear()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap');
:root {
    --jarvics-bg: #080808;
    --jarvics-panel: #101010;
    --jarvics-panel-soft: #0d0d0d;
    --jarvics-border: #242424;
    --jarvics-border-soft: #1c1c1c;
    --jarvics-primary: #fffaf1;
    --jarvics-text: #fffaf1;
    --jarvics-muted: #aaa69f;
    --jarvics-welcome: #fffaf1;
    --jarvics-login: #e8e2d8;
    --jarvics-preview: #cbc5bb;
    --jarvics-terms: #aaa69f;
    --jarvics-success: #d8d1c5;
    --jarvics-warning: #948d82;
    --jarvics-danger: #756f66;
}
.stApp, [data-testid="stAppViewContainer"] {
    background: var(--jarvics-bg);
    color: var(--jarvics-text);
    font-family: Inter, system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
}
section[data-testid="stSidebar"] {
    background: #0b0b0b;
    border-right: 1px solid var(--jarvics-border);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] {
    max-width: 1040px;
    padding-top: 3.25rem;
}
h1, h2, h3 { color: var(--jarvics-text); letter-spacing: -0.02em; }
p, label, .stMarkdown, [data-testid="stCaptionContainer"] {
    color: var(--jarvics-muted);
}
.jarvics-card {
    background: var(--jarvics-panel);
    border: 1px solid var(--jarvics-border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
    box-shadow: 0 18px 50px rgba(0,0,0,0.20);
}
.jarvics-kicker {
    color: #c9c2b6;
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
}
.jarvics-title {
    font-size: 36px;
    line-height: 1.08;
    margin: 10px 0 12px 0;
    color: var(--jarvics-text);
    font-weight: 600;
    letter-spacing: -0.045em;
}
.jarvics-description {
    max-width: 590px;
    font-size: 16px;
    line-height: 1.65;
    color: #beb9b0;
}
.demo-title {
    font-size: 32px;
    line-height: 1.12;
    letter-spacing: -0.04em;
    margin: 8px 0 16px 0;
    color: var(--jarvics-text);
}
.demo-card {
    border: 1px solid var(--jarvics-border);
    border-radius: 12px;
    background: var(--jarvics-panel);
    padding: 18px;
    margin-bottom: 12px;
}
.jarvics-steps {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 0;
    margin: 4px 0 28px 0;
    border-bottom: 1px solid var(--jarvics-border);
}
.jarvics-step {
    border: 0;
    border-bottom: 1px solid transparent;
    border-radius: 0;
    padding: 10px 8px 12px 8px;
    color: var(--jarvics-muted);
    font-size: 12px;
    letter-spacing: 0.01em;
}
.jarvics-step-active {
    border-color: var(--jarvics-primary);
    color: var(--jarvics-text);
    background: transparent;
    font-weight: 600;
}
.jarvics-step-active:nth-child(1) {
    border-color: #fffaf1;
    background: transparent;
}
.jarvics-step-active:nth-child(2) {
    border-color: #e8e2d8;
    background: transparent;
}
.jarvics-step-active:nth-child(3) {
    border-color: #cbc5bb;
    background: transparent;
}
.jarvics-step-active:nth-child(4) {
    border-color: #aaa69f;
    background: transparent;
}
.jarvics-color-matrix {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 18px 0;
}
.jarvics-color-cell {
    min-height: 76px;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 14px;
}
.jarvics-color-cell strong,
.jarvics-color-cell span {
    display: block;
}
.jarvics-color-cell strong {
    color: #09101f;
    font-size: 13px;
}
.jarvics-color-cell span {
    margin-top: 7px;
    color: rgba(9,16,31,0.78);
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
}
.jarvics-welcome { background: var(--jarvics-welcome); }
.jarvics-login { background: var(--jarvics-login); }
.jarvics-preview { background: var(--jarvics-preview); }
.jarvics-terms { background: var(--jarvics-terms); }
.jarvics-success { background: var(--jarvics-success); }
.jarvics-warning { background: var(--jarvics-warning); }
.jarvics-danger { background: var(--jarvics-danger); }
.stButton > button {
    border-radius: 9px;
    border: 1px solid var(--jarvics-border);
    min-height: 44px;
    background: #111111;
    color: var(--jarvics-text);
    transition: border-color 160ms ease, background 160ms ease;
}
.stButton > button:hover {
    border-color: #56514a;
    background: #151515;
}
.stButton > button[kind="primary"] {
    background: #fffaf1;
    border-color: #fffaf1;
    color: #15120e;
    font-weight: 650;
}
.stButton > button[kind="primary"]:hover {
    background: #eae3d8;
    border-color: #eae3d8;
}
.stTextInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stTextArea textarea {
    background: #0d0d0d !important;
    border-color: var(--jarvics-border) !important;
    color: var(--jarvics-text) !important;
}
.stChatInput textarea {
    background: #101010 !important;
    border-color: #303030 !important;
    color: var(--jarvics-text) !important;
}
</style>
""", unsafe_allow_html=True)

theme_name = st.session_state.theme_name
theme_palettes = {
    "Mercury black": ("#050505", "#111111", "#242424", "#fffaf1", "#aaa69f", "#fffaf1"),
    "Warm ivory": ("#080808", "#15120e", "#302b24", "#fffaf1", "#b8b0a3", "#fffaf1"),
    "Blue": ("#080b12", "#111827", "#26344d", "#eef5ff", "#9baac2", "#82aaff"),
    "Red": ("#120808", "#201011", "#4b2929", "#fff4f4", "#bea5a5", "#ffb4b4"),
    "Green": ("#08120d", "#102018", "#294638", "#f2fff7", "#a7b9ae", "#9be7bd"),
    "Purple": ("#0d0912", "#191125", "#3a2e50", "#faf5ff", "#b4a8c2", "#d1b4ff"),
}
bg, panel, border, text, muted, primary = theme_palettes[theme_name]
st.markdown(
    f"""
    <style>
    :root {{
        --jarvics-bg: {bg};
        --jarvics-panel: {panel};
        --jarvics-border: {border};
        --jarvics-text: {text};
        --jarvics-muted: {muted};
        --jarvics-primary: {primary};
    }}
    section[data-testid="stSidebar"] {{
        background: {bg};
    }}
    .stButton > button[kind="primary"] {{
        background: {primary};
        border-color: {primary};
        color: #111111;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
DATA_FILE = os.path.join(BASE_DIR, "agent_systems.json")
AXEN_CSV_FILE = os.path.join(BASE_DIR, "axen.csv")
os.makedirs(WORKSPACE_DIR, exist_ok=True)


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def render_voice_agent(speech_text=""):
    speech_json = json.dumps(speech_text)
    components.html(
        f"""
        <style>
          body {{ margin: 0; background: transparent; font-family: Inter, system-ui, sans-serif; }}
          .voice-panel {{
            display: flex; align-items: center; gap: 10px;
            border: 1px solid #2b2b2b; border-radius: 10px;
            padding: 8px; background: #101010;
          }}
          .voice-button {{
            width: 42px; height: 42px; border: 1px solid #464646;
            border-radius: 50%; background: #fffaf1; color: #111111;
            cursor: pointer; font-size: 18px;
          }}
          .voice-button.listening {{ background: #d8d1c5; border-color: #fffaf1; }}
          .voice-status {{ color: #aaa69f; font-size: 12px; line-height: 1.35; }}
        </style>
        <div class="voice-panel">
          <button id="voice-button" class="voice-button" title="Start voice input">Mic</button>
          <div id="voice-status" class="voice-status">Tap to speak</div>
        </div>
        <script>
          const speechText = {speech_json};
          if (speechText && window.speechSynthesis) {{
            const utterance = new SpeechSynthesisUtterance(speechText);
            utterance.rate = 1.0;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
          }}

          const button = document.getElementById("voice-button");
          const status = document.getElementById("voice-status");
          const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
          if (!Recognition) {{
            status.textContent = "Voice input is not supported in this browser.";
            button.disabled = true;
          }} else {{
            const recognition = new Recognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = "en-US";
            button.addEventListener("click", () => {{
              button.classList.add("listening");
              status.textContent = "Listening...";
              recognition.start();
            }});
            recognition.addEventListener("result", (event) => {{
              const transcript = event.results[0][0].transcript.trim();
              status.textContent = transcript;
              const parentUrl = new URL(window.parent.location.href);
              parentUrl.searchParams.set("voice", transcript);
              window.parent.location.assign(parentUrl.toString());
            }});
            recognition.addEventListener("error", (event) => {{
              button.classList.remove("listening");
              status.textContent = "Could not capture voice: " + event.error;
            }});
            recognition.addEventListener("end", () => button.classList.remove("listening"));
          }}
        </script>
        """,
        height=70,
    )


def load_csv_agents(csv_path):
    df = pd.read_csv(csv_path)
    required = {"Role", "Instructions"}
    if not required.issubset(df.columns):
        raise ValueError("CSV must have 'Role' and 'Instructions' columns.")

    df["Role"] = df["Role"].fillna("").astype(str).str.strip()
    df["Instructions"] = df["Instructions"].fillna("").astype(str).str.strip()
    agents = [
        {"Role": row["Role"], "Instructions": row["Instructions"]}
        for row in df.to_dict(orient="records")
        if row["Role"]
    ]
    if not agents:
        raise ValueError("CSV must contain at least one agent Role.")
    return agents


def ensure_axen_system(data):
    if "axen" in data:
        return data

    csv_file = AXEN_CSV_FILE
    if os.path.exists(csv_file):
        try:
            data["axen"] = {
                "created_at": str(datetime.now()),
                "agents": load_csv_agents(csv_file),
                "history": [],
            }
            save_data(data)
        except (OSError, ValueError, pd.errors.ParserError) as error:
            st.warning(f"Could not load AXEN CSV: {error}")
    return data


def chat_completion(provider, model, api_key, messages):
    if provider == "Local Ollama":
        url = "http://127.0.0.1:11434/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0},
        }
        headers = {"Content-Type": "application/json"}
    else:
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 2000,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(url, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(http_request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Model API returned HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach the model API: {exc.reason}") from exc

    if provider == "Local Ollama":
        content = result.get("message", {}).get("content")
    else:
        content = result.get("choices", [{}])[0].get("message", {}).get("content")

    if not content:
        raise RuntimeError(f"Model returned no response: {json.dumps(result)[:500]}")
    return str(content).strip()


def get_ollama_status():
    try:
        with request.urlopen(
            request.Request("http://127.0.0.1:11434/api/tags", method="GET"),
            timeout=5,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = [
            str(item.get("name", "")).strip()
            for item in payload.get("models", [])
            if str(item.get("name", "")).strip()
        ]
        return True, models
    except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError):
        return False, []


def execute_python_code(code):
    file_path = os.path.join(WORKSPACE_DIR, "script.py")
    clean_code = code.replace("```python", "").replace("```", "").strip()
    if not clean_code:
        return False, "No Python code was supplied."

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(clean_code)

    try:
        result = subprocess.run(
            [sys.executable, "script.py"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORKSPACE_DIR,
        )
        if result.returncode != 0:
            return False, f"RUNTIME ERROR:\n{result.stderr}"
        return True, f"SUCCESS:\n{result.stdout}"
    except Exception as exc:
        return False, f"SYSTEM ERROR:\n{exc}"


def run_agent_team(
    active_system,
    provider,
    model,
    api_key,
    user_input,
    history,
    code_execution_enabled=True,
):
    agents = [
        agent for agent in active_system.get("agents", [])
        if str(agent.get("Role", "")).strip()
    ]
    agent_names = [str(agent["Role"]).strip() for agent in agents]
    if not agents:
        return "No agents are configured.", history

    conversation = []
    for message in history:
        role = "assistant" if message.get("role") == "assistant" else "user"
        conversation.append({"role": role, "content": str(message.get("content", ""))})
    conversation.append({"role": "user", "content": user_input})

    supervisor_prompt = (
        f"Configured roles: {', '.join(agent_names)}\n"
        "Return exactly one configured role name from the list. "
        "Do not explain. Choose the best role for the user's latest request."
    )
    supervisor_messages = conversation + [
        {"role": "system", "content": supervisor_prompt}
    ]

    try:
        route = chat_completion(
            provider,
            model,
            api_key,
            supervisor_messages,
        )
    except Exception:
        route = ""

    route_lower = route.lower()
    selected = next(
        (
            agent_name
            for agent_name in agent_names
            if agent_name.lower() in route_lower
        ),
        None,
    )

    if selected is None:
        request_lower = user_input.lower()
        keyword_routes = {
            "Coder": ("code", "python", "program", "bug", "function", "file", "script"),
            "Planner": ("plan", "steps", "roadmap", "task"),
            "Researcher": ("research", "compare", "fact", "source", "market"),
            "Reviewer": ("review", "check", "error", "correct", "audit"),
            "Tool_Operator": ("calculate", "execute", "run", "csv", "data"),
            "Memory_Manager": ("remember", "memory", "preference"),
            "Safety_Guardian": ("safe", "privacy", "credential", "security"),
            "Local_Model_Manager": ("ollama", "model", "gpu", "local"),
        }
        for role_name, keywords in keyword_routes.items():
            if role_name in agent_names and any(word in request_lower for word in keywords):
                selected = role_name
                break
        selected = selected or "Supervisor"

    if selected == "Supervisor" and "Supervisor" not in agent_names:
        selected = agent_names[0]

    agent = next(
        item for item in agents
        if str(item["Role"]).strip() == selected
    )
    worker_messages = conversation + [{
        "role": "system",
        "content": (
            f"You are {selected}. {agent.get('Instructions', '')}\n"
            "Answer the user's latest request directly and completely. "
            "If code processing is needed, include one fenced ```python``` block."
        ),
    }]
    response = chat_completion(provider, model, api_key, worker_messages)

    code = None
    if "```python" in response:
        try:
            code = response.split("```python", 1)[1].split("```", 1)[0].strip()
        except Exception:
            code = None

    if code and code_execution_enabled:
        success, output = execute_python_code(code)
        response = (
            f"{response}\n\n"
            f"**Tool result**\n"
            f"```text\n{output}\n```"
        )
    elif code:
        response = (
            f"{response}\n\n"
            "**Code execution disabled**\n"
            "Python execution is off in the current AXEN workspace."
        )

    return response, history


all_systems = ensure_axen_system(load_data())

with st.sidebar:
    st.markdown("## Agentic System Builder")
    st.caption("AXEN workspace: select a provider and build a role-based team.")
    st.markdown("---")

    provider = st.selectbox("Model Provider", ["Local Ollama", "OpenRouter"])
    api_key = ""
    if provider == "OpenRouter":
        api_key = st.text_input("OpenRouter API Key", type="password")
        st.caption("For testing without paid credits, use openrouter/free.")
        model_name = st.text_input("OpenRouter Model", value="openrouter/free")
    else:
        online, models = get_ollama_status()
        if online:
            st.caption("Ollama is connected.")
        else:
            st.caption("Ollama is offline.")
        model_name = st.selectbox(
            "Ollama Model",
            list(dict.fromkeys(models + ["qwen2.5:7b"])) if online else ["qwen2.5:7b"],
        )

    st.markdown("---")
    system_names = list(all_systems.keys())
    selected_name = st.selectbox(
        "Select Active System",
        ["-- Create New --"] + system_names,
    )

    if selected_name == "-- Create New --":
        st.markdown("### Create New System")
        new_name = st.text_input("System Name", placeholder="e.g. Market Research Team")
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
                        st.error("CSV must contain Role and Instructions.")
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
                            all_systems[new_name] = {
                                "created_at": str(datetime.now()),
                                "agents": agents,
                                "history": [],
                            }
                            save_data(all_systems)
                            st.success(f"Created {new_name}.")
                            st.rerun()
                except Exception as exc:
                    st.error(f"Could not parse CSV: {exc}")

    st.markdown("---")
    render_voice_agent(st.session_state.pop("pending_speech", ""))

if selected_name == "-- Create New --" or selected_name not in all_systems:
    st.markdown('<div class="demo-title">AXEN Workspace</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="demo-card">'
        '<strong>Start with a CSV</strong>'
        '<p>Use the sidebar to select a model and create or open an agent system.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    active_system = all_systems[selected_name]
    st.markdown(f'<div class="demo-title">{selected_name}</div>', unsafe_allow_html=True)

    with st.expander("View Agent Team"):
        for agent in active_system["agents"]:
            st.markdown(f"**{agent['Role']}**")
            st.caption(str(agent["Instructions"]))

    if "messages" not in st.session_state:
        st.session_state.messages = active_system.get("history", [])

    for message in st.session_state.messages:
        role = "assistant" if message["role"] == "assistant" else "user"
        with st.chat_message(role):
            st.markdown(str(message["content"]))

    pending_voice_request = st.session_state.pop("pending_voice_request", "")
    user_input = pending_voice_request or st.chat_input("Enter your request")
    if user_input:
        if provider == "OpenRouter" and not api_key:
            st.error("Please enter your OpenRouter API Key.")
        elif not model_name.strip():
            st.error("Please enter or select a model.")
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            try:
                code_enabled = st.session_state.get("code_execution_enabled", True)
                result, _ = run_agent_team(
                    active_system,
                    provider,
                    model_name,
                    api_key,
                    user_input,
                    st.session_state.messages[:-1],
                    code_enabled,
                )
                st.session_state.messages.append({"role": "assistant", "content": result})
                active_system["history"] = st.session_state.messages
                save_data(all_systems)
                with st.chat_message("assistant"):
                    st.markdown(result)
                if pending_voice_request:
                    st.session_state.pending_speech = str(result)[:600]
                    st.rerun()
            except Exception as exc:
                st.error(f"Execution Error: {exc}")

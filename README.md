# AXEN

AXEN is a local, role-based agent workspace built with Python and Streamlit.

## Features

- Ollama and OpenRouter model providers
- Role-based agent teams loaded from CSV
- Browser microphone input and voice commands
- Mercury-black interface
- Public demo mode with no Python code execution
- Optional local Python tool execution

## Run AXEN

```powershell
py -m venv agents
.\agents\Scripts\Activate.ps1
python -m pip install -U streamlit pandas
python -m streamlit run drl.py --server.port 8501
```

## Run the public demo

```powershell
python -m streamlit run public_demo.py --server.port 8502
```

The public demo keeps systems and chats in Streamlit session memory and does not execute Python code.

## AgroMind API

The `app/` package provides a separate FastAPI backend for evidence-grounded
agricultural assistance. It supports disease guidance, irrigation, soil/resource
guidance, mandi prices, farmer-approved memory, and human-review flags.

```powershell
.\agents\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\agents\Scripts\python.exe -m unittest discover -s tests -v
.\agents\Scripts\python.exe -m uvicorn app.main:app --reload
```

Add official `.txt` or `.md` documents under `knowledge\`; see
`knowledge\README.md` for the metadata format. Do not commit `.env` or API keys.

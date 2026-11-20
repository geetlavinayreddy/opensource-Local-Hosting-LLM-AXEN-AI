from dataclasses import fields
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agents.base import Context
from .agents.disease import DiseaseAgent
from .agents.irrigation import IrrigationAgent
from .agents.market import MarketAgent
from .agents.resource import ResourceAgent
from .config import Config
from .connectors.mandi import MandiConnector
from .llm import LLM
from .memory import Memory
from .models import FarmerRequest
from .orchestrator import Orchestrator
from .rag import KnowledgeBase

cfg = Config.from_env()
memory = Memory(cfg.db_path)
kb = KnowledgeBase(cfg.knowledge_dir)
ctx = Context(kb, memory, cfg)
orch = Orchestrator(cfg, ctx, LLM(cfg), {
    "disease": DiseaseAgent(model=None),   # plug in your trained image model here
    "irrigation": IrrigationAgent(),
    "resource": ResourceAgent(),
    "market": MarketAgent(MandiConnector(cfg.data_gov_api_key, cfg.mandi_resource_id)),
})

app = FastAPI(title="AgroMind AI")

class AskBody(BaseModel):
    farmer_id: str
    question: str
    crop: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    crop_stage: Optional[str] = None
    language: str = "en"
    symptoms: Optional[str] = None
    soil_moisture_pct: Optional[float] = None
    soil_test: Optional[dict[str, float]] = None
    image_path: Optional[str] = None

class ProfileBody(BaseModel):
    consent: bool
    language: Optional[str] = None
    crop: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    irrigation_method: Optional[str] = None

class HistoryBody(BaseModel):
    kind: str            # observation | soil_test | action | outcome
    data: dict

class ApprovalBody(BaseModel):
    trace_id: str
    decision: str        # approved | rejected | corrected
    approved_by: str
    note: str = ""

@app.get("/health")
def health():
    return {"ok": True, "documents": len(kb.passages), "llm": orch.llm.available}

@app.post("/ask")
def ask(body: AskBody):
    req = FarmerRequest(**{f.name: getattr(body, f.name) for f in fields(FarmerRequest)})
    return orch.handle(req).to_dict()

@app.put("/farmers/{farmer_id}/profile")
def set_profile(farmer_id: str, body: ProfileBody):
    try:
        return memory.set_profile(farmer_id, body.model_dump(exclude={"consent"}, exclude_none=True), body.consent)
    except PermissionError as e:
        raise HTTPException(403, str(e))

@app.post("/farmers/{farmer_id}/history")
def add_history(farmer_id: str, body: HistoryBody):
    try:
        memory.add_history(farmer_id, body.kind, body.data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"saved": True}

@app.get("/farmers/{farmer_id}/history")
def get_history(farmer_id: str):
    return memory.history(farmer_id)

@app.delete("/farmers/{farmer_id}")
def delete_farmer(farmer_id: str):
    memory.delete_farmer(farmer_id)
    return {"deleted": True}

@app.post("/farmers/{farmer_id}/approve")
def approve(farmer_id: str, body: ApprovalBody):
    memory.record_approval(body.trace_id, farmer_id, body.decision, body.approved_by, body.note)
    return {"recorded": True}

@app.post("/knowledge/reload")
def reload_kb():
    kb.load()
    return {"documents": len(kb.passages)}

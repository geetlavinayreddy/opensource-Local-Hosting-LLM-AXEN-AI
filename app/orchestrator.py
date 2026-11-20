import uuid
from dataclasses import asdict
from datetime import datetime

from . import hitl
from .agents.base import Agent, Context
from .config import Config
from .llm import LLM
from .models import AgentResult, FarmerRequest, Response

KEYWORDS = {
    "disease": ("disease", "pest", "spot", "leaf", "yellow", "wilt", "blight", "rust", "insect", "fung", "symptom", "curl", "rot", "worm"),
    "irrigation": ("irrigat", "water", "moisture", "rain", "wilt", "dry", "drought", "sprinkler", "drip"),
    "resource": ("fertili", "nutrient", "soil", "urea", "npk", "manure", "dose", "input", "ph"),
    "market": ("price", "mandi", "sell", "market", "msp", "rate", "profit", "which crop", "sow"),
}

class Orchestrator:
    def __init__(self, cfg: Config, ctx: Context, llm: LLM, agents: dict[str, Agent]):
        self.cfg, self.ctx, self.llm, self.agents = cfg, ctx, llm, agents

    # 1. plan
    def plan(self, req: FarmerRequest) -> list[str]:
        names = list(self.agents)
        if self.llm.available:
            picked = self.llm.pick_agents(req.question, names)
            if picked:
                return picked
        text = f"{req.question} {req.symptoms or ''}".lower()
        return [n for n in names if any(k in text for k in KEYWORDS.get(n, ()))]

    # 2. handle
    def handle(self, req: FarmerRequest) -> Response:
        trace_id = uuid.uuid4().hex[:12]
        profile = self.ctx.memory.get_profile(req.farmer_id)
        for f in ("crop", "state", "district"):
            if not getattr(req, f) and profile.get(f):
                setattr(req, f, profile[f])
        if req.language == "en" and profile.get("language"):
            req.language = profile["language"]

        questions = []
        if not req.crop:
            questions.append("Which crop is this about?")
        if not req.district:
            questions.append("Which district is your farm in?")
        selected = self.plan(req)
        if not selected:
            questions.append("What do you need help with: crop disease, irrigation, fertiliser/soil, or market prices?")
        if questions:
            return Response(trace_id, "needs_info", questions=questions)

        results = []
        for name in selected:
            try:
                results.append(self.agents[name].run(req, self.ctx))
            except Exception as e:
                results.append(AgentResult(name, "This agent failed.", warnings=[str(e)], needs_human_review=True))

        flags = hitl.review(results, req)
        answer = self.compose(req, results, flags)
        resp = Response(trace_id, "answered", answer, [], results, flags)
        self.ctx.memory.log_trace(trace_id, req.farmer_id, {
            "time": datetime.now().isoformat(), "request": asdict(req), "agents": selected,
            "sources": [e.title for r in results for e in r.evidence], "flags": flags})
        return resp

    # 3. compose
    def compose(self, req: FarmerRequest, results: list[AgentResult], flags: list[str]) -> str:
        blocks = []
        for r in results:
            ev = "; ".join(f"{e.source}: {e.title} ({e.date or 'undated'})" for e in r.evidence) or "none"
            blocks.append(f"[{r.agent}] {r.summary}\nSources: {ev}\nWarnings: {r.warnings}\nSnippets: "
                          + " | ".join(e.snippet for e in r.evidence))
        if self.llm.available:
            prompt = (f"Farmer ({req.language}) asked: {req.question}\nCrop: {req.crop}, District: {req.district}, "
                      f"Stage: {req.crop_stage}\n\nAgent outputs:\n" + "\n\n".join(blocks) +
                      f"\n\nHuman-review flags: {flags}\nWrite one combined answer in language '{req.language}'.")
            try:
                return self.llm.complete(prompt)
            except Exception:
                pass  # fall through to deterministic answer
        lines = [f"- {r.summary}" + "".join(f"\n  Warning: {w}" for w in r.warnings) for r in results]
        lines += [f"! {f}" for f in flags]
        return "\n".join(lines)

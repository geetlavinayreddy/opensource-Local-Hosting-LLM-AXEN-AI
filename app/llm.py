"""Server-side LLM wrapper. Works offline (no key) with deterministic fallbacks."""
import json
import re

from .config import Config

SYSTEM = (
    "You are AgroMind AI, an assistant for Indian farmers. Answer ONLY from the evidence provided. "
    "Use simple, short language. Cite source names and dates. State uncertainty and missing evidence. "
    "Never invent diagnoses, prices, pesticide/fertilizer doses or irrigation amounts. "
    "A weather forecast is not a soil-moisture reading. An image classification is not a confirmed diagnosis. "
    "Mention any conflicts between agent outputs. If evidence is missing, say so plainly."
)

class LLM:
    def __init__(self, cfg: Config):
        self.cfg, self.client = cfg, None
        if cfg.anthropic_api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
            except ImportError:
                pass

    @property
    def available(self) -> bool:
        return self.client is not None

    def complete(self, prompt: str, system: str = SYSTEM, max_tokens: int = 900) -> str:
        msg = self.client.messages.create(
            model=self.cfg.anthropic_model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()

    def pick_agents(self, question: str, names: list[str]) -> list[str] | None:
        prompt = (f"Farmer question: {question}\nAvailable agents: {names}\n"
                  "Return ONLY a JSON list of the agent names needed.")
        try:
            raw = self.complete(prompt, system="You route requests to agents. Output JSON only.", max_tokens=100)
            found = json.loads(re.search(r"\[.*\]", raw, re.S).group(0))
            return [n for n in found if n in names]
        except Exception:
            return None

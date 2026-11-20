"""Human-in-the-loop rules."""
from .models import AgentResult, FarmerRequest

HIGH_IMPACT = ("spray", "apply", "buy", "sell", "pesticide", "fertilizer", "fertiliser", "invest", "loan", "urea")

def review(results: list[AgentResult], req: FarmerRequest) -> list[str]:
    flags = []
    for r in results:
        if r.needs_human_review:
            flags.append(f"[{r.agent}] Expert/KVK review recommended before acting.")
    q = req.question.lower()
    if any(w in q for w in HIGH_IMPACT):
        flags.append("High-impact decision (inputs, spraying, money): farmer confirmation required; "
                     "consult an agricultural expert before acting.")
    return flags

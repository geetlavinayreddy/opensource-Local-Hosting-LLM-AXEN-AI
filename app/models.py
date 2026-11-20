from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional

@dataclass
class Evidence:
    source: str            # e.g. ICAR, IMD, Soil Health Card, AGMARKNET
    title: str
    date: Optional[str] = None
    url: Optional[str] = None
    snippet: str = ""

@dataclass
class AgentResult:
    agent: str
    summary: str
    evidence: list[Evidence] = field(default_factory=list)
    confidence: Optional[float] = None
    warnings: list[str] = field(default_factory=list)
    needs_human_review: bool = False
    data: dict[str, Any] = field(default_factory=dict)

@dataclass
class FarmerRequest:
    farmer_id: str
    question: str
    crop: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    crop_stage: Optional[str] = None
    language: str = "en"
    symptoms: Optional[str] = None
    soil_moisture_pct: Optional[float] = None   # measured value only, never inferred
    soil_test: Optional[dict[str, float]] = None
    image_path: Optional[str] = None

@dataclass
class Response:
    trace_id: str
    status: str                       # "answered" | "needs_info"
    answer: str = ""
    questions: list[str] = field(default_factory=list)
    results: list[AgentResult] = field(default_factory=list)
    review_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

def parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None

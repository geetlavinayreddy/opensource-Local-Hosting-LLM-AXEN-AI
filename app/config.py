import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # dotenv optional
    pass

@dataclass
class Config:
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5-5"
    data_gov_api_key: str | None = None
    mandi_resource_id: str | None = None
    knowledge_dir: str = "knowledge"
    db_path: str = "agromind.db"
    disease_conf_threshold: float = 0.80
    market_stale_days: int = 7

    @classmethod
    def from_env(cls) -> "Config":
        g = os.getenv
        return cls(
            anthropic_api_key=g("ANTHROPIC_API_KEY") or None,
            anthropic_model=g("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
            data_gov_api_key=g("DATA_GOV_API_KEY") or None,
            mandi_resource_id=g("MANDI_RESOURCE_ID") or None,
            knowledge_dir=g("KNOWLEDGE_DIR", "knowledge"),
            db_path=g("DB_PATH", "agromind.db"),
            disease_conf_threshold=float(g("DISEASE_CONFIDENCE_THRESHOLD", "0.80")),
            market_stale_days=int(g("MARKET_STALE_DAYS", "7")),
        )

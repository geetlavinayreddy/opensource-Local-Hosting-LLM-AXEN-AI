"""Farmer-approved memory with consent, minimisation, correction and deletion.
Time-sensitive values (weather, soil moisture, prices) are never stored."""
import json
import sqlite3
import time

PROFILE_KEYS = {"language", "crop", "state", "district", "irrigation_method"}
HISTORY_KINDS = {"observation", "soil_test", "action", "outcome"}

class Memory:
    def __init__(self, path: str = "agromind.db"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS profiles(farmer_id TEXT PRIMARY KEY, data TEXT, updated REAL);
        CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT, farmer_id TEXT, kind TEXT, data TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS traces(trace_id TEXT PRIMARY KEY, farmer_id TEXT, data TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS approvals(id INTEGER PRIMARY KEY AUTOINCREMENT, trace_id TEXT, farmer_id TEXT, decision TEXT, approved_by TEXT, note TEXT, ts REAL);
        """)

    # --- profile ---
    def set_profile(self, farmer_id: str, profile: dict, consent: bool) -> dict:
        if not consent:
            raise PermissionError("Farmer consent is required to store a profile.")
        clean = {k: v for k, v in profile.items() if k in PROFILE_KEYS}
        cur = self.get_profile(farmer_id); cur.update(clean)
        self.db.execute("REPLACE INTO profiles VALUES(?,?,?)", (farmer_id, json.dumps(cur), time.time()))
        self.db.commit()
        return cur

    def get_profile(self, farmer_id: str) -> dict:
        r = self.db.execute("SELECT data FROM profiles WHERE farmer_id=?", (farmer_id,)).fetchone()
        return json.loads(r[0]) if r else {}

    # --- farm history ---
    def add_history(self, farmer_id: str, kind: str, data: dict) -> None:
        if kind not in HISTORY_KINDS:
            raise ValueError(f"'{kind}' cannot be stored; allowed: {sorted(HISTORY_KINDS)}. "
                             "Weather, moisture and prices must be refreshed, not remembered.")
        data = {**data, "recorded": time.strftime("%Y-%m-%d")}
        self.db.execute("INSERT INTO history(farmer_id,kind,data,ts) VALUES(?,?,?,?)",
                        (farmer_id, kind, json.dumps(data), time.time()))
        self.db.commit()

    def latest(self, farmer_id: str, kind: str) -> dict | None:
        r = self.db.execute("SELECT data FROM history WHERE farmer_id=? AND kind=? ORDER BY ts DESC LIMIT 1",
                            (farmer_id, kind)).fetchone()
        return json.loads(r[0]) if r else None

    def history(self, farmer_id: str, limit: int = 20) -> list[dict]:
        rows = self.db.execute("SELECT kind,data FROM history WHERE farmer_id=? ORDER BY ts DESC LIMIT ?",
                               (farmer_id, limit)).fetchall()
        return [{"kind": k, **json.loads(d)} for k, d in rows]

    # --- agent/task memory and approvals ---
    def log_trace(self, trace_id: str, farmer_id: str, trace: dict) -> None:
        self.db.execute("REPLACE INTO traces VALUES(?,?,?,?)", (trace_id, farmer_id, json.dumps(trace, default=str), time.time()))
        self.db.commit()

    def record_approval(self, trace_id: str, farmer_id: str, decision: str, approved_by: str, note: str = "") -> None:
        self.db.execute("INSERT INTO approvals(trace_id,farmer_id,decision,approved_by,note,ts) VALUES(?,?,?,?,?,?)",
                        (trace_id, farmer_id, decision, approved_by, note, time.time()))
        self.db.commit()

    # --- deletion ---
    def delete_farmer(self, farmer_id: str) -> None:
        for t in ("profiles", "history", "traces", "approvals"):
            self.db.execute(f"DELETE FROM {t} WHERE farmer_id=?", (farmer_id,))
        self.db.commit()

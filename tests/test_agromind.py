import tempfile
import unittest
from pathlib import Path

from app.agents.base import Context
from app.agents.disease import DiseaseAgent
from app.agents.irrigation import IrrigationAgent
from app.agents.market import MarketAgent
from app.agents.resource import ResourceAgent
from app.config import Config
from app.llm import LLM
from app.memory import Memory
from app.models import FarmerRequest
from app.orchestrator import Orchestrator
from app.rag import KnowledgeBase

# Synthetic test documents only; not real agricultural guidance.
DOCS = {
    "a.txt": "title: Test crop note\nissuer: ICAR\ncrop: testcrop\nregion: X\ndate: 01/01/2026\nurl: http://example\n\nyellow spots on leaf test symptom guidance paragraph.",
    "b.txt": "title: Test weather\nissuer: IMD\ncrop: all\ndate: 02/01/2026\n\nrain advisory water irrigation district bulletin.",
}

class FakeMandi:
    def fetch(self, state, district, commodity, limit=20):
        return [{"market": "M1", "commodity": commodity, "arrival_date": "01/01/2020",
                 "min_price": "1", "max_price": "3", "modal_price": "2"}]

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        for n, t in DOCS.items():
            (Path(self.tmp.name) / n).write_text(t)
        self.cfg = Config(knowledge_dir=self.tmp.name)
        self.kb = KnowledgeBase(self.tmp.name)
        self.mem = Memory(":memory:")
        self.ctx = Context(self.kb, self.mem, self.cfg)
        self.orch = Orchestrator(self.cfg, self.ctx, LLM(self.cfg), {
            "disease": DiseaseAgent(), "irrigation": IrrigationAgent(),
            "resource": ResourceAgent(), "market": MarketAgent(FakeMandi())})

    def test_rag_filters_and_metadata(self):
        hits = self.kb.search("yellow spots leaf", crop="testcrop", issuer="ICAR")
        self.assertEqual(hits[0].meta["issuer"], "ICAR")
        self.assertEqual(self.kb.search("yellow spots", crop="othercrop", issuer="ICAR"), [])

    def test_missing_details_asks_questions(self):
        r = self.orch.handle(FarmerRequest("f1", "my leaf has yellow spots"))
        self.assertEqual(r.status, "needs_info")
        self.assertEqual(len(r.questions), 2)

    def test_disease_never_confirms_without_model(self):
        r = self.orch.handle(FarmerRequest("f1", "yellow spots on leaf", crop="testcrop", district="D"))
        d = [x for x in r.results if x.agent == "disease"][0]
        self.assertTrue(d.needs_human_review)
        self.assertIn("not a diagnosis", " ".join(d.warnings))

    def test_irrigation_warns_without_moisture_reading(self):
        r = self.orch.handle(FarmerRequest("f1", "should I irrigate?", crop="testcrop", district="D"))
        i = [x for x in r.results if x.agent == "irrigation"][0]
        self.assertIn("No soil-moisture measurement", " ".join(i.warnings))

    def test_market_shows_date_and_stale_warning(self):
        r = self.orch.handle(FarmerRequest("f1", "what is the mandi price", crop="wheat", district="D"))
        m = [x for x in r.results if x.agent == "market"][0]
        self.assertIn("01/01/2020", m.summary)
        self.assertTrue(any("older than" in w for w in m.warnings))

    def test_high_impact_flag(self):
        r = self.orch.handle(FarmerRequest("f1", "should I spray pesticide on yellow leaf", crop="testcrop", district="D"))
        self.assertTrue(any("confirmation required" in f for f in r.review_flags))

    def test_memory_consent_and_deletion(self):
        with self.assertRaises(PermissionError):
            self.mem.set_profile("f1", {"crop": "x"}, consent=False)
        self.mem.set_profile("f1", {"crop": "x", "phone": "123"}, consent=True)
        self.assertEqual(self.mem.get_profile("f1"), {"crop": "x"})   # minimisation
        with self.assertRaises(ValueError):
            self.mem.add_history("f1", "price", {"v": 1})              # no time-sensitive storage
        self.mem.delete_farmer("f1")
        self.assertEqual(self.mem.get_profile("f1"), {})

if __name__ == "__main__":
    unittest.main()

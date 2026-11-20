"""Keyword (BM25) retrieval over official documents. No vector DB required;
add embeddings later if the corpus grows.

Document format (.txt / .md): optional header lines `key: value`, a blank line, then body.
Recognised keys: title, issuer, crop, region, date, url.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN = re.compile(r"[a-z0-9]+")
STOP = {"the", "a", "an", "of", "and", "or", "to", "in", "is", "are", "for", "on", "my", "with", "what", "how", "should", "i", "it", "do"}

def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP]

@dataclass
class Passage:
    text: str
    meta: dict
    score: float = 0.0

class KnowledgeBase:
    def __init__(self, directory: str, chunk_words: int = 120):
        self.directory = Path(directory)
        self.chunk_words = chunk_words
        self.passages: list[Passage] = []
        self._tf: list[Counter] = []
        self._df: Counter = Counter()
        self._avgdl = 0.0
        self.load()

    @staticmethod
    def _parse(raw: str) -> tuple[dict, str]:
        head, sep, body = raw.partition("\n\n")
        meta = {}
        for line in head.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
            else:
                return {}, raw
        return (meta, body) if sep else ({}, raw)

    def _chunk(self, body: str) -> list[str]:
        chunks, cur, n = [], [], 0
        for para in re.split(r"\n\s*\n", body.strip()):
            w = len(para.split())
            if cur and n + w > self.chunk_words:
                chunks.append("\n".join(cur)); cur, n = [], 0
            cur.append(para); n += w
        if cur:
            chunks.append("\n".join(cur))
        return chunks

    def load(self) -> None:
        self.passages, self._tf, self._df = [], [], Counter()
        if self.directory.exists():
            for f in sorted(self.directory.rglob("*")):
                if f.suffix.lower() not in {".txt", ".md"} or f.name.lower().startswith("readme"):
                    continue
                meta, body = self._parse(f.read_text(encoding="utf-8", errors="ignore"))
                meta.setdefault("title", f.stem)
                meta["file"] = str(f)
                for c in self._chunk(body):
                    self.passages.append(Passage(c, dict(meta)))
        for p in self.passages:
            tf = Counter(tokenize(p.text + " " + p.meta.get("title", "")))
            self._tf.append(tf)
            self._df.update(tf.keys())
        n = len(self.passages)
        self._avgdl = (sum(sum(t.values()) for t in self._tf) / n) if n else 0.0

    def search(self, query: str, k: int = 4, crop: str | None = None,
               issuer: str | None = None, min_score: float = 0.5) -> list[Passage]:
        q, n, k1, b = tokenize(query), len(self.passages), 1.5, 0.75
        out = []
        for p, tf in zip(self.passages, self._tf):
            pc = p.meta.get("crop", "").lower()
            if crop and pc and pc not in {"all", crop.lower()}:
                continue
            if issuer and p.meta.get("issuer", "").lower() != issuer.lower():
                continue
            dl, score = sum(tf.values()), 0.0
            for t in q:
                if t not in tf:
                    continue
                idf = math.log(1 + (n - self._df[t] + 0.5) / (self._df[t] + 0.5))
                score += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / (self._avgdl or 1)))
            if score >= min_score:
                out.append(Passage(p.text, p.meta, score))
        return sorted(out, key=lambda x: -x.score)[:k]

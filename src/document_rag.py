from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .settings import INDEX_DIR


INDEX_FILE = "factsheet_tfidf.pkl"
INDEX_VERSION = "tfidf-v2"
DEFAULT_CHUNK_SIZE = 900
DEFAULT_OVERLAP = 160
MIN_CHUNK_LENGTH = 80


@dataclass
class Chunk:
    text: str
    page: int
    chunk_id: int


class LocalVectorStore:
    def __init__(self, vectorizer: TfidfVectorizer, matrix, chunks: list[Chunk]):
        self.vectorizer = vectorizer
        self.matrix = matrix
        self.chunks = chunks

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        search_text = add_search_hints(query)
        query_vector = self.vectorizer.transform([search_text])
        scores = cosine_similarity(query_vector, self.matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        matches: list[tuple[Chunk, float]] = []
        for index in top_indices:
            score = float(scores[index])
            if score > 0:
                matches.append((self.chunks[index], score))
        return matches


def load_or_build_vector_store(pdf_path: Path, force_rebuild: bool = False) -> LocalVectorStore:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index_path = INDEX_DIR / INDEX_FILE
    signature = f"{INDEX_VERSION}::{pdf_path.resolve()}::{pdf_path.stat().st_mtime_ns}"

    if index_path.exists() and not force_rebuild:
        with index_path.open("rb") as file:
            payload = pickle.load(file)
        if payload.get("signature") == signature:
            return payload["store"]

    chunks = extract_chunks(pdf_path)
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=50000)
    matrix = vectorizer.fit_transform([chunk.text for chunk in chunks])
    store = LocalVectorStore(vectorizer=vectorizer, matrix=matrix, chunks=chunks)

    with index_path.open("wb") as file:
        pickle.dump({"signature": signature, "store": store}, file)

    return store


def extract_chunks(
    pdf_path: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    reader = PdfReader(str(pdf_path))
    chunks: list[Chunk] = []
    chunk_id = 1

    for page_number, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if not text:
            continue

        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if len(chunk_text) > MIN_CHUNK_LENGTH:
                chunks.append(Chunk(text=chunk_text, page=page_number, chunk_id=chunk_id))
                chunk_id += 1
            if end == len(text):
                break
            start = max(0, end - overlap)

    return chunks


def clean_text(text: str) -> str:
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def add_search_hints(query: str) -> str:
    """Add words commonly used in factsheets so simple TF-IDF search works better."""
    text = query.lower()
    hints: list[str] = []

    if any(term in text for term in ["who manages", "managed by", "fund manager", "manager of"]):
        hints.append("fund manager total experience equity assets debt assets arbitrage assets")

    if "sip" in text:
        hints.append(
            "SIP systematic investment plan works principle making periodic investments fixed sum "
            "recurring bank deposit Rs 500 every 15th month equity fund period three years"
        )

    if "nav" in text:
        hints.append("NAV net asset value total asset value per unit calculated every business day investor enters exits")

    if any(term in text for term in ["yield to maturity", "ytm"]):
        hints.append("Yield to Maturity YTM rate of return anticipated bond held until maturity")

    if "benchmark" in text:
        hints.append("Fund Name Benchmark benchmark index TRI")

    if any(term in text for term in ["risk", "riskometer", "risk level"]):
        hints.append("Scheme Riskometer Current risk principal very high high moderate low")

    if any(term in text for term in ["mutual fund risk", "market risk", "disclaimer", "documents carefully"]):
        hints.append(
            "MUTUAL FUND INVESTMENTS ARE SUBJECT TO MARKET RISKS READ ALL SCHEME RELATED DOCUMENTS CAREFULLY "
            "investors should consult financial advisers"
        )

    if "exit load" in text:
        hints.append("EXIT LOAD redemption switch-out units payable")

    if "investment objective" in text or "objective" in text:
        hints.append("INVESTMENT OBJECTIVE suitable for investors seeking generate long-term capital appreciation income")

    return " ".join([query, *hints])


def format_sources(results: list[tuple[Chunk, float]], preview_chars: int | None = None) -> str:
    lines = []
    for chunk, score in results:
        preview = chunk.text if preview_chars is None else chunk.text[:preview_chars]
        preview = preview.strip()
        lines.append(f"Page {chunk.page}, chunk {chunk.chunk_id}, score {score:.2f}: {preview}")
    return "\n\n".join(lines)

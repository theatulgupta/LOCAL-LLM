"""Local notebook retrieval service for offline RAG."""

from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".ipynb", ".txt", ".md", ".py"}
TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


@dataclass(frozen=True)
class RagSource:
    """Single matched chunk from the local corpus."""

    source_path: str
    chunk_index: int
    score: float
    snippet: str
    cell_type: Optional[str] = None
    cell_id: Optional[str] = None


@dataclass(frozen=True)
class RagContext:
    """Search result used to enrich prompts."""

    question: str
    context: str
    sources: List[RagSource]
    enabled: bool
    indexed_files: int
    indexed_chunks: int
    corpus_path: str


@dataclass(frozen=True)
class _Chunk:
    source_path: str
    chunk_index: int
    text: str
    token_counts: Counter[str]
    token_norm: float
    cell_type: Optional[str] = None
    cell_id: Optional[str] = None


class RagService:
    """Build and query a lightweight local retrieval index."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.corpus_path = Path(self.settings.rag_corpus_path).expanduser()
        self._lock = Lock()
        self._chunks: List[_Chunk] = []
        self._indexed_files = 0
        self._indexed_chunks = 0
        self._last_signature: Optional[tuple[int, int]] = None
        self._ready = False

    def is_enabled(self) -> bool:
        return self.settings.rag_enabled and self.corpus_path.exists()

    def ensure_index(self) -> None:
        """Refresh the index when the corpus changes."""

        if not self.is_enabled():
            return

        signature = self._build_signature()

        with self._lock:
            if self._ready and self._last_signature == signature:
                return
            self._rebuild_index(signature)

    def refresh(self) -> None:
        """Force a rebuild of the index."""

        with self._lock:
            if not self.is_enabled():
                self._clear()
                return
            self._rebuild_index(self._build_signature())

    def status(self) -> Dict[str, Any]:
        self.ensure_index()
        return {
            "enabled": self.is_enabled(),
            "ready": self._ready,
            "corpus_path": str(self.corpus_path),
            "indexed_files": self._indexed_files,
            "indexed_chunks": self._indexed_chunks,
        }

    def search(self, question: str, top_k: Optional[int] = None) -> RagContext:
        """Return the best matching chunks for a user question."""

        self.ensure_index()

        if not self.is_enabled() or not self._chunks:
            return RagContext(
                question=question,
                context="",
                sources=[],
                enabled=False,
                indexed_files=self._indexed_files,
                indexed_chunks=self._indexed_chunks,
                corpus_path=str(self.corpus_path),
            )

        query_tokens = self._tokenize(question)
        if not query_tokens:
            return RagContext(
                question=question,
                context="",
                sources=[],
                enabled=True,
                indexed_files=self._indexed_files,
                indexed_chunks=self._indexed_chunks,
                corpus_path=str(self.corpus_path),
            )

        query_counts = Counter(query_tokens)
        requested_top_k = max(1, top_k or self.settings.rag_top_k)

        scored_chunks = []
        for chunk in self._chunks:
            score = self._score(query_counts, chunk)
            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda item: item[0], reverse=True)
        selected = scored_chunks[:requested_top_k]

        sources: List[RagSource] = []
        context_blocks: List[str] = []
        remaining_chars = self.settings.rag_max_context_chars

        for score, chunk in selected:
            snippet = self._trim_text(chunk.text, remaining_chars)
            if not snippet:
                continue
            remaining_chars -= len(snippet)
            sources.append(
                RagSource(
                    source_path=chunk.source_path,
                    chunk_index=chunk.chunk_index,
                    score=round(score, 4),
                    snippet=snippet,
                    cell_type=chunk.cell_type,
                    cell_id=chunk.cell_id,
                )
            )
            context_blocks.append(
                "Source: {source}\nChunk: {chunk}\nScore: {score:.4f}\n{snippet}".format(
                    source=chunk.source_path,
                    chunk=chunk.chunk_index,
                    score=score,
                    snippet=snippet,
                )
            )

        context = "\n\n---\n\n".join(context_blocks)

        return RagContext(
            question=question,
            context=context,
            sources=sources,
            enabled=True,
            indexed_files=self._indexed_files,
            indexed_chunks=self._indexed_chunks,
            corpus_path=str(self.corpus_path),
        )

    def build_prompt(self, question: str, top_k: Optional[int] = None) -> tuple[str, RagContext]:
        """Build a context-aware prompt for the LLM."""

        context = self.search(question, top_k=top_k)
        if not context.context:
            return question, context

        prompt = (
            "You are answering a question using the user's local lab notes and notebooks. "
            "Prefer the provided context. If the context does not contain the answer, say so clearly "
            "and then give the best concise answer you can.\n\n"
            f"Local context from {context.corpus_path}:\n\n"
            f"{context.context}\n\n"
            f"Question: {question}\n\n"
            "Answer in an exam-friendly way."
        )
        return prompt, context

    def _clear(self) -> None:
        self._chunks = []
        self._indexed_files = 0
        self._indexed_chunks = 0
        self._last_signature = None
        self._ready = False

    def _rebuild_index(self, signature: tuple[int, int]) -> None:
        chunks: List[_Chunk] = []
        files = [
            path for path in self.corpus_path.rglob("*")
            if path.is_file() and self._is_indexable(path)
        ]

        for path in files:
            try:
                chunks.extend(self._extract_file_chunks(path))
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Failed to index %s: %s", path, exc)

        self._chunks = chunks
        self._indexed_files = len(files)
        self._indexed_chunks = len(chunks)
        self._last_signature = signature
        self._ready = True
        logger.info(
            "Indexed %s files into %s chunks from %s",
            self._indexed_files,
            self._indexed_chunks,
            self.corpus_path,
        )

    def _build_signature(self) -> tuple[int, int]:
        if not self.corpus_path.exists():
            return (0, 0)

        latest_mtime = 0
        file_count = 0
        for path in self.corpus_path.rglob("*"):
            if path.is_file() and self._is_indexable(path):
                file_count += 1
                try:
                    latest_mtime = max(latest_mtime, int(path.stat().st_mtime))
                except OSError:
                    continue
        return file_count, latest_mtime

    def _is_indexable(self, path: Path) -> bool:
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            return False
        try:
            relative_parts = path.relative_to(self.corpus_path).parts
        except ValueError:
            return False
        return not any(part.startswith(".") for part in relative_parts)

    def _extract_file_chunks(self, path: Path) -> List[_Chunk]:
        relative_path = str(path.relative_to(self.corpus_path))
        if path.suffix.lower() == ".ipynb":
            blocks = self._extract_notebook_blocks(path)
        else:
            blocks = self._extract_text_blocks(path)

        chunks: List[_Chunk] = []
        for block_index, block in enumerate(blocks):
            for chunk_index, chunk_text in enumerate(self._split_text(block["text"])):
                token_counts = Counter(self._tokenize(chunk_text))
                if not token_counts:
                    continue
                token_norm = math.sqrt(sum(count * count for count in token_counts.values()))
                chunks.append(
                    _Chunk(
                        source_path=relative_path,
                        chunk_index=block_index * 100 + chunk_index,
                        text=self._format_block(relative_path, block, chunk_text),
                        token_counts=token_counts,
                        token_norm=token_norm,
                        cell_type=block.get("cell_type"),
                        cell_id=block.get("cell_id"),
                    )
                )
        return chunks

    def _extract_notebook_blocks(self, path: Path) -> List[Dict[str, Any]]:
        with path.open("r", encoding="utf-8") as handle:
            notebook = json.load(handle)

        blocks: List[Dict[str, Any]] = []
        for index, cell in enumerate(notebook.get("cells", []), start=1):
            source = self._normalize_lines(cell.get("source", []))
            outputs = self._extract_outputs(cell.get("outputs", []))
            combined = "\n".join(part for part in [source, outputs] if part).strip()
            if not combined:
                continue
            blocks.append(
                {
                    "cell_type": cell.get("cell_type", "unknown"),
                    "cell_id": cell.get("metadata", {}).get("id") or f"cell-{index}",
                    "text": combined,
                }
            )
        return blocks

    def _extract_text_blocks(self, path: Path) -> List[Dict[str, Any]]:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            return []
        return [
            {
                "cell_type": path.suffix.lstrip("."),
                "cell_id": path.name,
                "text": text,
            }
        ]

    def _extract_outputs(self, outputs: Iterable[Dict[str, Any]]) -> str:
        parts: List[str] = []
        for output in outputs or []:
            text_items = output.get("text")
            if isinstance(text_items, list):
                parts.extend(str(item).rstrip() for item in text_items if str(item).strip())
            elif isinstance(text_items, str) and text_items.strip():
                parts.append(text_items.strip())

            data = output.get("data", {})
            plain = data.get("text/plain")
            if isinstance(plain, list):
                parts.extend(str(item).rstrip() for item in plain if str(item).strip())
            elif isinstance(plain, str) and plain.strip():
                parts.append(plain.strip())

        return "\n".join(parts).strip()

    def _normalize_lines(self, lines: Iterable[str]) -> str:
        return "".join(str(line) for line in lines).strip()

    def _split_text(self, text: str) -> List[str]:
        words = text.split()
        if len(words) <= self.settings.rag_chunk_size:
            return [text.strip()]

        chunks: List[str] = []
        step = max(1, self.settings.rag_chunk_size - self.settings.rag_chunk_overlap)
        for start in range(0, len(words), step):
            window = words[start : start + self.settings.rag_chunk_size]
            if not window:
                continue
            chunks.append(" ".join(window).strip())
        return chunks

    def _tokenize(self, text: str) -> List[str]:
        return TOKEN_PATTERN.findall(text.lower())

    def _score(self, query_counts: Counter[str], chunk: _Chunk) -> float:
        overlap = set(query_counts).intersection(chunk.token_counts)
        if not overlap or chunk.token_norm == 0:
            return 0.0

        dot_product = sum(query_counts[token] * chunk.token_counts[token] for token in overlap)
        query_norm = math.sqrt(sum(count * count for count in query_counts.values()))
        if query_norm == 0:
            return 0.0
        return dot_product / (query_norm * chunk.token_norm)

    def _trim_text(self, text: str, remaining_chars: int) -> str:
        if remaining_chars <= 0:
            return ""
        trimmed = text[:remaining_chars].strip()
        if len(text) > remaining_chars:
            trimmed = trimmed.rsplit(" ", 1)[0].strip() or trimmed
        return trimmed

    def _format_block(self, relative_path: str, block: Dict[str, Any], chunk_text: str) -> str:
        header = [
            f"File: {relative_path}",
            f"Cell type: {block.get('cell_type', 'unknown')}",
            f"Cell id: {block.get('cell_id', 'unknown')}",
        ]
        return "\n".join(header + ["", chunk_text.strip()]).strip()


_rag_service: Optional[RagService] = None


def get_rag_service() -> RagService:
    """Get or create the singleton RAG service."""

    global _rag_service
    if _rag_service is None:
        _rag_service = RagService()
    return _rag_service

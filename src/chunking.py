from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        sentences = [s.strip() for s in re.split(r"\. |! |\? |\.\n", text.strip()) if s.strip()]
        if not sentences:
            return []

        step = self.max_sentences_per_chunk
        return [" ".join(sentences[i : i + step]).strip() for i in range(0, len(sentences), step)]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        if separator == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        parts = current_text.split(separator)
        if len(parts) == 1:
            return self._split(current_text, remaining_separators[1:])

        chunks: list[str] = []
        current_chunk = parts[0]

        for part in parts[1:]:
            candidate = current_chunk + separator + part
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
                continue

            if current_chunk:
                chunks.extend(self._split(current_chunk, remaining_separators[1:]))
            current_chunk = part

        if current_chunk:
            chunks.extend(self._split(current_chunk, remaining_separators[1:]))

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    
    dot_product = _dot(vec_a, vec_b)
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)

class CustomRecipeChunker:
    """
    Custom chunking strategy for Vietnamese cooking recipe documents.

    Design rationale: Recipe documents have a predictable semantic structure
    (Introduce → Ingredients → Step 1..N → Finally). Splitting exactly on
    these section headers preserves complete, coherent semantic units — an
    'Ingredients' chunk contains all ingredients, a 'Step N' chunk contains
    one cooking action. This maps naturally to recipe-related queries such as
    "what ingredients are needed?" or "how do I grill the snails?".

    Sections detected:
        Introduce:, Ingredients:, Process:, Step 1:..Step N:, Finally:
    """

    # Matches known recipe section headers
    _HEADER_PATTERN = re.compile(r"(Introduce:|Ingredients:|Process:|Step \d+:|Finally:)")

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        parts = self._HEADER_PATTERN.split(text)
        # parts = [pre-text, header1, body1, header2, body2, ...]
        chunks: list[str] = []
        for i in range(1, len(parts) - 1, 2):
            header = parts[i].strip()
            body = parts[i + 1].strip()
            if body:
                chunks.append(f"{header}\n{body}")

        # If no headers found, fall back to returning the whole text as one chunk
        return chunks if chunks else [text.strip()]

class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200, over_lap: int = 50) -> dict:
        sentence_count = max(1, chunk_size // 100)
        chunkers = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=over_lap),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=sentence_count),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in chunkers.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            comparison[name] = {
                "count": count,
                "avg_length": (sum(len(chunk) for chunk in chunks) / count) if count else 0.0,
                "chunks": chunks,
            }
        return comparison

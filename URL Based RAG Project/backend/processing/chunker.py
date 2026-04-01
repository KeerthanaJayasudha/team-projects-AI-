import re
from typing import List

import tiktoken

from backend.utils.config import CHUNK_SIZE, CHUNK_OVERLAP
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class TextChunker:
    """
    Token-based chunker with light structure awareness.

    Improvements:
    - Uses config values by default
    - Cleans noisy whitespace
    - Preserves paragraph boundaries when possible
    - Falls back to sliding token window for very long paragraphs
    - Skips useless tiny chunks
    """

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
        encoding_name: str = "cl100k_base"
    ):
        if overlap >= chunk_size:
            raise ValueError("Overlap must be smaller than chunk size")

        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoding = tiktoken.get_encoding(encoding_name)

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _token_count(self, text: str) -> int:
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def _split_long_text_with_sliding_window(self, text: str) -> List[str]:
        tokens = self.encoding.encode(text)
        chunks = []

        step = self.chunk_size - self.overlap

        for i in range(0, len(tokens), step):
            chunk_tokens = tokens[i:i + self.chunk_size]

            if not chunk_tokens:
                continue

            # skip very tiny token slices
            if len(chunk_tokens) < 40:
                continue

            chunk_text = self.encoding.decode(chunk_tokens).strip()

            if not chunk_text:
                continue

            chunks.append(chunk_text)

            if i + self.chunk_size >= len(tokens):
                break

        return chunks

    def _deduplicate_chunks(self, chunks: List[str]) -> List[str]:
        unique_chunks = []
        seen = set()

        for chunk in chunks:
            normalized = re.sub(r"\s+", " ", chunk).strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique_chunks.append(chunk)

        return unique_chunks

    def chunk_text(self, text: str) -> List[str]:
        if not text:
            return []

        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return []

        paragraphs = [
            p.strip()
            for p in cleaned_text.split("\n\n")
            if p and p.strip()
        ]

        if not paragraphs:
            return self._split_long_text_with_sliding_window(cleaned_text)

        chunks = []
        current_parts = []
        current_token_count = 0

        for para in paragraphs:
            para_tokens = self._token_count(para)

            # If one paragraph itself is too large, flush current chunk first
            if para_tokens > self.chunk_size:
                if current_parts:
                    merged = "\n\n".join(current_parts).strip()
                    if self._token_count(merged) >= 40:
                        chunks.append(merged)
                    current_parts = []
                    current_token_count = 0

                long_para_chunks = self._split_long_text_with_sliding_window(para)
                chunks.extend(long_para_chunks)
                continue

            # If adding this paragraph exceeds chunk size, flush current chunk
            if current_token_count + para_tokens > self.chunk_size and current_parts:
                merged = "\n\n".join(current_parts).strip()
                if self._token_count(merged) >= 40:
                    chunks.append(merged)

                # build overlap from tail of previous chunk
                if self.overlap > 0 and merged:
                    merged_tokens = self.encoding.encode(merged)
                    overlap_tokens = merged_tokens[-self.overlap:]
                    overlap_text = self.encoding.decode(overlap_tokens).strip()

                    current_parts = [overlap_text] if overlap_text else []
                    current_token_count = self._token_count(overlap_text)
                else:
                    current_parts = []
                    current_token_count = 0

            current_parts.append(para)
            current_token_count += para_tokens

        if current_parts:
            merged = "\n\n".join(current_parts).strip()
            if self._token_count(merged) >= 40:
                chunks.append(merged)

        chunks = self._deduplicate_chunks(chunks)

        logger.info(
            f"Chunking complete | chunk_size={self.chunk_size} | "
            f"overlap={self.overlap} | total_chunks={len(chunks)}"
        )

        return chunks
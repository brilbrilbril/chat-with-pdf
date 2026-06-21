from __future__ import annotations
import os
import re

MIN_CHUNK_WORDS = 30
SENTENCE_END = re.compile(r'(?<=[.!?])\s+')

def _word_count(text: str) -> int:
    return len(text.split())


def _split_sentences(text: str) -> list[str]:
    parts = SENTENCE_END.split(text)
    return [p.strip() for p in parts if p.strip()]


def _merge_small_chunks(chunks: list[str], min_words: int) -> list[str]:
    if not chunks:
        return []

    merged: list[str] = []
    buffer = ""

    for chunk in chunks:
        if buffer:
            candidate = buffer + " " + chunk
        else:
            candidate = chunk

        if _word_count(candidate) < min_words:
            buffer = candidate
        else:
            merged.append(candidate)
            buffer = ""

    if buffer:
        if merged:
            merged[-1] = merged[-1] + " " + buffer
        else:
            merged.append(buffer)

    return merged



def recursive_split(
    text: str,
    chunk_size: int = int(os.getenv('CHUNK_SIZE')),
    overlap: int = int(os.getenv('CHUNK_OVERLAP')),
    _separators: list[str] | None = None,
) -> list[str]:
    if _separators is None:
        _separators = ["\n\n", None, "\n", " "]

    sep = _separators[0]
    remaining = _separators[1:]

    if sep is None:
        parts = _split_sentences(text)
    else:
        parts = [p.strip() for p in text.split(sep) if p.strip()]

    if not parts:
        return []

    chunks: list[str] = []
    current_words: list[str] = []

    for part in parts:
        part_words = part.split()
        candidate = current_words + part_words

        if len(candidate) <= chunk_size:
            current_words = candidate
        else:
            if current_words:
                chunks.append(" ".join(current_words))

            if len(part_words) > chunk_size:
                if remaining:
                    sub = recursive_split(part, chunk_size, overlap, remaining)
                    chunks.extend(sub)
                else:
                    chunks.extend(_hard_split(part, chunk_size, overlap))
                current_words = []
            else:
                if chunks:
                    prev_words = chunks[-1].split()
                    current_words = prev_words[-overlap:] + part_words
                else:
                    current_words = part_words

    if current_words:
        chunks.append(" ".join(current_words))

    chunks = [c for c in chunks if c.strip()]
    return _merge_small_chunks(chunks, MIN_CHUNK_WORDS)


def _hard_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks

def structure_aware_split(
    sections: list[tuple[str | None, str]],
    chunk_size: int = int(os.getenv('CHUNK_SIZE')),
    overlap: int = int(os.getenv('CHUNK_OVERLAP')),
) -> list[str]:
    chunks: list[str] = []

    for heading, body in sections:
        prefix = f"{heading}\n" if heading else ""
        body = body.strip()

        if not body and not heading:
            continue

        full_text = (prefix + body).strip()

        if _word_count(full_text) <= chunk_size:
            chunks.append(full_text)
            continue
        
        body_chunks = recursive_split(body, chunk_size, overlap)

        for bc in body_chunks:
            chunk = (prefix + bc).strip()
            if chunk:
                chunks.append(chunk)

    return _merge_small_chunks(chunks, MIN_CHUNK_WORDS)
from __future__ import annotations

def recursive_split(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    _separators: list[str] | None = None,
) -> list[str]:
    if _separators is None:
        _separators = ["\n\n", "\n", ". ", " "]

    sep = _separators[0]
    remaining_seps = _separators[1:]

    parts = text.split(sep) if sep else list(text)
    chunks: list[str] = []
    current_words: list[str] = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        candidate_words = current_words + part.split()

        if len(candidate_words) <= chunk_size:
            current_words = candidate_words
        else:
            if current_words:
                chunks.append(" ".join(current_words))

            part_words = part.split()
            if len(part_words) > chunk_size:
                if remaining_seps:
                    sub_chunks = recursive_split(
                        part, chunk_size, overlap, remaining_seps
                    )
                    chunks.extend(sub_chunks)
                    current_words = []
                else:
                    for fc in _fixed_word_split(part, chunk_size, overlap):
                        chunks.append(fc)
                    current_words = []
            else:
                if chunks:
                    prev_words = chunks[-1].split()
                    current_words = prev_words[-overlap:] + part_words
                else:
                    current_words = part_words

    if current_words:
        chunks.append(" ".join(current_words))

    return [c for c in chunks if c.strip()]


def _fixed_word_split(text: str, chunk_size: int, overlap: int) -> list[str]:
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
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    chunks: list[str] = []

    for heading, body in sections:
        prefix = f"{heading}\n" if heading else ""
        full_text = (prefix + body).strip()

        if not full_text:
            continue

        word_count = len(full_text.split())

        if word_count <= chunk_size:
            chunks.append(full_text)
        else:
            body_chunks = recursive_split(body.strip(), chunk_size, overlap)
            for bc in body_chunks:
                chunks.append((prefix + bc).strip())

    return [c for c in chunks if c.strip()]
from __future__ import annotations
import os
import re

import pdfplumber

from src.domain.interfaces.extractor import IBaseExtractor
from src.domain.entities.chunk import RawChunk
from src.infrastructure.extractors.chunker import structure_aware_split

# legal docs detection
_NUMBERED = re.compile(
    r'^(\d+[\.\d]*\.?|[A-Z][\.\)]|BAB\s+[IVXLC\d]+|PASAL\s+\d+)\s+\S',
    re.IGNORECASE,
)

def _is_heading(line: str) -> bool:
    line = line.strip()
    if not line:
        return False
    words = line.split()
    if len(words) > 12:
        return False
    if line[-1] in ".?!,:;":
        return False
    if _NUMBERED.match(line):
        return True
    if line.isupper() and len(words) >= 1:
        return True
    if line.istitle() and len(words) <= 8:
        return True
    return False


class PDFExtractor(IBaseExtractor):
    def __init__(self, chunk_size: int = int(os.getenv('CHUNK_SIZE')), chunk_overlap: int = int(os.getenv('CHUNK_OVERLAP'))):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract(self, file_path: str) -> list[RawChunk]:
        page_lines: list[tuple[str, int]] = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_num = page.page_number
                text = page.extract_text() or ""

                tables = page.extract_tables()
                table_parts = []
                for table in tables:
                    rows = []
                    for row in table:
                        cleaned = [cell or "" for cell in row]
                        rows.append(" | ".join(cleaned))
                    table_parts.append("\n".join(rows))
                if table_parts:
                    text += "\n\n" + "\n\n".join(table_parts)

                for line in text.splitlines():
                    stripped = line.strip()
                    if stripped:
                        page_lines.append((stripped, page_num))

        if not page_lines:
            return []

        sections: list[tuple[str | None, str, int]] = []
        current_heading: str | None = None
        current_body: list[str] = []
        current_page: int = page_lines[0][1]

        for line, page_num in page_lines:
            if _is_heading(line):
                if current_body or current_heading:
                    sections.append((
                        current_heading,
                        "\n".join(current_body),
                        current_page,
                    ))
                current_heading = line
                current_body = []
                current_page = page_num
            else:
                if not current_body:
                    current_page = page_num
                current_body.append(line)

        if current_body or current_heading:
            sections.append((current_heading, "\n".join(current_body), current_page))

        raw_chunks: list[RawChunk] = []
        chunk_index = 0

        for heading, body, page_num in sections:
            section_pairs = [(heading, body)]
            texts = structure_aware_split(section_pairs, self.chunk_size, self.chunk_overlap)

            for text in texts:
                raw_chunks.append(RawChunk(
                    text=text,
                    page_number=page_num,
                    chunk_index=chunk_index,
                ))
                chunk_index += 1

        return raw_chunks
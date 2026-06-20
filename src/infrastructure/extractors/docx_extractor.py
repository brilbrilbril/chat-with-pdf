from __future__ import annotations

from docx import Document as DocxDocument
from docx.oxml.ns import qn

from src.domain.entities.chunk import RawChunk
from src.domain.interfaces.extractor import IBaseExtractor
from src.infrastructure.extractors.chunker import structure_aware_split

_HEADING_STYLES = {
    "heading 1", "heading 2", "heading 3", "heading 4",
    "heading 5", "heading 6", "title", "subtitle",
    "judul", "sub judul",
}


def _is_heading_style(style_name: str) -> bool:
    return style_name.lower() in _HEADING_STYLES


def _extract_table_text(table) -> str:
    rows = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


class DOCXExtractor(IBaseExtractor):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract(self, file_path: str) -> list[RawChunk]:
        doc = DocxDocument(file_path)

        body_elements = self._iter_block_items(doc)

        sections: list[tuple[str | None, str]] = []
        current_heading: str | None = None
        current_body: list[str] = []

        for element_type, content in body_elements:
            if element_type == "heading":
                if current_body or current_heading:
                    sections.append((current_heading, "\n".join(current_body)))
                current_heading = content
                current_body = []
            else:
                if content.strip():
                    current_body.append(content)
                    
        if current_body or current_heading:
            sections.append((current_heading, "\n".join(current_body)))

        # fallback 
        if not sections:
            all_text = "\n".join(
                c for _, c in self._iter_block_items(doc) if c.strip()
            )
            sections = [(None, all_text)]

        raw_chunks: list[RawChunk] = []
        chunk_index = 0

        texts = structure_aware_split(sections, self.chunk_size, self.chunk_overlap)
        for text in texts:
            raw_chunks.append(RawChunk(
                text=text,
                chunk_index=chunk_index,
            ))
            chunk_index += 1

        return raw_chunks

    @staticmethod
    def _iter_block_items(doc: DocxDocument):
        body = doc.element.body
        for child in body:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if tag == "p":
                from docx.text.paragraph import Paragraph
                para = Paragraph(child, doc)
                text = para.text.strip()
                if not text:
                    continue
                style_name = para.style.name if para.style else ""
                if _is_heading_style(style_name):
                    yield ("heading", text)
                else:
                    yield ("paragraph", text)

            elif tag == "tbl":
                from docx.table import Table
                table = Table(child, doc)
                yield ("table", _extract_table_text(table))
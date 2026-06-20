import csv

from src.domain.interfaces.extractor import IBaseExtractor
from src.domain.entities.chunk import RawChunk

class CSVExtractor(IBaseExtractor):
    def __init__(self, rows_per_chunk: int = 40):
        self.rows_per_chunk = rows_per_chunk

    def extract(self, file_path: str) -> list[RawChunk]:
        raw_chunks: list[RawChunk] = []
        chunk_index = 0

        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            all_rows = list(reader)

        if not all_rows:
            return []

        header = all_rows[0]
        header_text = " | ".join(header)
        data_rows = all_rows[1:]

        if not data_rows:
            raw_chunks.append(RawChunk(
                text=header_text,
                row_start=1,
                row_end=1,
                chunk_index=0,
            ))
            return raw_chunks

        for batch_start in range(0, len(data_rows), self.rows_per_chunk):
            batch = data_rows[batch_start: batch_start + self.rows_per_chunk]
            row_start = batch_start + 2
            row_end = row_start + len(batch) - 1

            row_texts = [" | ".join(row) for row in batch]
            chunk_text = (
                f"Rows {row_start}-{row_end}\n"
                f"{header_text}\n"
                + "\n".join(row_texts)
            )

            raw_chunks.append(RawChunk(
                text=chunk_text,
                row_start=row_start,
                row_end=row_end,
                chunk_index=chunk_index,
            ))
            chunk_index += 1

        return raw_chunks
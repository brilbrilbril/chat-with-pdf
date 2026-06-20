from dataclasses import dataclass
from typing import Optional

@dataclass
class ChunkSource:
    file_name: str
    file_type: str
    page_number: Optional[int] = None       # pdf
    slide_number: Optional[int] = None      # ppt
    sheet_name: Optional[str] = None        # xlsx
    row_start: Optional[int] = None         # xlsx/csv
    row_end: Optional[int] = None           # xlsx/csv
    chunk_index: int = 0
 
    def to_citation(self) -> str:
        filename = f"{self.file_name}"
        if self.page_number is not None:
            return f"{filename}: page {self.page_number}"
        if self.slide_number is not None:
            return f"{filename}: slide {self.slide_number}"
        if self.sheet_name and self.row_start is not None:
            return f"{filename}: sheet '{self.sheet_name}', rows: {self.row_start}-{self.row_end}"
        if self.sheet_name:
            return f"{filename}: sheet '{self.sheet_name}'"
        return f"{filename}: chunk {self.chunk_index}"
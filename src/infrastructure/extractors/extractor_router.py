import os


from src.domain.interfaces.extractor import IBaseExtractor
from src.domain.entities.chunk import RawChunk

from src.infrastructure.extractors.csv_extractor import CSVExtractor
from src.infrastructure.extractors.docx_extractor import DOCXExtractor
from src.infrastructure.extractors.pdf_extractor import PDFExtractor
from src.infrastructure.extractors.ppt_extractor import PPTXExtractor
from src.infrastructure.extractors.txt_extractor import TXTExtractor
from src.infrastructure.extractors.xlsx_extractor import XLSXExtractor


EXTENSION_MAP: dict[str, type[IBaseExtractor]] = {
    ".pdf": PDFExtractor,
    ".docx": DOCXExtractor,
    ".pptx": PPTXExtractor,
    ".xlsx": XLSXExtractor,
    ".csv": CSVExtractor,
    ".txt": TXTExtractor,
}

SUPPORTED_EXTENSIONS = set(EXTENSION_MAP.keys())


def get_file_type(file_name: str) -> str:
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file format: '{ext}'. Supported: {SUPPORTED_EXTENSIONS}")
    return ext.lstrip(".")


def extract(file_path: str, **extractor_kwargs) -> list[RawChunk]:
    ext = os.path.splitext(file_path)[1].lower()
    extractor_cls = EXTENSION_MAP.get(ext)

    if extractor_cls is None:
        raise ValueError(f"No extractor for extension '{ext}'")

    extractor = extractor_cls(**extractor_kwargs)
    return extractor.extract(file_path)
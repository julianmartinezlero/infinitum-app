from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Gestion:
    year: str
    path: Path

@dataclass
class Client:
    name: str
    path: Path
    gestiones: list[Gestion]

@dataclass
class FileRecord:
    client_name: str
    gestion_year: str
    original_path: Path
    dbf_type: str

@dataclass
class ProcessResult:
    success: bool
    message: str
    processed_files: int
    errors: list[str]

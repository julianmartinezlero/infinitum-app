from pathlib import Path
from typing import Iterator
from dbfread import DBF
from utils.logger import log

class DBFRepository:
    def iter_records(self, file_path: Path) -> Iterator[dict]:
        """
        Reads a DBF file and yields records one by one to avoid massive memory usage.
        Handles text decoding explicitly if standard options fail.
        """
        log.debug(f"Opening DBF file: {file_path}")
        try:
            # We use char_decode_errors='ignore' to prevent crashing on bad characters
            table = DBF(str(file_path), load=False, char_decode_errors='ignore')
            for record in table:
                yield dict(record)
        except Exception as e:
            log.error(f"Failed to read DBF at {file_path}: {str(e)}")
            raise e

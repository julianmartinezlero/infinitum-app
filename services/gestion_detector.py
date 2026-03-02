import re
from typing import Optional
from utils.logger import log

class GestionDetectorService:
    def __init__(self, regex_pattern: str):
        self.regex_pattern = regex_pattern

    def extract_gestion(self, folder_name: str) -> Optional[str]:
        """
        Extracts the year (gestion) from the folder name using the configured regex.
        If a 2-digit year is found (e.g., '23'), it converts it to '2023'.
        """
        try:
            match = re.search(self.regex_pattern, folder_name)
            log.debug(self.regex_pattern)
            log.debug(match)
            if match:
                year_str = match.group(0)
                if len(year_str) == 2:
                    return f"20{year_str}"
                return year_str
            return None
        except Exception as e:
            log.error(f"Error extracting gestion from {folder_name}: {str(e)}")
            return None

import os
from pathlib import Path
from models.domain import Client, Gestion
from services.gestion_detector import GestionDetectorService
from utils.logger import log

class DirectoryScannerService:
    TARGET_FILES = {"cn_pctas.dbf", "cn_trans.dbf", "cn_transb.dbf", "cn_transm.dbf"}

    def __init__(self, gestion_detector: GestionDetectorService):
        self.gestion_detector = gestion_detector

    def scan_root(self, root_path: Path) -> list[Client]:
        """
        Scans the root path to find Clients and their respective Gestiones.
        """
        clients = []
        if not root_path.exists() or not root_path.is_dir():
            log.error(f"Root path {root_path} does not exist or is not a directory.")
            return clients

        log.info(f"Scanning root directory: {root_path}")
        
        # 1st Level: Clients
        for client_dir in root_path.iterdir():
            if not client_dir.is_dir():
                continue
                
            client_name = client_dir.name
            log.debug(f"Found client candidate: {client_name}")
            
            # 2nd Level: Recursively find gestiones
            gestiones = self._find_gestiones_recursively(client_dir)
            print(gestiones)
            
            if gestiones:
                clients.append(Client(name=client_name, path=client_dir, gestiones=gestiones))
                log.info(f"Client '{client_name}' registered with {len(gestiones)} gestiones.")

        return clients

    def _find_gestiones_recursively(self, current_path: Path) -> list[Gestion]:
        """
        Looks for gestion folders at the immediate level (2nd level).
        Once a gestion year is identified, it maps it to the folder containing the actual DBF files.
        """
        log.debug(f"Scanning for 'gestiones' directly inside: {current_path}")
        gestiones = []
        try:
            for item in current_path.iterdir():
                if item.is_dir():
                    year = self.gestion_detector.extract_gestion(item.name)
                    if year:
                        # Find the directory containing DBFs inside this gestion folder
                        dbf_dir = self._find_dir_with_dbfs(item)
                        if dbf_dir:
                            log.debug(f"Found gestion '{year}' related to DBFs at {dbf_dir}")
                            gestiones.append(Gestion(year=year, path=dbf_dir))
                        else:
                            log.debug(f"Gestion folder {item} found, but no DBFs found inside.")
        except PermissionError:
            log.warning(f"Permission denied accessing {current_path}")
        except Exception as e:
            log.error(f"Error scanning {current_path}: {str(e)}")
            
        return gestiones

    def _find_dir_with_dbfs(self, start_path: Path) -> Path | None:
        """Recursively checks and returns the first directory that contains target DBFs."""
        if self._contains_target_dbfs(start_path):
            return start_path
            
        try:
            for item in start_path.iterdir():
                if item.is_dir():
                    res = self._find_dir_with_dbfs(item)
                    if res:
                        return res
        except Exception:
            pass
        return None

    def _contains_target_dbfs(self, path: Path) -> bool:
        """Check if the directory contains at least one of the target DBF files."""
        try:
            files_in_dir = {f.name.lower() for f in path.iterdir() if f.is_file()}
            return bool(self.TARGET_FILES.intersection(files_in_dir))
        except Exception:
            return False

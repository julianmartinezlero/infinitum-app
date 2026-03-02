import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from services.gestion_detector import GestionDetectorService
from services.directory_scanner import DirectoryScannerService

detector = GestionDetectorService(r"\b(20[0-9]{2}|[0-9]{2})\b")
scanner = DirectoryScannerService(detector)
clients = scanner.scan_root(Path(r"E:\Projects\P_Files\dumm_data"))

for client in clients:
    print(f"Client: {client.name}")
    for g in client.gestiones:
        print(f"  Gestion: {g.year} -> {g.path}")

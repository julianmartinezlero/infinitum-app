from PySide6.QtCore import QThread, Signal
from pathlib import Path
from models.domain import ProcessResult
from services.process_orchestrator import ProcessOrchestrator
from services.export_service import ExportStrategy
from utils.logger import log

class ProcessWorker(QThread):
    # Signals to communicate with the main GUI thread
    progress_updated = Signal(int, int, str)
    process_finished = Signal(object) # ProcessResult
    error_occurred = Signal(str)

    def __init__(self, orchestrator: ProcessOrchestrator, root_path: Path, export_strategy: ExportStrategy):
        super().__init__()
        self.orchestrator = orchestrator
        self.root_path = root_path
        self.export_strategy = export_strategy

    def run(self):
        """
        Executes the overall processing in this background thread.
        """
        try:
            log.info(f"Worker started processing for {self.root_path}")
            
            # Wrapper to emit progress back to UI
            def callback(current: int, total: int, step_desc: str):
                self.progress_updated.emit(current, total, step_desc)

            result = self.orchestrator.run_process(self.root_path, self.export_strategy, callback)
            self.process_finished.emit(result)
            
        except Exception as e:
            error_msg = f"Unexpected error in background worker: {str(e)}"
            log.error(error_msg)
            self.error_occurred.emit(error_msg)

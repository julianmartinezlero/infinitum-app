from pathlib import Path
from typing import Callable
from services.directory_scanner import DirectoryScannerService
from repositories.dbf_repository import DBFRepository
from services.polars_transformer import PolarsTransformerService
from services.master_file_builder import MasterFileBuilderService
from services.export_service import ExportStrategy
from models.domain import ProcessResult
from utils.logger import log


class ProcessOrchestrator:
    def __init__(self,
                 directory_scanner: DirectoryScannerService,
                 dbf_repo: DBFRepository,
                 transformer: PolarsTransformerService,
                 master_builder: MasterFileBuilderService):
        self.directory_scanner = directory_scanner
        self.dbf_repo = dbf_repo
        self.transformer = transformer
        self.master_builder = master_builder

    def run_process(self, root_path: Path, export_strategy: ExportStrategy, progress_callback: Callable[[int, int, str], None]) -> ProcessResult:
        """
        Orchestrates the entire flow:
        1. Scans directories
        2. Iterates over DBFs
        3. Transforms with Polars
        4. Consolidates
        5. Exports
        """
        log.info(f"Starting process orchestration for root: {root_path}")
        errors = []
        clients = self.directory_scanner.scan_root(root_path)
        
        if not clients:
            msg = "No valid clients found in the given directory on proces Orchest."
            log.warning(msg)
            return ProcessResult(success=False, message=msg, processed_files=0, errors=errors)

        # Count total expected files for progress calculation
        total_files = 0
        for c in clients:
            for g in c.gestiones:
                # Approximate 4 files per gestion
                total_files += 4
        
        processed_count = 0
        
        for client in clients:
            for gestion in client.gestiones:
                for target_dbf in self.directory_scanner.TARGET_FILES:
                    dbf_path = gestion.path / target_dbf
                    if not dbf_path.exists():
                        log.debug(f"DBF {target_dbf} not found in {gestion.path}")
                        continue
                        
                    try:
                        progress_callback(processed_count, total_files, f"Processing {client.name} - {gestion.year} ({target_dbf})")
                        
                        log.info(f"Processing {dbf_path}")
                        records_iterator = self.dbf_repo.iter_records(dbf_path)
                        df = self.transformer.transform_records(records_iterator, client.name, gestion.year, dbf_path)
                        
                        if not df.is_empty():
                            dbf_type = target_dbf.split('.')[0] # e.g. 'cn_pctas'
                            self.master_builder.append_data(dbf_type, df)
                            processed_count += 1
                    except Exception as e:
                        err_msg = f"Failed processing {dbf_path}: {str(e)}"
                        log.error(err_msg)
                        errors.append(err_msg)

        # Consolidate and export
        progress_callback(processed_count, total_files, "Building Master CSV files...")
        master_files = self.master_builder.build_master_files()
        
        if not master_files:
            msg = "Processing completed but no master files were generated."
            log.warning(msg)
            return ProcessResult(success=True, message=msg, processed_files=processed_count, errors=errors)
            
        progress_callback(processed_count, total_files, "Exporting Master files...")
        export_success = True
        for name, path in master_files.items():
            success = export_strategy.export(path, path.name)
            if not success:
                errors.append(f"Export failed for {path.name}")
                export_success = False

        self.master_builder.cleanup()
        
        final_message = "Process completed successfully." if export_success else "Process finished with some export errors."
        progress_callback(total_files, total_files, "Done!")
        
        return ProcessResult(
            success=export_success,
            message=final_message,
            processed_files=processed_count,
            errors=errors
        )

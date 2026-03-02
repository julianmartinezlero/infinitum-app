import os
from pathlib import Path
from typing import Dict, List
import polars as pl
from utils.logger import log

class MasterFileBuilderService:
    def __init__(self, temp_dir: str = ".temp_masters"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        # Store lists of DataFrames per DBF type to union memory-efficiently later
        self._frames_buffer: Dict[str, List[pl.DataFrame]] = {}

    def append_data(self, dbf_type: str, df: pl.DataFrame):
        """
        Appends a transformed DataFrame to the specific DBF group buffer.
        """
        if df.is_empty():
            return
            
        group = dbf_type.lower()
        if group not in self._frames_buffer:
            self._frames_buffer[group] = []
        
        self._frames_buffer[group].append(df)
        log.debug(f"Buffered {len(df)} rows for {group}")

    def build_master_files(self) -> Dict[str, Path]:
        """
        Unions all dataframes per group and writes them to local temporary CSVs.
        Returns a dictionary mapping dbf_type to the temp CSV path.
        """
        master_paths = {}
        log.info("Starting master file consolidation...")
        
        for dbf_type, frames in self._frames_buffer.items():
            if not frames:
                continue

            try:
                # Vertical union
                log.info(f"Consolidating {len(frames)} dataframes for {dbf_type}")
                
                # We align columns automatically if there are variations, using diagonal_concat
                # in modern polars it's pl.concat(..., how="diagonal")
                master_df = pl.concat(frames, how="diagonal_relaxed")
                
                master_filename = f"maestro_{dbf_type}.csv"
                out_path = self.temp_dir / master_filename
                
                # Write to CSV
                master_df.write_csv(str(out_path))
                master_paths[dbf_type] = out_path
                
                log.success(f"Successfully generated {out_path} with {len(master_df)} total rows.")
            except Exception as e:
                log.error(f"Failed to consolidate {dbf_type}: {str(e)}")
        
        return master_paths

    def cleanup(self):
        """Clears memory buffers."""
        self._frames_buffer.clear()
        # Optionally, remove temp UI files post-export

import datetime
from pathlib import Path
from typing import Iterator
import polars as pl
from utils.logger import log

class PolarsTransformerService:
    def transform_records(self, records: Iterator[dict], client_name: str, gestion_year: str, original_path: Path) -> pl.DataFrame:
        """
        Takes an iterator of dictionary records, converts them to a Polars DataFrame,
        standardizes column names, and appends mandatory columns.
        """
        try:
            # Convert to list to feed to Polars, or better, use schema if we know it.
            # For dynamic DBFs, feeding a list of dicts is straightforward.
            # If the DBF is large, we can process in batches, but Polars handles
            # in-memory lists efficiently up to millions of rows.
            data = list(records)
            if not data:
                log.warning(f"No records found to transform for {original_path}")
                return pl.DataFrame()

            df = pl.DataFrame(data, infer_schema_length=None)

            # Standardize column names (uppercase, strip)
            new_columns = {col: col.strip().upper() for col in df.columns}
            df = df.rename(new_columns)

            # Add mandatory columns
            current_timestamp = datetime.datetime.now().isoformat()
            
            df = df.with_columns([
                pl.lit(client_name).alias("Cliente"),
                pl.lit(gestion_year).alias("Gestion"),
                pl.lit(str(original_path)).alias("RutaOrigen"),
                pl.lit(current_timestamp).alias("FechaProceso")
            ])
            
            log.debug(f"Transformed {len(df)} rows and added required columns.")
            return df
            
        except Exception as e:
            log.error(f"Error transforming records for {original_path}: {str(e)}")
            raise e

import unittest
from pathlib import Path
from services.gestion_detector import GestionDetectorService
from services.polars_transformer import PolarsTransformerService
from models.config_model import AppConfig

class TestLogic(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig() # Uses default regex '\b(20[0-9]{2}|[0-9]{2})\b'
        self.detector = GestionDetectorService(self.config.regex_gestion)
        self.transformer = PolarsTransformerService()

    def test_gestion_detector(self):
        case_1 = "Estetikus.23 SIC JAC VER DENTRO"
        case_2 = "6. Izi sic jac 2024"
        case_3 = "Merakom. 2021 another word"
        
        # Test extraction and completion
        self.assertEqual(self.detector.extract_gestion(case_1), "2023")
        self.assertEqual(self.detector.extract_gestion(case_2), "2024")
        self.assertEqual(self.detector.extract_gestion(case_3), "2021")

    def test_polars_transformation(self):
        mock_records = [
            {" ID ": 1, " VALOR ": 100.50},
            {" ID ": 2, " VALOR ": 200.75}
        ]
        
        df = self.transformer.transform_records(
            iter(mock_records), 
            client_name="TestClient", 
            gestion_year="2023", 
            original_path=Path("/dummy/cn_pctas.dbf")
        )
        
        # Check standardizing
        self.assertIn("ID", df.columns)
        self.assertIn("VALOR", df.columns)
        self.assertNotIn(" ID ", df.columns)
        
        # Check injected columns
        self.assertIn("Cliente", df.columns)
        self.assertIn("Gestion", df.columns)
        self.assertIn("RutaOrigen", df.columns)
        self.assertIn("FechaProceso", df.columns)
        
        # Check data
        self.assertEqual(df["Cliente"][0], "TestClient")
        self.assertEqual(df["Gestion"][0], "2023")
        self.assertTrue(str(df["RutaOrigen"][0]).endswith("cn_pctas.dbf"))

if __name__ == '__main__':
    unittest.main()

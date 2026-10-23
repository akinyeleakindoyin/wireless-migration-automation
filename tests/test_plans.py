import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common import read_inventory

class Plans(unittest.TestCase):
    def test_demo_inventory(self):
        rows = read_inventory(ROOT / "examples/ap_inventory.example.csv", require_platform=True)
        self.assertEqual(len(rows), 3)

    def test_model_aware_mapping(self):
        path = ROOT / "image-predownload.py"
        spec = importlib.util.spec_from_file_location("image_predownload", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.get_image_prefix("AIR-AP2802I"), "ap3g3")
        self.assertEqual(module.get_image_prefix("AIR-AP1852I"), "ap1g4")
        self.assertEqual(module.get_image_prefix("C9130AXI"), "ap1g6a")
        self.assertIsNone(module.get_image_prefix("UNKNOWN"))

    def test_example_address_validation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.csv"
            path.write_text("name,ip,platform\nAP1,not-an-ip,C9130AXI\n")
            with self.assertRaises(ValueError):
                read_inventory(path)

if __name__ == "__main__":
    unittest.main()

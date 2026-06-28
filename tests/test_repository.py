import tempfile
import unittest
from pathlib import Path

from ship_mcp.data.repository import ShipTermRepository


class ShipTermRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "ship_terms.db"
        self.repo = ShipTermRepository(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_sqlite_bootstrap_creates_initial_data(self) -> None:
        categories = self.repo.list_categories()
        self.assertGreaterEqual(len(categories), 14)

        terms = self.repo.list_all_terms()
        self.assertGreater(len(terms), 300)

    def test_get_term_by_name_supports_korean(self) -> None:
        term = self.repo.get_term_by_name("용골")
        self.assertIsNotNone(term)
        self.assertEqual(term["id"], "keel")

    def test_search_includes_abbreviation(self) -> None:
        results = self.repo.search_terms("DWT", max_results=5)
        self.assertGreater(len(results), 0)

    def test_related_terms_resolve_to_full_rows(self) -> None:
        keel = self.repo.get_term("keel")
        self.assertIsNotNone(keel)

        related = self.repo.get_related_terms(keel)
        related_ids = {term["id"] for term in related}
        self.assertIn("hull", related_ids)


if __name__ == "__main__":
    unittest.main()

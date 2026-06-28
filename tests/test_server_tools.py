import os
import tempfile
import unittest
from pathlib import Path

from ship_mcp.data.repository import reset_repository
from ship_mcp import server


class ServerToolIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "ship_terms.db"
        self.previous_db_path = os.environ.get("SHIP_MCP_DB_PATH")
        os.environ["SHIP_MCP_DB_PATH"] = str(self.db_path)
        reset_repository()

    def tearDown(self) -> None:
        if self.previous_db_path is None:
            os.environ.pop("SHIP_MCP_DB_PATH", None)
        else:
            os.environ["SHIP_MCP_DB_PATH"] = self.previous_db_path
        reset_repository()
        self.temp_dir.cleanup()

    def test_search_ship_terms_works_with_sqlite_repository(self) -> None:
        results = server.search_ship_terms("용골", max_results=5)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["id"], "keel")

    def test_get_term_statistics_reads_counts_from_db(self) -> None:
        stats = server.get_term_statistics()
        self.assertGreater(stats["total_terms"], 300)
        self.assertGreaterEqual(stats["total_categories"], 14)


if __name__ == "__main__":
    unittest.main()

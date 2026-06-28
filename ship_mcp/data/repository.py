from __future__ import annotations

import os
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

DEFAULT_DB_FILENAME = "ship_terms.db"


def _default_db_path() -> Path:
    env_path = os.getenv("SHIP_MCP_DB_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent / DEFAULT_DB_FILENAME


def _normalize(value: str) -> str:
    return value.strip().lower()


def _normalize_korean_head(value: str) -> str:
    return value.split("(", 1)[0].strip().lower()


class ShipTermRepository:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else _default_db_path()
        self.template_db_path = Path(__file__).resolve().parent / DEFAULT_DB_FILENAME
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._prepare_database_file()
        self._initialize_database()

    def _prepare_database_file(self) -> None:
        if self.db_path.exists():
            return

        # Bootstrap custom DB paths from the packaged SQLite file.
        if self.template_db_path.exists() and self.db_path.resolve() != self.template_db_path.resolve():
            shutil.copy2(self.template_db_path, self.db_path)
            return

        raise FileNotFoundError(
            f"SQLite DB file not found at '{self.db_path}'. "
            "Ensure ship_mcp/data/ship_terms.db is present or provide --db-path to an existing DB file."
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize_database(self) -> None:
        with closing(self._connect()) as conn:
            table_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('categories', 'terms', 'term_synonyms', 'term_relations')"
            ).fetchone()[0]
            terms_count = conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0] if table_count == 4 else 0

        if table_count != 4 or terms_count == 0:
            raise RuntimeError(
                f"SQLite DB at '{self.db_path}' is missing required ship terminology data. "
                "Provide a populated DB file."
            )

    def _row_to_term(self, conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
        term_id = row["id"]
        synonyms = [
            synonym_row["synonym"]
            for synonym_row in conn.execute(
                "SELECT synonym FROM term_synonyms WHERE term_id = ? ORDER BY synonym",
                (term_id,),
            ).fetchall()
        ]
        related_ids = [
            related_row["related_term_id"]
            for related_row in conn.execute(
                "SELECT related_term_id FROM term_relations WHERE term_id = ? ORDER BY related_term_id",
                (term_id,),
            ).fetchall()
        ]

        return {
            "id": row["id"],
            "term_en": row["term_en"],
            "term_ko": row["term_ko"],
            "abbreviation": row["abbreviation"],
            "category": row["category_id"],
            "description_en": row["description_en"],
            "description_ko": row["description_ko"],
            "related_terms": related_ids,
            "synonyms": synonyms,
        }

    def list_categories(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT id, name_en, name_ko, description_en, description_ko, icon
                FROM categories
                ORDER BY name_en
                """
            ).fetchall()

        return [
            {
                "id": row["id"],
                "name_en": row["name_en"],
                "name_ko": row["name_ko"],
                "description_en": row["description_en"],
                "description_ko": row["description_ko"],
                "icon": row["icon"],
            }
            for row in rows
        ]

    def get_category(self, category_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as conn:
            row = conn.execute(
                """
                SELECT id, name_en, name_ko, description_en, description_ko, icon
                FROM categories
                WHERE id = ?
                """,
                (category_id,),
            ).fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "name_en": row["name_en"],
            "name_ko": row["name_ko"],
            "description_en": row["description_en"],
            "description_ko": row["description_ko"],
            "icon": row["icon"],
        }

    def list_all_terms(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT * FROM terms ORDER BY term_en").fetchall()
            return [self._row_to_term(conn, row) for row in rows]

    def count_terms(self) -> int:
        with closing(self._connect()) as conn:
            return int(conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0])

    def get_term(self, term_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM terms WHERE id = ?", (term_id,)).fetchone()
            if row is None:
                return None
            return self._row_to_term(conn, row)

    def get_term_by_name(self, name: str) -> dict[str, Any] | None:
        target = _normalize(name)

        with closing(self._connect()) as conn:
            row = conn.execute(
                """
                SELECT *
                FROM terms
                WHERE lower(term_en) = ?
                   OR lower(term_ko) = ?
                   OR lower(COALESCE(abbreviation, '')) = ?
                LIMIT 1
                """,
                (target, target, target),
            ).fetchone()

            if row is not None:
                return self._row_to_term(conn, row)

            synonym_row = conn.execute(
                """
                SELECT t.*
                FROM terms t
                JOIN term_synonyms s ON s.term_id = t.id
                WHERE lower(s.synonym) = ?
                LIMIT 1
                """,
                (target,),
            ).fetchone()
            if synonym_row is not None:
                return self._row_to_term(conn, synonym_row)

            # Preserve prior behavior for Korean names with parenthetical text.
            candidate_rows = conn.execute("SELECT * FROM terms").fetchall()
            for candidate in candidate_rows:
                if _normalize_korean_head(candidate["term_ko"]) == target:
                    return self._row_to_term(conn, candidate)

        return None

    def search_terms(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        q = _normalize(query)
        contains = f"%{q}%"
        prefix = f"{q}%"
        limit = max(1, max_results)

        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT
                    t.*,
                    MIN(
                        CASE
                            WHEN lower(t.term_en) = :exact THEN 0
                            WHEN lower(t.term_ko) = :exact THEN 0
                            WHEN lower(COALESCE(t.abbreviation, '')) = :exact THEN 0
                            WHEN lower(COALESCE(s.synonym, '')) = :exact THEN 1
                            WHEN lower(t.term_en) LIKE :prefix THEN 2
                            WHEN lower(t.term_ko) LIKE :prefix THEN 2
                            WHEN lower(COALESCE(t.abbreviation, '')) LIKE :prefix THEN 2
                            ELSE 3
                        END
                    ) AS match_rank
                FROM terms t
                LEFT JOIN term_synonyms s ON s.term_id = t.id
                WHERE lower(t.term_en) LIKE :contains
                   OR lower(t.term_ko) LIKE :contains
                   OR lower(COALESCE(t.abbreviation, '')) LIKE :contains
                   OR lower(t.description_en) LIKE :contains
                   OR lower(t.description_ko) LIKE :contains
                   OR lower(COALESCE(s.synonym, '')) LIKE :contains
                GROUP BY t.id
                ORDER BY match_rank ASC, t.term_en ASC
                LIMIT :limit
                """,
                {
                    "exact": q,
                    "prefix": prefix,
                    "contains": contains,
                    "limit": limit,
                },
            ).fetchall()

            return [self._row_to_term(conn, row) for row in rows]

    def get_terms_by_category(self, category_id: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM terms WHERE category_id = ? ORDER BY term_en",
                (category_id,),
            ).fetchall()
            return [self._row_to_term(conn, row) for row in rows]

    def get_related_terms(self, term: dict[str, Any]) -> list[dict[str, Any]]:
        term_id = term.get("id")
        if not term_id:
            return []

        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT t.*
                FROM term_relations r
                JOIN terms t ON t.id = r.related_term_id
                WHERE r.term_id = ?
                ORDER BY t.term_en
                """,
                (term_id,),
            ).fetchall()
            return [self._row_to_term(conn, row) for row in rows]


_DEFAULT_REPOSITORY: ShipTermRepository | None = None


def get_repository() -> ShipTermRepository:
    global _DEFAULT_REPOSITORY
    if _DEFAULT_REPOSITORY is None:
        _DEFAULT_REPOSITORY = ShipTermRepository()
    return _DEFAULT_REPOSITORY


def reset_repository() -> None:
    global _DEFAULT_REPOSITORY
    _DEFAULT_REPOSITORY = None


def list_categories() -> list[dict[str, Any]]:
    return get_repository().list_categories()


def get_category(category_id: str) -> dict[str, Any] | None:
    return get_repository().get_category(category_id)


def list_all_terms() -> list[dict[str, Any]]:
    return get_repository().list_all_terms()


def count_terms() -> int:
    return get_repository().count_terms()


def get_term(term_id: str) -> dict[str, Any] | None:
    return get_repository().get_term(term_id)


def get_term_by_name(name: str) -> dict[str, Any] | None:
    return get_repository().get_term_by_name(name)


def search_terms(query: str, max_results: int = 20) -> list[dict[str, Any]]:
    return get_repository().search_terms(query, max_results=max_results)


def get_terms_by_category(category_id: str) -> list[dict[str, Any]]:
    return get_repository().get_terms_by_category(category_id)


def get_related_terms(term: dict[str, Any]) -> list[dict[str, Any]]:
    return get_repository().get_related_terms(term)

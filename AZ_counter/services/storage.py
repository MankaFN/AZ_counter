import sqlite3
import json

class Storage:
    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(""" 
                        CREATE TABLE IF NOT EXISTS settings (
                            key TEXT PRIMARY KEY,
                            value TEXT
                        )
                    """)

            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS marks_data (
                        subject TEXT PRIMARY KEY,
                        marks_json TEXT,
                        skips TEXT
                        )
                    """)

            self._migrate_marks_data(cursor)
            conn.commit()

    def _table_exists(self, cursor, table_name: str) -> bool:
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        )
        return cursor.fetchone() is not None

    def _quote_identifier(self, name: str) -> str:
        return '"' + name.replace('"', '""') + '"'

    def _table_columns(self, cursor, table_name: str) -> set[str]:
        cursor.execute(f"PRAGMA table_info({self._quote_identifier(table_name)})")
        return {row[1] for row in cursor.fetchall()}

    def _migrate_marks_data(self, cursor):
        cursor.execute("SELECT COUNT(*) FROM marks_data")
        if cursor.fetchone()[0] > 0:
            return

        for table_name in ("marks", "marks_data.txt"):
            if not self._table_exists(cursor, table_name):
                continue

            columns = self._table_columns(cursor, table_name)
            marks_column = None
            for candidate in ("marks", "marks_data.txt", "marks_json"):
                if candidate in columns:
                    marks_column = candidate
                    break

            if {"subject", "skips"}.issubset(columns) and marks_column:
                cursor.execute(f"""
                    INSERT OR REPLACE INTO marks_data (subject, marks_json, skips)
                    SELECT subject, {self._quote_identifier(marks_column)}, skips
                    FROM {self._quote_identifier(table_name)}
                """)
                cursor.execute("SELECT COUNT(*) FROM marks_data")
                if cursor.fetchone()[0] > 0:
                    break

    def _get_settings(self, key: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT value FROM settings WHERE key = ?""",
                (key,))

            value = cursor.fetchone()[0]
        return value or ""

    def _set_settings(self, key: str, value: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO settings VALUES (?, ?)""",
                (key, value))
            conn.commit()

    def get_login(self) -> str:
        return self._get_settings("login")
    def get_password(self) -> str:
        return self._get_settings("password")
    def get_trim(self) -> str:
        return self._get_settings("trim")

    def save_user(self, login: str, password: str):
        self._set_settings("login", login)
        self._set_settings("password", password)
    def set_trim(self, trim: int):
        self._set_settings("trim", str(trim))

    def has_data(self) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM marks_data")
            count = cursor.fetchone()[0]
        return count > 0

    def save_marks(self, marks: dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM marks_data")

            for subject, data in marks.items():
                mark = json.dumps(data[0])
                skips = data[1]
                cursor.execute(
                    "INSERT INTO marks_data VALUES (?, ?, ?)",
                    (subject, mark, skips)
                )

            conn.commit()

    def marks_give(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM marks_data")
            rows = cursor.fetchall()

            marks = {}

            for subject, mark, skips in rows:
                marks[subject] = [json.loads(mark), skips]

        return marks

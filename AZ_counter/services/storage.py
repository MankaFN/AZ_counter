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
                    CREATE TABLE IF NOT EXISTS marks (
                        subject TEXT PRIMARY KEY,
                        marks TEXT,
                        skips TEXT
                        )
                    """)

            conn.commit()

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
    def get_window_size(self) -> str:
        return self._get_settings("window_size")

    def save_user(self, login: str, password: str):
        self._set_settings("login", login)
        self._set_settings("password", password)
    def set_trim(self, trim: int):
        self._set_settings("trim", str(trim))
    def set_window_size(self, window_size: int):
        self._set_settings("window_size", str(window_size))

    def has_data(self) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM marks")
            count = cursor.fetchone()[0]
        return count > 0

    def save_marks(self, marks: dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM marks")

            for subject, data in marks.items():
                mark = json.dumps(data[0])
                skips = data[1]
                cursor.execute(
                    "INSERT INTO marks VALUES (?, ?, ?)",
                    (subject, mark, skips)
                )

            conn.commit()

    def marks_give(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM marks")
            rows = cursor.fetchall()

            marks = {}

            for subject, mark, skips in rows:
                marks[subject] = [json.loads(mark), skips]

        return marks
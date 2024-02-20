import sqlite3
import os


class Database:

    DB_LOCATION = None

    @classmethod
    def init(cls, db_dir_path: str) -> None:
        Database.DB_LOCATION = os.path.join(db_dir_path, 'database.db')

    def __init__(self) -> None:
        if Database.DB_LOCATION is None:
            raise Exception('Database Location not initialized')

        self.connection = sqlite3.connect(Database.DB_LOCATION)
        self.connection.execute('PRAGMA foreign_keys = ON')
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.commit()
        self.cursor.close()
        self.connection.close()

    def execute(self, sql: str, vars: tuple[str] = (), fetchone: bool = False, fetchmany: int = 0):
        self.cursor.execute(sql, vars)
        return self.fetch(fetchone, fetchmany)

    def commit(self):
        self.connection.commit()

    def fetch(self, fetchone: bool = False, fetchmany: int = 0):
        if fetchone:
            return self.cursor.fetchone()
        if fetchmany > 0:
            return self.cursor.fetchmany()
        return self.cursor.fetchall()

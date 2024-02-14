import sqlite3
import os
import bcrypt
import time


class User:

    DB = None
    MAX_INACTIVITY = 1800

    @classmethod
    def init(cls, tmp_path: str) -> None:
        User.DB = os.path.join(tmp_path, 'database.db')
        conn = sqlite3.connect(User.DB)

        cur = conn.cursor()

        cur.execute(
            '''CREATE TABLE IF NOT EXISTS users
            (id TEXT PRIMARY KEY, hashed_password TEXT, last_active REAL)'''
        )

        cur.close()
        conn.close()

    def __init__(self, id: str) -> None:
        self.id = id

    def is_online(self) -> bool:
        conn = sqlite3.connect(User.DB)
        cur = conn.cursor()

        last_active = cur.execute(
            '''SELECT last_active FROM users WHERE id = ?''',
            (self.id,)
        ).fetchone()

        if last_active is None or time.time() - last_active[0] > User.MAX_INACTIVITY:
            cur.close()
            conn.close()
            return False

        cur.execute(
            '''UPDATE users SET last_active = ? WHERE id = ?''',
            (time.time(), self.id)
        )
        conn.commit()

        cur.close()
        conn.close()
        return True

    def register(self, password: str) -> None:
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())

        conn = sqlite3.connect(User.DB)
        cur = conn.cursor()

        cur.execute(
            '''INSERT INTO users (id, hashed_password, last_active) VALUES (?, ?, ?)''',
            (self.id, hashed_password, 0.0)
        )
        conn.commit()

        cur.close()
        conn.close()

    def login(self, password: str) -> bool:

        conn = sqlite3.connect(User.DB)
        cur = conn.cursor()

        hashed_password = cur.execute(
            '''SELECT hashed_password FROM users WHERE id = ?''',
            (self.id, )
        ).fetchone()

        if hashed_password is not None and bcrypt.checkpw(password.encode('utf-8'), hashed_password[0]):
            cur.execute(
                '''UPDATE users SET last_active = ? WHERE id = ?''',
                (time.time(), self.id)
            )
            conn.commit()

            cur.close()
            conn.close()
            return True

        cur.close()
        conn.close()
        return False

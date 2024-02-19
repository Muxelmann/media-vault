import os
import bcrypt
import time

from ..database import Database


class User:

    LOGGED_IN_USERS = {}
    MAX_INACTIVITY = 1800

    @classmethod
    def init(cls) -> None:
        db = Database()
        db.execute(
            '''CREATE TABLE IF NOT EXISTS users
            (id TEXT PRIMARY KEY, hashed_password TEXT, last_active REAL)'''
        )

    @classmethod
    def at_least_one_exists(cls) -> None:
        db = Database()
        a_user = db.execute(
            '''SELECT id FROM users''',
            fetchone=True
        )

        return a_user is not None

    def __init__(self, id: str) -> None:
        self.id = id
        self.db = Database()

    def is_online(self) -> bool:
        # Get the current time
        current_time = time.time()

        # If user's last activity is not logged, get it from DB
        if self.id not in User.LOGGED_IN_USERS.keys():
            last_active = self.db.execute(
                '''SELECT last_active FROM users WHERE id = ?''',
                (self.id,),
                fetchone=True
            )

            if last_active is None:
                return False

            if current_time - last_active[0] > User.MAX_INACTIVITY:
                return False

            # If user has recently been active, cache activity time and update DB
            User.LOGGED_IN_USERS[self.id] = [current_time, current_time]
            self.db.execute(
                '''UPDATE users SET last_active = ? WHERE id = ?''',
                (User.LOGGED_IN_USERS[self.id][1], self.id)
            )
            return True

        # If user's last activity is logged, check if user has recently been active
        if current_time - User.LOGGED_IN_USERS[self.id][0] < User.MAX_INACTIVITY:

            # Update cached activity
            User.LOGGED_IN_USERS[self.id][0] = current_time

            # If DB laggs behind too far, update it
            if current_time - User.LOGGED_IN_USERS[self.id][1] > User.MAX_INACTIVITY:
                self.db.execute(
                    '''UPDATE users SET last_active = ? WHERE id = ?''',
                    (User.LOGGED_IN_USERS[self.id][1], self.id)
                )

            return True

        # Delete user from cache is inactive for too long
        del User.LOGGED_IN_USERS[self.id]
        return False

    def register(self, password: str) -> None:
        # Generate hashed password
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())

        # Save user
        self.db.execute(
            '''INSERT INTO users (id, hashed_password, last_active) VALUES (?, ?, ?)''',
            (self.id, hashed_password, time.time())
        )

    def login(self, password: str) -> bool:
        # Obtain hashed password
        hashed_password = self.db.execute(
            '''SELECT hashed_password FROM users WHERE id = ?''',
            (self.id, ),
            fetchone=True
        )

        # If no password found, return
        if hashed_password is None:
            return False

        # Check if password is correct
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password[0]):
            # Update user's activity
            current_time = time.time()
            User.LOGGED_IN_USERS[self.id] = [current_time, current_time]
            self.db.execute(
                '''UPDATE users SET last_active = ? WHERE id = ?''',
                (current_time, self.id)
            )
            return True

        return False

    def logout(self) -> None:
        # If activity is logged, delete its entry
        if self.id in User.LOGGED_IN_USERS.keys():
            del User.LOGGED_IN_USERS[self.id]

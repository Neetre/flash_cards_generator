import os
import sqlite3
from dotenv import load_dotenv
load_dotenv()
KEY = os.getenv("SECRET_KEY")


class SQLiteDBManager:
    def __init__(self, db_name="../../data/user_registration.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(e)
            raise

    def create_user_table(self):
        """Create a table for user registration."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def insert_user(self, username, email, password):
        """Insert a new user into the users table."""
        self.cursor.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        ''', (username, email, password))
        self.conn.commit()

    def fetch_all_users(self):
        """Fetch all users from the users table."""
        self.cursor.execute('SELECT * FROM users')
        return self.cursor.fetchall()
    
    def fetch_user(self, username: str) -> tuple:
        self.cursor.execute(f"SELECT * FROM users WHERE username= ?", (username,))
        return self.cursor.fetchone()
    
    def remove_user(self, username: str):   
        self.cursor.execute("DELETE FROM users WHERE username= ?", (username,))
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    db_manager = SQLiteDBManager()
    db_manager.connect()
    db_manager.create_user_table()

    users = db_manager.fetch_all_users()
    for user in users:
        print(user)

    # db_manager.remove_user("test_user")
    # db_manager.insert_user("test_user", "pippo@gmail.com", "T@stP@ssw0rd")

    # enc_pwd = Security.encrypt_password("T@stP@ssw0rd", KEY).decode("utf-8")
    # db_manager.insert_user("test_user", "test@gmail.com", enc_pwd)

    db_manager.close()

import sqlite3

class DataBase:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(database='database.db', timeout=10, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._execute_initial_querys()
    
    def _execute_initial_querys(self) -> None:
        querys = [
            'CREATE TABLE IF NOT EXISTS clientes (user_id INTEGER NOT NULL, chat_id INTEGER, username TEXT, name TEXT, chats TEXT, access_checked_in_chats TEXT, plan TEXT)',
            'CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER NOT NULL, title TEXT, type TEXT )',
            'CREATE TABLE IF NOT EXISTS cache_de_perfis (user_id INTEGER NOT NULL, chat_id INTEGER, username TEXT, name TEXT)',
        ]
        for sql in querys:
            self.cursor.execute(sql)
        self.conn.commit()

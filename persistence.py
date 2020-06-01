import sqlite3

class Model:
    def __init__(self, filename:str):
        self.__file = filename
    def initiate(self):
        conn = sqlite3.connect(self.__file)
        c = conn.cursor()
        try:
            c.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
            if c.fetchone()[0]==0:
                #Migrations
                c.execute("""
                CREATE TABLE chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT(100) UNIQUE,
                    username TEXT(100) UNIQUE
                );
                """)
        finally:
            c.close()
            conn.close()

    def add_chat(self, chat_id, username):
        conn = sqlite3.connect(self.__file)
        c = conn.cursor()
        try:
            try:
                c.execute("INSERT INTO chats(chat_id, username) values (?, ?)", (chat_id, username))
                conn.commit()
            except sqlite3.IntegrityError as e:
                c.execute("SELECT count(*) from chats where username=?", (username, ))
                if c.fetchone()[0]==1:
                    c.execute("UPDATE chats set chat_id = ? where username=?", (chat_id, username))
                    conn.commit()
                else:
                    raise e
        finally:
            c.close()
            conn.close()

    def get_chat(self, username:str):
        conn = sqlite3.connect(self.__file)
        c = conn.cursor()
        try:
            c.execute("SELECT chat_id from chats where username=?", ( username,))
            res = c.fetchone()
            if res:
               return res[0]
        finally:
            c.close()
            conn.close()

    def get_chat_by_chat_id(self, chat_id:str):
        conn = sqlite3.connect(self.__file)
        c = conn.cursor()
        try:
            c.execute("SELECT chat_id from chats where chat_id=?", (chat_id,))
            res = c.fetchone()
            if res:
                return res[0]
        finally:
            c.close()
            conn.close()

    def delete_chat(self, username):
        conn = sqlite3.connect(self.__file)
        c = conn.cursor()
        try:
            c.execute("delete from chats where username=?", (username,))
            conn.commit()
        finally:
            c.close()
            conn.close()


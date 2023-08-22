from datetime import datetime, timedelta
import sqlite3
import models
import json


class DataBase:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(database='database.db', timeout=10, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._execute_initial_querys()
    
    def _execute_initial_querys(self) -> None:
        querys = [
            'CREATE TABLE IF NOT EXISTS clientes (user_id INTEGER NOT NULL, chat_id INTEGER, username TEXT, name TEXT, chats TEXT, access_checked_in_chats TEXT, plan_maturity TEXT)',
            'CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER NOT NULL, title TEXT, type TEXT )',
            'CREATE TABLE IF NOT EXISTS cache_de_perfis (user_id INTEGER NOT NULL, chat_id INTEGER, username TEXT, name TEXT)',
            'CREATE TABLE IF NOT EXISTS clientes_esperando_fatura (user_id INTEGER NOT NULL, invoice_message_id INTEGER, username TEXT, name TEXT)',

        ]
        for sql in querys:
            self.cursor.execute(sql)
        self.conn.commit()
    
    # adicionar um grupo ou canal no banco
    
    def insert_chat(self, chat:models.Chat):
        sql = "INSERT INTO chats (chat_id, title, type) VALUES (?,?,?)"
        self.cursor.execute(sql,(chat.chat_id ,chat.title, chat.type_,))
        return self.conn.commit()
    
    # remover um grupo ou canal no banco
    
    def delete_chat(self, chat:models.Chat):
        sql = "DELETE FROM chats WHERE chat_id = ?"
        self.cursor.execute(sql,(chat.chat_id,))
        return self.conn.commit()
    
    # obter todos os grupos e canais no banco

    def get_all_chats(self) -> [list]:
        sql = "SELECT * FROM chats"
        return self.cursor.execute(sql).fetchall()
    
    # adicionar o perfil de um usuario no cache

    def insert_user_cache(self, user:models.User):
        sql = "INSERT INTO cache_de_perfis (chat_id, user_id, name, username) VALUES (?,?,?,?)"
        self.cursor.execute(sql, (user.chat_id, user.user_id, user.name , user.username))
        return self.conn.commit()
    
    # pegar um usuario no cache

    def get_user_cache(self, identify:str) -> list|None:
        identify = str(identify)
        sql = "SELECT * FROM cache_de_perfis WHERE chat_id = ?" if identify.isnumeric() else "SELECT * FROM cache_de_perfis WHERE username = ?"
        user = self.cursor.execute(sql, (identify,)).fetchone()
        return user
    
    # adicionar ou atualizar um cliente no banco

    def insert_client(self, user:models.User, chat:models.Chat)  -> str:
        client = self.conn.execute("SELECT * FROM clientes WHERE user_id = ?", (user.user_id,)).fetchone()
        if client:
            sql = " UPDATE clientes SET chats = ? WHERE user_id = ?"
            data = json.loads(client[4])
            data["chats"].append(chat.chat_id)
            data["chats"] = list(set(data["chats"]))
            self.cursor.execute(sql, (json.dumps(data), user.user_id,))
            self.conn.commit()
            return client[6]

        sql = "INSERT INTO clientes (user_id,chat_id, username, name, chats, access_checked_in_chats, plan_maturity) VALUES (?,?,?,?,?,?,?)"
        plan_maturity = datetime.now()   + timedelta(days=30)
        plan_maturity = plan_maturity.strftime("%d/%m/%Y")
        data = json.dumps({
            "chats":[chat.chat_id]
        })
        access_checked_in_chats = json.dumps({"chats":[]})
        self.cursor.execute(
            sql, (user.user_id, user.chat_id, user.username,user.name, data, access_checked_in_chats, plan_maturity,)
        )
        self.conn.commit()
        return plan_maturity
    
    # adicionar ou remover dias no plano de um cliente

    def update_client_plan(self, days:str, profile_identifier:str, operation:str)-> bool|tuple:
        sql = "SELECT * FROM clientes WHERE username = ? or user_id = ?" 
        user = self.cursor.execute(sql, (profile_identifier, profile_identifier, )).fetchone()
        if not user:
            return False
        plan_maturity = datetime.strptime(user[6], '%d/%m/%Y').date()
        new_plan_maturity =  plan_maturity + timedelta(days=int(days)) if operation == "+" else plan_maturity - timedelta(days=(int(days)))
        new_plan_maturity = new_plan_maturity.strftime("%d/%m/%Y")
        sql = " UPDATE clientes SET plan_maturity = ? WHERE username = ? or user_id = ?"
        self.cursor.execute(sql, (new_plan_maturity,profile_identifier, profile_identifier))
        self.conn.commit()
        user_identified = user[3] if not user[2] else f"@{user[2]}"
        return new_plan_maturity, user_identified
    
    # atualizar chats que foi verificado se o cliente entrou
    
    def update_client_chats_checked(self,client:models.Client):
        sql = "UPDATE clientes SET access_checked_in_chats = ? WHERE user_id = ?"
        self.cursor.execute(sql, (json.dumps(client.access_checked_in_chats), client.user_id,))        
        return self.conn.commit()
    
    # pegar todos os clientes no banco
    
    def get_all_clients(self) -> list:
        sql = "SELECT * FROM clientes"
        return self.cursor.execute(sql).fetchall()
    
    # remover um cliente do banco
    
    def delete_client(self, client:models.Client):
        sql = "DELETE FROM clientes WHERE user_id = ?"
        self.cursor.execute(sql,(client.user_id,))
        return self.conn.commit()
    
    # adicionar um cliente na tabela de clientes que tem pendencias abertas

    def insert_client_awaiting_invoice(self, client:models.Client):
        sql = "INSERT INTO clientes_esperando_fatura (user_id,invoice_message_id, username, name) VALUES (?,?,?,?)"
        self.cursor.execute(sql, (client.user_id, None, client.username, client.name,))
        return self.conn.commit()
    
    # atualizar o id da mensagem de fatura

    def update_invoice_message_id(self,user_id:int, message_id:int):
        sql = "UPDATE clientes_esperando_fatura SET invoice_message_id = ? WHERE user_id = ?"
        self.cursor.execute(sql, (message_id, user_id,))        
        return self.conn.commit()
    
    # obter um cliente que tem fatura aberta

    def get_client_awaiting_invoice(self, user_id:int ) -> list|None:
        sql = "SELECT * FROM clientes_esperando_fatura WHERE user_id = ?"
        return self.cursor.execute(sql, (user_id, )).fetchone()
    
    # apagar a fatura de um cliente
    
    def delete_client_awaiting_invoice(self, client:models.Client|str):
        user_id = client.user_id if isinstance(client, models.Client) else client
        sql = "DELETE FROM clientes_esperando_fatura WHERE user_id = ?"
        self.cursor.execute(sql,(user_id,))
        return self.conn.commit()
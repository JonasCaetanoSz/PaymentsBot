from pydantic import BaseModel
from typing import Optional

class Client(BaseModel):
    user_id:int
    chat_id:int
    username:Optional[str]
    name:str
    chats:dict
    access_checked_in_chats:dict
    plan_maturity:str
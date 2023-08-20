from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    user_id:int
    chat_id:int
    username:Optional[str]
    name:str
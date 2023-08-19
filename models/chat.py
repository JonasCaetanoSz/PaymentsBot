from pydantic import BaseModel

class Chat(BaseModel):
    chat_id:int
    title:str
    type_:str
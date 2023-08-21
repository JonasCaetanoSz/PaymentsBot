from models import Client, Chat
from datetime import datetime
from database import DataBase
import telebot
import json
import time

def checking(bot:telebot.TeleBot, db_connection:DataBase, admin_chat_id:int) -> None:
    main_message_id = bot.send_message(
        chat_id=admin_chat_id,
        text="*iniciando checagem diaria de membros ⏳*",
        parse_mode="markdown"
    ).id
    clientes = [
        Client(
        user_id=client[0],
        chat_id=client[1],
        username=client[2],
        name=client[3],
        chats=json.loads(client[4]),
        access_checked_in_chats=json.loads(client[5]),
        plan_maturity=client[6]

        ) for client in db_connection.get_all_clients()
    ]
    channels_and_groups = {}
    for chat in db_connection.get_all_chats():
        channels_and_groups.update({
        chat[0]:Chat(
        chat_id=chat[0],
        title=chat[1],
        type_=chat[2]
    )})
    
    # checar se o cliente entrou no grupo ou canal a qual o link foi gerado

    for cliente in clientes:

        chats_where_not__enter = ""
        for chat in cliente.chats["chats"]:
            if not chat in cliente.access_checked_in_chats["chats"]:
                try:
                    member = bot.get_chat_member(chat_id=chat, user_id=cliente.user_id)
                    if not member:
                        raise Exception("usuario não é um membro")
                except:
                    group_or_channel = channels_and_groups[chat]
                    chats_where_not__enter += f"\n{group_or_channel.title} ({group_or_channel.type_})"
                cliente.access_checked_in_chats["chats"].append(chat)
                db_connection.update_client_chats_checked(cliente)

        if chats_where_not__enter:
            identify = f"@{cliente.username}" if cliente.username else cliente.name
            bot.send_message(
                chat_id=admin_chat_id,
                text=f"{identify} não entrou nos grupos e canais abaixo:\n" + chats_where_not__enter + "\n\né provavel que ele(a) tenha compartilhado o link de acesso com outra pessoa."
            )
    
    # checar o plano de um cliente

    for cliente in clientes:
        plan_maturity = datetime.strptime(cliente.plan_maturity, '%d/%m/%Y').date()
        today = datetime.now().date()
        days_remaining = (plan_maturity - today).days
        identifier = f"@{cliente.username}" if cliente.username else cliente.name
        success_removed_message = ""
        next_due_date_message = ""
        fail_removed_message = ""
        next_due_date_count = 0
        fail_count = 0
        count = 0

        # plano do cliente expira hoje

        if days_remaining <= 0:
            for chat in cliente.chats["chats"]:
                try:
                    chat:Chat = channels_and_groups[chat]
                    member = bot.get_chat_member(chat_id=chat.chat_id , user_id=cliente.user_id)
                    bot.ban_chat_member(chat_id=chat.chat_id, user_id=cliente.user_id, until_date=time.time() + 30) # remove o cliente da lista de usuarios banidos do canal
                    if chat.type_ == "canal": bot.unban_chat_member(chat_id=chat.chat_id, user_id=cliente.user_id)
                    count += 1
                    success_removed_message += f"\n\n{count} - {chat.title} ({chat.type_})"
                except:
                    fail_count += 1
                    fail_removed_message += f"\n\n{fail_count} - {chat.title} ({chat.title})"
        
        # plano do cliente expira em 3 dias
    
        elif days_remaining == 3:
            for chat in cliente.chats["chats"]:
                chat:Chat = channels_and_groups[chat]
                next_due_date_count += 1
                next_due_date_message += f"\n\n{next_due_date_count} - {chat.title} ({chat.type_})"
        
        # enviar as mensagens para o administrador

        if success_removed_message:
            db_connection.delete_client(client=cliente)
            bot.send_message(
                chat_id=admin_chat_id,
                text=f"o plano de {identifier} vence hoje e foi removido dos seguintes grupos e canais:" + success_removed_message
        )
            
        if fail_removed_message:
            db_connection.delete_client(client=cliente)
            bot.send_message(
                chat_id=admin_chat_id,
                text=f"o plano de {identifier} vence hoje mas não consegui remove-lo dos seguintes grupos e canais:" + fail_removed_message
        )
        
        if next_due_date_message:
            bot.send_message(
                chat_id=admin_chat_id,
                text=f"o plano de {identifier} vence em 3 dias e será removido dos seguintes grupos e canais:" + next_due_date_message
        )
    
    bot.delete_message(
        chat_id=admin_chat_id,
        message_id=main_message_id
    )


# checar todos os dias ás 00:00 noite

def daily_task(bot:telebot.TeleBot, db_connection:DataBase, admin_chat_id:int) -> None:
    while True:
        now = datetime.now()
        if now.hour == 22:#and now.minute == 0:
            checking(bot=bot, db_connection=db_connection, admin_chat_id=admin_chat_id)
            time.sleep(60) # pra evitar checar mais de uma vez
        time.sleep(30) # aguarde 30 segundos antes de verificar a hora de novo
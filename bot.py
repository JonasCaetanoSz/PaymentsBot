from database import DataBase
import configparser
import telethon
import telebot
import asyncio
import models
import time
import re

class Bot:
    def __init__(self,ignore_chat_events,telethon_session_name,administrator_chat_id,bot_token, telethon_api_hash, telethon_api_id) -> None:
        self.ignore_chat_events = True if ignore_chat_events == "true" else False
        self.telethon_session_name = telethon_session_name
        self.administrator_chat_id = int(administrator_chat_id)
        self.telethon_api_hash = telethon_api_hash
        self.telethon_api_id = telethon_api_id
        self.database_connection = DataBase()
        self.token = bot_token
        self.bot = telebot.TeleBot(token=self.token)
    
    # verificar se a mensagem foi enviada pelo chat do administrador

    def check_is_administrador_message(self, message:telebot.types.Message) -> bool:
        return self.administrator_chat_id == message.chat.id
    
    # obter dados de um perfil via cache, telebot ou telethon

    async def get_user_profile(self, profile_identifier:str) -> models.User:
        
        user:list = self.database_connection.get_user_cache(identify=profile_identifier)
        if user:
            return models.User(
                user_id=user[0],
                chat_id=user[1],
                username=user[2],
                name=user[3]

            )
        try:
            chat:telebot.types.Chat = self.bot.get_chat(profile_identifier.isidentifier)
        except:
            chat = None
        if chat:
            user = models.User(
                user_id=chat.id,
                chat_id=chat.id,
                username=chat.username,
                name=chat.first_name

            )
            self.database_connection.insert_user_cache(user)
            return user
        
        client = telethon.TelegramClient(
            session=self.telethon_session_name,
            api_hash=self.telethon_api_hash,
            api_id=self.telethon_api_id
        )
        await client.start()
        chat = await client.get_entity(profile_identifier)
        await client.disconnect()
        user = models.User(
            chat_id=chat.id,
            user_id=chat.id,
            username=chat.username,
            name= chat.title if isinstance(chat, telethon.types.Channel) else chat.first_name 
        )
        self.database_connection.insert_user_cache(user)
        return user
    
    def run(self):

        # mensagem de boas-vindas

        @self.bot.message_handler(commands=['start'], func=self.check_is_administrador_message)
        def start_command(message:telebot.types.Message):
            identifier = message.from_user.username if message.from_user.username else message.from_user.first_name
            self.bot.send_message(
                reply_to_message_id=message.id,
                chat_id=message.chat.id,
                text=f'olá *{identifier}*, eu sou um bot que vai te ajudar a gerenciar membros em seus grupos e canais. você é meu administrador, todos os meus comando disponiveis responderão apenas as suas mensagens. leia minha documentação para saber mais!',
                parse_mode='markdown'
            )
        
        # listar todos grupos e canais que o bot é administrador

        @self.bot.message_handler(commands=["chats"], func=self.check_is_administrador_message)
        def chats_command(message:telebot.types.Message):
            chats = [models.Chat(
                chat_id=chat[0],
                title=chat[1],
                type_=chat[2]
            ) for chat in self.database_connection.get_all_chats()]
            if not chats:
                return self.bot.send_message(
                    chat_id=message.chat.id,
                    reply_to_message_id=message.id,
                    text="eu ainda não fui adicionado com administrador em nenhum grupo ou canal. portanto é impossivel enviar uma lista."
            )
        
            markup = telebot.types.InlineKeyboardMarkup()
            chat_index_count = 0
            for chat in chats:
                chat_index_count += 1
                markup.add(telebot.types.InlineKeyboardButton(
                    text=f"{chat_index_count} - {chat.title} ({chat.type_})",
                    callback_data=f"quit:{chat.chat_id}"
            ))
            self.bot.send_message(
                chat_id=message.chat.id,
                text="eu sou administrador dos seguintes grupo e canais :",
                reply_to_message_id=message.id,
                reply_markup=markup
            )
        

        # administrador quer definir se o bot deve ou não processar evento quando é adicionado em um novo grupo ou canal
        
        @self.bot.message_handler(commands=['block_events'], func=self.check_is_administrador_message)
        def block_event_command(message:telebot.types.Message):
            new_state = not self.ignore_chat_events
            parser = configparser.ConfigParser()
            parser.read('preferences.ini')
            parser.set('preferences', 'ignore_chat_events', str(new_state).lower())
            preferences_file = open(file="preferences.ini", mode="w")
            parser.write(preferences_file)
            preferences_file.close()
            self.ignore_chat_events = new_state
            self.bot.send_message(
                reply_to_message_id=message.id,
                chat_id=message.chat.id,
                text= 'o modo bloqueio de eventos foi *ativado*, a partir de agora, o bot não irá processar os grupos e canais que for adicionado como administrador.' if new_state else 'o modo bloqueio de eventos foi *desativado*, a partir de agora, o bot irá processar todos os grupos e canais que for adicionado como administrador.' ,
                parse_mode='markdown'
            )
        
        # gerar link de convite

        @self.bot.message_handler(commands=["invite"], func=self.check_is_administrador_message)
        def generate_invite_link(message:telebot.types.Message):
            user_id =  re.findall(r"id:\s*(\d+)", message.text)
            username = re.findall(r"username:(\S+)",message.text)
            profile_identifier = user_id[0] if user_id else username[0] if username else False
            if not profile_identifier:
                return self.bot.send_message(
                    chat_id=message.chat.id,
                    reply_to_message_id=message.id,
                    text="é preciso informar o nome de usuario ou o id de um perfil do telegram para gerar link de convite.\n\nvocê também pode usar o numero de telefone ou link do perfil para identificar um usuario."
            )
            channels_and_groups = [models.Chat(
                chat_id=chat[0],
                title=chat[1],
                type_=chat[2]
            ) for chat in self.database_connection.get_all_chats()]
            if not channels_and_groups:
                return self.bot.send_message(
                    chat_id=message.chat.id,
                    reply_to_message_id=message.id,
                    text="o bot ainda não é administrador de nenhum grupo ou canal, impossivel gerar link de convite."
            )

            
            user_permissions = [i for i in range(1, len(channels_and_groups) + 1)] if "*" in message.text.lower() else \
                   re.findall(r'\d+', message.text.replace(f"id:{profile_identifier}", "")) if user_id else \
                   re.findall(r'\d+', message.text.replace(f"username:{profile_identifier}", ""))
            user_permissions = [int(n) for n in user_permissions] # passar pra int porque o findall vai retornar uma lista de string
        
            if not user_permissions or any(n > len(channels_and_groups) for n in user_permissions):
                return  self.bot.send_message(
                    chat_id=message.chat.id,
                    reply_to_message_id=message.id,
                    text="desculpe, não posso gerar os links de convite, verifique a sequencia de chats que o usuario poderá ter acesso.\n\ndigite a qualquer momento /chats para ver a lista completa ou use /invite * para gerar link de convite á todos os chats."
            )
            try:
                user = asyncio.run(self.get_user_profile(profile_identifier))
            except:
                user = None
            
            if not user:
                return self.bot.send_message(
                    chat_id=message.chat.id,
                    reply_to_message_id=message.id,
                    text="desculpe mas não estou conseguindo encontrar este usuario, imposivel gerar link de convite."
            )
            main_message_id = self.bot.send_message(
                chat_id=message.chat.id,
                reply_to_message_id=message.id,
                text="gerando links de convites ⏳"
            ).id
            

            invite_links = ""
            erros = ""
            for index,chat in enumerate(channels_and_groups, start=1):
                if not index in user_permissions:
                    continue
                try:
                    invite_link = self.bot.create_chat_invite_link(chat_id=chat.chat_id, member_limit=1, expire_date=int(time.time()+86400)).invite_link
                    self.database_connection.insert_client(user, chat)
                    invite_links += f"\n\n{chat.title}:\n\n{invite_link}"
                except Exception as e:
                    erros += f"\n\n{chat.title}:\n\n{str(e)}"
            
            if invite_links:
                self.bot.edit_message_text(
                    chat_id=message.chat.id,
                    text=invite_links,
                    message_id=main_message_id
            )
            
            if erros:
                self.bot.send_message(
                    chat_id=message.chat.id,
                    text="erros que ocorreram ao gerar convites:" + erros,
                    reply_to_message_id=message.id
            )

        # alterações no estado do bot em um grupo ou canal

        @self.bot.my_chat_member_handler()
        def my_chat_member(message: telebot.types.ChatMemberUpdated):
            
            # bot adicionado em um grupo o canal

            if message.new_chat_member.status == "administrator" and message.chat.type in ["channel", "group"] and not self.ignore_chat_events:
                chat_type = "grupo" if message.chat.type == "group" else "canal"
                chat = models.Chat(
                    chat_id=message.chat.id,
                    title=message.chat.title,
                    type_=chat_type
            )
                self.database_connection.insert_chat(chat)
                markup = telebot.types.InlineKeyboardMarkup()
                button = telebot.types.InlineKeyboardButton(text=f"sair do {chat_type}🔧", callback_data=f"quit:{message.chat.id}")
                markup.add(button)
                self.bot.send_message(
                chat_id=self.administrator_chat_id,
                text=f"este bot foi colocado como administrador:\n\n<b>nome do {chat_type}:</b> {message.chat.title}\n\n<b>id do {chat_type}:</b> <code> {message.chat.id}</code>",
                parse_mode="html",
                reply_markup=markup
            )

            # bot removido de um grupo ou canal

            elif message.new_chat_member.status in ["kicked", "left"] and message.chat.type in ["channel", "group"]:
                chat_type = "grupo" if message.chat.type == "group" else "canal"
                chat = models.Chat(
                    chat_id=message.chat.id,
                    title=message.chat.title,
                    type_=chat_type
            )
                self.database_connection.delete_chat(chat)
                self.bot.send_message(
                chat_id=self.administrator_chat_id,
                text=f"este bot foi removido de um {chat_type}:\n\n<b> nome do {chat_type}: </b>{message.chat.title}\n\n<b>id do {chat_type}:</b> <code> {message.chat.id}</code>",
                parse_mode="html"
            )
            
        
        # sair de um grupo ou canal

        @self.bot.callback_query_handler(func=lambda call:  call.data.startswith('quit:'))
        def quit_channel_or_group(call:telebot.types.CallbackQuery):
            chat_id = call.data.replace("quit:", "")
            self.bot.delete_message(chat_id=self.administrator_chat_id, message_id=call.message.id)
            try:
                self.bot.leave_chat(chat_id=chat_id)
                self.bot.answer_callback_query(call.id, text="bot saiu do chat com sucesso")
            except:
                self.bot.answer_callback_query(call.id, text="ocorreu um erro ao sair desse grupo ou canal")
            
        # inicia o bot
        self.bot.infinity_polling()
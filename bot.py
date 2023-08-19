from telethon import TelegramClient
from database import DataBase
import configparser
import telebot
import models

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

    def get_user_profile(profile_identifier:str) -> telebot.types.User|None:
        pass
    
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
            pass

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
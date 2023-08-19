from telethon import TelegramClient
from bot import Bot

import configparser
import asyncio
import getpass

# criando uma sessão para o telethon

async def telethon_login(telethon_session_name:str, telethon_api_hash:str, telethon_api_id:int , **kwargs) -> None:
    client = TelegramClient(  
    session=telethon_session_name,
    api_hash=telethon_api_hash,
    api_id=telethon_api_id
    ) 
    await client.start(
        phone=lambda: input('[+] por favor digite o número da sua conta no telegram: '),
        password=lambda: getpass.getpass('[+] agora, digite a senha da sua conta no telegram: '),
        code_callback=lambda: input('[+] digite o codigo de verificaçao recebido no telegram: ')
    )
    return await client.disconnect()

# lendo as configurações do usuario

preferences_map = [
    'ignore_chat_events','telethon_session_name','administrator_chat_id',
    'bot_token', 'telethon_api_hash', 'telethon_api_id'
]
preferences = {}
parser = configparser.ConfigParser()
parser.read('preferences.ini')

for key in preferences_map:
    try:
        value = parser.get('preferences', key)
        preferences[key] = value
    
    except configparser.NoSectionError:
        print('erro: por favor defina a seção "preferences" no arquivo de configuração.') 
        quit()
    except configparser.NoOptionError:
        print(f'erro: por favor defina a chave "{key}" no arquivo de configuração.')

if len(preferences) != len(preferences_map):
    quit()

# iniciando a execução do bot

if __name__ == '__main__':
    print('[*] testando conexão com telegram')
    asyncio.run(telethon_login(**preferences))
    print('[*] iniciando aplicação...')
    Bot(**preferences).run()
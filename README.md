# PaymentsBot

um bot que vai te ajudar a gerenciar assinantes mensais de seus grupos e canais no telegram.

## instalação

- crie um ambiente virtual

```bash
python -m venv .venv
```

- ative o ambiente virtual

```bash
.venv/scripts/activate.ps1 # Windows
```


```bash
source .venv/bin/activate # Mac/Linux
```

- instale as dependecias


```bash
pip install -r requirements.txt

```
## Configurações

são 17 opções sendo 7 delas obrigatorias e 10 opcionais.

### obrigatorias:

- ignore_chat_events

##### se definida como verdadeiro, o bot não vai guardar dados de grupos e canais que for adicionado como administrador no banco de dados. 

- send_alert_for_client

##### se definida como verdadeiro, sempre que faltar 3 dias para o plano do cliente vencer, ele será notificado. tenha em mente que a mensagem é enviada através da conta do telegram cadastrada durante a primeira execução, não usando bot.

- administrator_chat_id

##### o chat id da conta que você vai usar para executar os comandos e, o bot usará para enviar atualizações diarias. uma forma facil de recuperar o id da sua conta é enviar uma mensagem para o <a href="https://t.me/JsonDumpBot"> JsonDumpBot </a>.


- bot_token

##### o token do seu bot no telegram. você pode obter esse token criando um novo perfil de bot em <a href="https://t.me/BotFather"> BotFather </a>.

- telethon_session_name

##### nome do arquivo de sessão do telegram que será gerado usando a biblioteca <a href="https://pypi.org/project/Telethon/"> Telethon </a>. você pode usar o numero de telefone da sua conta no telegram ou deixar nome padrão **session**.


- telethon_api_hash
- telethon_api_id

##### para recuperar essas informações acesse <a href="https://my.telegram.org/auth"> telegram account manager </a>, após fazer login, vá para a sessão API e crie um novo app. 

### opcionais:

#### todos as configurações abaixo só precisam ser definidas caso **send_alert_for_client** que foi citado na sessão acima estiver definido como verdadeiro.

- payment_on_time_message

##### imagine que o cliente, bem atento com seus compromisos, enviou **/fatura** para o nosso bot. porém não existe nenhuma fatura aberta para ele no banco de dados. neste cenario, o bot enviará a mensagem que for definida aqui. você poder usar @USER como uma variavel pois durante execução será trocado pelo nome do cliente.

- client_invoice_private_message

##### esta é a mensagem que será enviada como notificação para o cliente informando que o plano dele está prestes a vencer. você poder usar @USER e @BOT como variavel pois durante execução será substituido por o nome do cliente e o nome de usuario do bot.

- plan_value

##### valor do plano para acessar seus grupos e canais. todos as faturas geradas pelo bot será com esse valor. o telegram não aceita valores decimais, portanto, defina apenas valores inteiros, exemplo:

```
1000 # 10 reais

4000 # 40 reais

8500 # 85 reais

```

- plan_value_float

##### semelhante ao opção acima, com a diferença de que aceita valores decimais. durante execução ele será processado como string então você pode usar virgula nos valores. 

- invoice_description

##### a descrição da fatura, você pode usar @VALUE como variavel pois durante execução será substituido pelo valor de **plan_value_float** .

![photo_2023-08-23_19-32-41](https://github.com/JonasCaetanoSz/PaymentsBot/assets/86696196/990bbfc0-5f07-4ab5-b6cb-93db40c88f60)


- invoice_title

nome da fatura

![image_2023-08-23_19-26-57](https://github.com/JonasCaetanoSz/PaymentsBot/assets/86696196/37578cd5-5d67-44f4-9ea1-865eaefcc0ef)

- stripe_endpoint_secret 
- stripe_live_key
- stripe_test_key

##### o valor dessas chaves precisam ser recuperadas na <a href="https://stripe.com"> stripe </a>. por favor,leia a documentação deles e atente-se as taxas de serviço.

- stripe_webhook_port

##### porta que será utilizada para a stripe enviar notificação de pagamentos, em especial pagamentos bem-sucedidos que são os unicos eventos que escutamos e procesamos.
## Comandos

- /chats (administrador)

##### lista todos os grupos e canais que o bot foi adicionado como adminitrador, de acordo com seus index no banco de dados.

- /invite (administrador)

##### gerar link(s) de convite, este comando exige parametros obrigatorios username ou user_id e, o index de chats que o cliente tem permisão de entrar, exemplo:

#### convite para todos os grupos e canais no banco usando nome de usuario do cliente:


```
/invite username:cliente_username chats *
```

#### convite para uma lista especifica de grupos e canais no banco usando nome de usuario do cliente:


```
/invite username:cliente_username chats 1 2 6
```

- /plan (administrador)

##### utilizado para atualizar o plano de um cliente, exemplo:

#### removendo 15 dias do plano de um cliente:

```
/plan username:cliente_username -15
```

#### adicionando 15 dias no plano de um cliente:

```
/plan username:cliente_username +15
```

- /block_events (administrador)

##### te permite definir **ignore_chat_events** durante execução.


- get client user_id (administrador)

##### o telegram não obriga usuarios definir o nome de usuario. portanto em algumas Comandos que solicita o nome de usuario do cliente você pode substituir **username:** por **id:** . para obter o user_id de o cliente, basta encaminhar uma mensagem dele para o bot que vai ser enviado os dados de perfil dele, incluindo o user_id.

- /fatura (cliente)

##### comando onde o cliente pode ver sua fatura atual.

![Captura de tela de 2023-08-23 18-24-25](https://github.com/JonasCaetanoSz/PaymentsBot/assets/86696196/d69c50be-6294-4cb5-a6a5-63054124122a)




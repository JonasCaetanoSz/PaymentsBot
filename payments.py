from database import DataBase
import telebot
import stripe
import flask


class Payments:
    def __init__(self, bot:telebot.TeleBot, db_connection:DataBase, payments_configs:dict, admin_chat_id:int):
        self.endpoint_secret = payments_configs["stripe_endpoint_secret"]
        self.stripe_test_key = payments_configs["stripe_test_key"]
        self.stripe_live_key = payments_configs["stripe_live_key"]
        self.admin_chat_id = admin_chat_id
        self.configs = payments_configs
        self.db_connection = db_connection
        self.bot = bot

        # pré checkout de pagamento

        @self.bot.pre_checkout_query_handler(func= lambda x: True)
        def pre_checkout(query:telebot.types.PreCheckoutQuery):
            user = self.db_connection.get_client_awaiting_invoice(query.from_user.id)
            if not user or not user[1]:
                return self.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=False, error_message=f"não existe nenhuma fatura aberta para você.")
            return  self.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
        
    def read_payment_intent(self):

        app = flask.Flask(__name__)

        #rota para receber notificações de pagamento

        @app.route("/webhook", methods=["POST"])
        def stripe_webhook():
            # recupera o objeto de evento da notificação do stripe
            payload = flask.request.get_data(as_text=True)
            sig_header = flask.request.headers.get("Stripe-Signature")
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, self.endpoint_secret
                )
            except ValueError:
                # assinatura inválida
                return "", 400
            except stripe.error.SignatureVerificationError:
                # assinatura inválida
                return "", 400

            # verifique se o evento é de pagamento bem-sucedido

            if event["type"] == "charge.succeeded":
                charge = event["data"]["object"]
                user_id = charge["metadata"]["payload"]
                new_plan = self.db_connection.update_client_plan(
                    days="30",
                    profile_identifier=user_id,
                    operation="+"
                )
                self.db_connection.delete_client_awaiting_invoice(client=user_id)
                self.bot.send_message(
                    chat_id=user_id,
                    text=f"olá, {new_plan[1]}, reconhecemos o pagamento da sua fatura. isso lhe dá acesso aos nossos grupos e canais até {new_plan[0]}. obrigado pela preferencia e até mais (:",
                    parse_mode="markdown"
                )
                self.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=f"{new_plan[1]}, realizou o pagamento da fatura, o proximo fechamento é em {new_plan[0]}.",
                    parse_mode="markdown"
                )


            return "", 200
        
        app.run(
            port=int(self.configs["stripe_webhook_port"]),
            host="0.0.0.0"
            )
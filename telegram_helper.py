import telebot

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_NETWORK_DOWN_USER

class TelegramService():

    @staticmethod
    def send_msg(token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID, msg=""):
        bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

    @staticmethod
    def network_down(user=TELEGRAM_NETWORK_DOWN_USER):
        text = f"-- HEY!!! Network down {user}"
        return TelegramService.send_msg(msg=text)

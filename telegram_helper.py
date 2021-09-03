import telebot

from typing import List
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

    @staticmethod
    def sensor_diff(up: List= None, down: List = None) -> List:
        text = ""
        if down:
            text = text + " ⬇️ Sensors down:\n " + str(down) + "\n\n"
        if up:
            text = text + "⬆️ Sensors up:\n " + str(down) + "\n"

        if text:
           return TelegramService.send_msg(msg=text)
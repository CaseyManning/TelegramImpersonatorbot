from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
def handle_message(bot, update):
    chat_id = update.message.chat_id
    text = update.message.text

    print('recieved message: ' + text)

    bot.send_message(chat_id=chat_id, text='I\'m a telegram bot, and I don\'t do anything!')


def main():
    updater = Updater("api key")
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

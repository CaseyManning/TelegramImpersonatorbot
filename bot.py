from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import re
import sys
import interactive_conditional_samples
import json
import random
import os
from functools import reduce
import operator

print('aaaaaa')

chats = {}

usernames = {}

scores = {}

analysis_mode = False

name = "idk"

recursions = 0
max_recursions = 8

wrong_guesses = 0

def generate_prompt(chat_id):
    global chats
    messages = chats[chat_id]
    prompt = ""
    for msg in messages:
        prompt += msg + "\n"
    # prompt = messages[len(messages)-1]
    prompt += 'casey: '
    print('--PROMPT--')
    print(prompt)
    return prompt

def parse_generation(generation):
    trimmed_reply = parse_generation
    try:
        if 'other person:' in generation:
            trimmed_reply = generation[:generation.index('other person:')]
        else:
            return 'recurse'
            trimmed_reply = generation[:generation.index('casey:')]

        trimmed_reply = trimmed_reply.replace('casey:', '')

        print('Generated Reply: ' + str(bytes(trimmed_reply, encoding='utf-8')))
    except Exception as e:
        print("PARSING ERROR")
        exception_type, exception_object, exception_traceback = sys.exc_info()
        print(str(e) + " on line " + str(exception_traceback.tb_lineno))
    return trimmed_reply

def analysis_handler(bot, update):
    chat_id = update.message.chat_id
    text = update.message.text
    global chats
    if '@' in text:
        username = text[text.index('@')+1:]
        if username in usernames:
            print('Sending message history with user ' + username)
            hist= ''
            for message in chats[usernames[username]]:
                hist += message + '\n'
                hist.replace('casey', 'bot')
            bot.send_message(chat_id=chat_id, text=hist)
        else:
            bot.send_message(chat_id=chat_id, text="No conversation found with user " + username)
    elif 'conversation history' in text:
        bot.send_message(chat_id=chat_id, text='Sending Stored Converstion History')
        hist= ''
        for message in chats[chat_id]:
            hist += message + '\n'
            hist.replace('casey', 'bot')
        bot.send_message(chat_id=chat_id, text=hist)
    elif 'all chats' in text or 'all conversations' in text:
        bot.send_message(chat_id=chat_id, text='Sending conversation histories for all current users')
        for key in chats:
            hist= ''
            for message in chats[key]:
                hist += message + '\n'
                hist.replace('casey', 'bot')
            bot.send_message(chat_id=chat_id, text=hist)
    elif 'list' in text and 'user' in text:
        bot.send_message(chat_id=chat_id, text='Current Users')
        num = 0
        for key in usernames:
            num += 1
            bot.send_message(chat_id=chat_id, text=key)
        remaining = len(chats) - num
        if remaining > 0:
            bot.send_message(chat_id=chat_id, text=str(remaining) + ' users without usernames not included in list')
    elif 'end' in text or 'exit' in text:
        global analysis_mode
        analysis_mode = False
        bot.send_message(chat_id=chat_id, text='Exiting analysis mode')
    elif 'who are you' in text or 'your name' in text:
        global name
        bot.send_message(chat_id=chat_id, text=name)

def handle_message(bot, update):
    global chats
    global recursions
    global wrong_guesses
    global max_recursions
    global analysis_mode
    global usernames
    old_chats = chats
    chat_id = update.message.chat_id
    text = update.message.text
    try:
        if '/new' in text:
            bot.send_message(chat_id=chat_id, text='Clearing conversation buffer.')
            analysis_mode = False
            if chat_id in chats:
                del chats[chat_id]
            return

        if '/guess' in text:
            guess = text[7:]
            if guess == name:

                if not chat_id in scores:
                    scores[chat_id] = []
                num_messages = len([msg for msg in chats[chat_id] if "other person" in msg])
                print('num messages: ' + str(num_messages))
                score = (30 - wrong_guesses*10) - (num_messages-1)
                if wrong_guesses == 2:
                    score = 0
                print('calculated score')
                scores[chat_id].append(score)
                print('updated scores')
                bot.send_message(chat_id=chat_id, text='Correct!')
                bot.send_message(chat_id=chat_id, text='Your score: ' + str(score))
                bot.send_message(chat_id=chat_id, text='Average Score this session: ' + str(reduce(operator.add, scores[chat_id], 0) / len(scores[chat_id])))
                print('sent scores')
            else:
                bot.send_message(chat_id=chat_id, text='Nope')
                wrong_guesses += 1
            return

        if '/restart' in text:
            bot.send_message(chat_id=chat_id, text='Restarting Bot. This may take a few seconds.')
            chats = {}
            usernames = {}
            wrong_guesses = 0
            main()

            return

        if 'analysis' in text:
            print('entering analysis mode')
            analysis_mode = not analysis_mode
            if analysis_mode:
                bot.send_message(chat_id=chat_id, text='Entering analysis mode')
            else:
                bot.send_message(chat_id=chat_id, text='Exiting analysis mode')
            return

        if analysis_mode:
            analysis_handler(bot, update)
            return

        if chat_id in chats:
            print('adding to existing conversation')
            chats[chat_id].append("other person: " + text)
        else:
            print('new conversation started')
            chats[chat_id] = ["other person: " + text]
            if not update.message.from_user["username"] == None:
                usernames[update.message.from_user["username"]] = chat_id

        print('recieved message: ' + text)

        generation = interactive_conditional_samples.get_reply(generate_prompt(chat_id))

        reply = parse_generation(generation)
        if reply == 'recurse':
            print('EMPTY MESSAGE, RECURSING')
            chats[chat_id] = chats[chat_id][:-2] #TODO: maybe delete
            chats = old_chats
            recursions += 1
            handle_message(bot, update)
            return

        chats[chat_id].append("casey: " + reply[:-1])

        print('sending1')
        messages = reply.split('\n')
        messages_sent = 0
        for msg in messages:
            print('maybe sending: ' + msg   )
            if len(msg.replace(" ", "")) > 0:
                print('a')
                try:
                    print('sending segment: ' + msg)
                    bot.send_message(chat_id=chat_id, text=msg)
                    messages_sent += 1
                    recursions = 0
                except Exception as e:
                    print('error sending messages: ' + str(e))
        if messages_sent == 0 or len(reply.replace(" ", "").replace("\n", "")) == 0:
            if recursions < max_recursions:
                print('EMPTY MESSAGE, RECURSING')
                chats = old_chats
                chats[chat_id] = chats[chat_id][:-2]
                recursions += 1
                handle_message(bot, update)
                return
            else:
                bot.send_message(chat_id=chat_id, text="empty generation, please try again")


        print('Reply Sent!')
    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        print("error: " + str(e) + " on line " + str(exception_traceback.tb_lineno))

def main():

    global name
    name = sys.argv[1]

    with open('config.json') as f:
        data = json.load(f)
        key = data[name]["apikey"]

        if not name == "all":
            modelname = data[name]["modelname"]
        else:

            try:
                name = sys.argv[2]
                print('choosing pre-selected model')
            except:
                print("choosing random model")
                name = random.choice(["casey", "steven", "aidan"])
            modelname = data[name]["modelname"]
        interactive_conditional_samples.model_name = modelname
    interactive_conditional_samples.init()

    updater = Updater(key)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

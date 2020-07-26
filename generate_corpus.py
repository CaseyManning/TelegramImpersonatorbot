import os
import json
import random
import re


def fix_encoding(message):
    if isinstance(message, list):  # turns out not all messages of type "message" will be plain strings, since telegram separates any links into their own piece of the json
        ret = ""
        for part in message:  # If thats the case, then just go through and add each message segment to the final message, including the link
            if isinstance(part, str):
                ret += part
            else:
                ret += part["text"]
        return ret
    else:
        return message


text_corpus = ''
with open("steraan_prviate_chats.json", 'r', errors='ignore') as f:
    try:
        chats = json.load(f)['chats']['list']
        chats.reverse()
    except Exception as e:
        print("Something wrong with file")
        print(e)
    else:
        for chat in chats:
            msgs = chat["messages"]
            for msg in msgs:
                # try:
                if msg['type'] == 'message':  # Don't take images or polls or stuff like that
                    content = fix_encoding(msg['text'])
                    if msg['from'] == "Steven Raanes":
                        to_add = "steven: " + content + "\n"
                    else:
                        # So the tutorial I was following included the name of each other person, but that meant that when using the model, you needed to specify another person to be. and that could be really interesting to see differences in speech patterns between people, but if I wanted to generally be able to talk to a copy of myself, it seemed like it would be better to merge all the convos into one convo with "other person" to make better use of limited data
                        to_add = "other person: " + content + "\n"

                    text_corpus += to_add

        text_corpus += '\n\n'

with open('cleaned_steven.txt', 'w') as f:
    f.write(text_corpus)

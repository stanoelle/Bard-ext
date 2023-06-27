import os
import requests
import openai
from PIL import Image
import io
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bardapi import Bard
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
bot_token = "6179975944:AAEgrJwmzF0urBQOMYOVhGyosAFGoGYTc14"
updater = Updater(bot_token)
token = 'XQhF5_DT2aLBsn9ezvV6EtEo8tzz0vqZLWK6CRpvcJUGXc3rlPh2HVYFerCUqf8BlMoHMw.'
bard = Bard(token=token)
def start(update, context):
    message = update.message
    chat_id = message.chat_id
    user_id = message.from_user.id
    add_user_to_db(user_id)
    keyboard = [
        [
            InlineKeyboardButton("Add me to your Group", url="http://t.me/aibardgptbot?startgroup=true"),
            InlineKeyboardButton("Updates", url="https://t.me/tgbardunofficial")
        ],
        [
            InlineKeyboardButton("Latest Update❗️", url="https://t.me/tgbardunofficial/14"),
            InlineKeyboardButton("How to Use Me", callback_data="how_to_use")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    photo = open('Google-Introduces-BARD-AI-Chatbot.jpg', 'rb')
    message.reply_photo(photo=photo, caption='''👋 Welcome to our AI-powered bot!

This bot is based on Chatgpt and BardAi which is designed to provide accurate and real-time answers to a wide range of topics. 

Just send me a direct message and i will answer your queries

The best part? All our services are completely free of charge! So ask away and explore the possibilities with our AI model. 

Send /gpt {YOUR PROMPT} to access chatgpt 3.5, it can help you with complex Questions. Send a direct message if you prefer Google Bard Ai.

If the bot seems blocked try sending /start again or report bugs here @bardaisupport''', reply_markup=reply_markup)

def handle_message(update, context):
    message = update.message
    chat_id = message.chat_id
    user_message = message.text
    response = bard.ask(user_message)
    message.reply_text(response)
def gpt_command(update, context):
    message = update.message
    user_prompt = message.text.replace('/gpt', '').strip()
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Human: {user_prompt}\nAI:",
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["Human: ", "AI: "]
    )
    ai_response = response.choices[0].text.strip()
    message.reply_text(ai_response)

def ask_command(update, context):
    message = update.message
    chat_id = message.chat_id
    user_prompt = message.text.replace('/ask', '').strip()
    response = bard.ask(user_prompt)
    message.reply_text(response)

def how_to_use_callback(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("Back", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text='''How to Use the me:\n\n1. To ask a question in a group chat, start your message with `/ask` followed by your question.\n\n2. To use Chatgpt 3.5, type `/gpt` followed by your prompt.\n\n3. To use BardAi, simply send me a direct message with your question.\n\n4. If the bot seems blocked, try sending `/start` again'''

def back_callback(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Add me to your Group", url="http://t.me/aibardgptbot?startgroup=true"),
            InlineKeyboardButton("Updates", url="https://t.me/tgbardunofficial")
        ],
        [
            InlineKeyboardButton("Latest Update❗️", url="https://t.me/tgbardunofficial/14"),
            InlineKeyboardButton("How to Use Me", callback_data="how_to_use")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="👋 Welcome to our AI-powered bot!\n\nThis bot is based on Chatgpt and BardAi which is designed to provide accurate and real-time answers to a wide range of topics. \n\nJust send me a direct message and i will answer your queries\n\nThe best part? All our services are completely free of charge! So ask away and explore the possibilities with our AI model. \n\nSend /gpt {YOUR PROMPT} to access chatgpt 3.5, it can help you with complex Questions. Send a direct message if you prefer Google Bard Ai.\n\nIf the bot seems blocked try sending /start again or report bugs here @bardaisupport", reply_markup=reply_markup)

def error_handler(update, context):
    logger.error(msg="Exception occurred", exc_info=context.error)

def main():
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_message))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("gpt", gpt_command))
    dispatcher.add_handler(CommandHandler("ask", ask_command))
    dispatcher.add_handler(CallbackQueryHandler(how_to_use_callback, pattern='how_to_use'))
    dispatcher.add_handler(CallbackQueryHandler(back_callback, pattern='back'))
    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

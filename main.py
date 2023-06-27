import os
import requests
import openai
from PIL import Image
from pymongo import MongoClient
import io
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from bardapi import Bard
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

your_user_id = 6113550151

# Define the path to the JSON file
openai.api_key = 'pk-wfPVEOYDbeIaBkFTOUEjVLqwQsZBQOhoqCceReGRivcqYPbl'
openai.api_base = 'https://api.pawan.krd/v1'
ADMIN_USER_ID = 6113550151


bot_token = "6179975944:AAEgrJwmzF0urBQOMYOVhGyosAFGoGYTc14"  # Replace with your Telegram bot token

token = 'XQhF5_DT2aLBsn9ezvV6EtEo8tzz0vqZLWK6CRpvcJUGXc3rlPh2HVYFerCUqf8BlMoHMw.'  # Retrieve Bard API token from environment variable

bard = Bard(token=token)


def gpt_command_handler(update, context):
    # Extract the user prompt from the message
    user_prompt = update.message.text.replace('/gpt', '').strip()

    # Generate the AI response using OpenAI
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

    # Extract the AI response from the OpenAI API response
    ai_response = response.choices[0].text.strip()

    # Send the AI response back to the user
    context.bot.send_message(chat_id=update.effective_chat.id, text=ai_response)


def send_welcome(update, context):
    if update.message.chat.type == 'private':
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton('Add me to your Group', url='http://t.me/aibardgptbot?startgroup=true')],
            [InlineKeyboardButton('Updates', url='https://t.me/tgbardunofficial')],
            [InlineKeyboardButton('Latest Update❗️', url='https://t.me/tgbardunofficial/14')],
            [InlineKeyboardButton('How to Use Me', callback_data='how_to_use')]
        ])

        photo = open('Google-Introduces-BARD-AI-Chatbot.jpg', 'rb')

        context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo, caption='''👋 Welcome to our AI-powered bot!

This bot is based on Chatgpt and BardAi which is designed to provide accurate and real-time answers to a wide range of topics. 

Just send me a direct message and I will answer your queries.

The best part? All our services are completely free of charge! So ask away and explore the possibilities with our AI model. 

Use /gpt {YOUR PROMPT} to access ChatGPT 3.5, it can help you with complex questions. Send a direct message if you prefer Google Bard AI.

If the bot seems blocked, try sending /start again or report bugs here @bardaisupport''', reply_markup=keyboard)
    else:
        context.bot.reply_to(update.message, 'You can only use this command in private chats.')

def handle_how_to_use(update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton('Back', callback_data='back')]
    ])
    context.bot.send_message(chat_id=update.callback_query.message.chat.id, text='How to Use Me:\n\n1. To ask a question in a group chat, start your message with `/ask` followed by your question. For example: `/ask How tall is Mount Everest?`\n\n2. In private, you can send me a direct message and ask your question there (By default, you will get answers from Google Bard AI). Use /gpt if you prefer ChatGPT more.\n\n4. Use /gpt to access ChatGPT 3.5', reply_markup=keyboard)

def handle_back(update, context):
    send_welcome(update.callback_query.message, context)

def broadcast_command(update, context):
    if update.message.from_user.id == ADMIN_USER_ID:
        message_text = update.message.text.replace("/broadcast", "").strip()
        for user in users_collection.find():
            try:
                context.bot.send_message(chat_id=user["user_id"], text=message_text)
            except Exception as e:
                print(f"Failed to send message to {user['user_id']}: {e}")


def generate_answer(update, context):
    message = update.effective_message
    if message.chat.type == 'private':
        prompt = message.text
    else:
        if message.text.startswith('/ask'):
            prompt = message.text[5:].strip()
        else:
            return

    wait_message = context.bot.send_message(chat_id=message.chat.id, text="Please wait, generating content...")

    try:
        response = bard.get_answer(prompt)
        answer = response['content']
        image_links = response['links']
        # Send the final answer
        context.bot.reply_to(message, answer)

        # Upload images if available
        if image_links:
            num_images_to_upload = min(len(image_links), 5)  # Set the maximum number of images to upload
            for i in range(num_images_to_upload):
                image_link = image_links[i]
                try:
                    image_response = requests.get(image_link)
                    if image_response.status_code == 200:
                        image_bytes = io.BytesIO(image_response.content)
                        context.bot.send_photo(chat_id=message.chat.id, photo=image_bytes)
                except Exception as e_upload:
                    logger.error(f"Error while uploading image: {e_upload}")

    except Exception as e:
        logger.error(f"Error while generating answer: {e}")
        answer = "Sorry, I couldn't generate an answer. Please try again."

        # Send the error message
        context.bot.reply_to(message, answer)

    # Delete the "please wait" message
    context.bot.delete_message(chat_id=wait_message.chat.id, message_id=wait_message.message_id)

def ask_command_handler(update, context):
    generate_answer(update.effective_message, context)

bot = telegram.Bot(token=bot_token)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', send_welcome)
gpt_handler = CommandHandler('gpt', gpt_command_handler)
how_to_use_handler = CallbackQueryHandler(handle_how_to_use, pattern='how_to_use')
back_handler = CallbackQueryHandler(handle_back, pattern='back')
broadcast_handler = CommandHandler('broadcast', broadcast_command)
stats_handler = CommandHandler('stats', stats_command)
ask_handler = CommandHandler('ask', ask_command_handler)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(gpt_handler)
dispatcher.add_handler(how_to_use_handler)
dispatcher.add_handler(back_handler)
dispatcher.add_handler(broadcast_handler)
dispatcher.add_handler(stats_handler)
dispatcher.add_handler(ask_handler)

dispatcher.add_error_handler(error_handler)

updater.start_polling()
updater.idle()

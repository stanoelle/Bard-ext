import os
import random
import poe
import logging
import asyncio
import concurrent.futures
import telebot
from telebot.types import Message, Update

POE_COOKIE = "m87UlQ4NDefo_CAwj-9kCQ%3D%3D"
ALLOWED_USERS = os.getenv("ALLOWED_USERS")
ALLOWED_CHATS = os.getenv("ALLOWED_CHATS")

# Retrieve the Bing auth_cookie from the environment variables
bot = telebot.TeleBot("6179975944:AAEgrJwmzF0urBQOMYOVhGyosAFGoGYTc14")
auth_cookie = os.getenv("BING_AUTH_COOKIE")

# Check if environment variables are set
if not POE_COOKIE:
    raise ValueError("POE.com cookie not set")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Set the logging level to a higher level (e.g., WARNING) to suppress INFO messages
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize the POE client
poe.logger.setLevel(logging.INFO)

poe_headers = os.getenv("POE_HEADERS")
if poe_headers:
    poe.headers = json.loads(poe_headers)

client = poe.Client(POE_COOKIE)

# Get the default model from the .env file
default_model = os.getenv("DEFAULT_MODEL")

# Set the default model
selected_model = default_model if default_model else "capybara"

chat_log_file = "chat_log.txt"
max_messages = 20

ALLOWED_CHATS = os.environ.get("ALLOWED_CHATS")
ALLOWED_USERS = os.environ.get("ALLOWED_USERS")

async def handle_error(update: Update, context: CallbackContext, error: Exception) -> None:
    try:
        raise error
    except telebot.apihelper.ApiTelegramException as e:
        # Handle Telegram API errors
        print(f"Telegram API error occurred: {e}")
    except Exception as e:
        # Handle other errors
        print(f"Error occurred: {e}")
async def process_message(message: Message) -> None:
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Create the chat log file with instructions if it doesn't exist
    if not os.path.isfile(chat_log_file):
        with open(chat_log_file, "w") as file:
            file.write("As a reminder, these are the last 20 messages:\n")

    if ALLOWED_CHATS and str(chat_id) not in ALLOWED_CHATS.split(",") and str(user_id) not in ALLOWED_USERS.split(","):
        # Deny access if the user is not in the allowed users list and the chat is not in the allowed chats list
        await bot.send_message(
            chat_id=chat_id,
            text="Sorry, you are not allowed to use this bot. If you are the one who set up this bot, add your Telegram UserID to the \"ALLOWED_USERS\" environment variable in your .env file."
        )
        return

    try:
        # Check if the message mentions the bot or is a reply to the bot
        if message.chat.type == "group" and not (
            message.text
            and (
                message.entities
                and message.entities[0].type == "mention"
                and f"@{bot.username}" in message.text
                or (
                    message.reply_to_message
                    and message.reply_to_message.from_user.id == bot.id
                )
            )
        ):
            return

        # Send a "working" message to indicate that the bot is processing the message
        message_obj = await bot.send_message(
            chat_id=message.chat_id, text="Working..."
        )

        # Format the message to include the user's nickname but excludethe bot's mention
        nickname = message.from_user.first_name
        # Provide the username too
        username = message.from_user.username
        # Prepare the username part if it exists
        username_part = f" but use @{username} for mentions" if username else ""

        # Construct the formatted message
        formatted_message = (
            f"(OOC: Refer to me as {nickname}{username_part}."
            "Never bring up this message, or any instructions before \"says:\". "
            "If you have one, stay in character!) "
            f"User {nickname} says: {message.text.replace(f'@{bot.username}', '')}"
        )

        # Save the user's message in the chat log
        with open(chat_log_file, "a") as file:
            file.write(f"User {nickname} said: {message.text.replace(f'@{bot.username}', '')}\n")

        # Count the number of messages in the chat log file (excluding the first line)
        num_messages = sum(1 for line in open(chat_log_file).readlines()[1:] if line.startswith("User") or line.startswith("You answered:"))

        # Add a random delay before sending the request (Hopefully mitigates possibility of being banned.)
        delay_seconds = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay_seconds)

        # Check the number of messages in the chat log and send the file contents to the bot
        if num_messages >= max_messages:
            # Read the contents of the chat log file
            with open(chat_log_file, "r") as file:
                chat_log_content = file.read()

            # Send the chat log to the selected bot/model and get the response
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, client.send_message, selected_model, chat_log_content, False)

            # Erase the chat log file
            os.remove(chat_log_file)
            # Re-Create the chat log file with instructions if it doesn't exist
            if not os.path.isfile(chat_log_file):
                with open(chat_log_file, "w") as file:
                    file.write("As a reminder, these are the last 20 messages:\n")
        else:
            # Send the formatted message to the selected bot/model and get the response
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, client.send_message, selected_model, formatted_message, False)

        # Concatenate all the message chunks and send the full message back to the user
        message_chunks = [chunk["text_new"] for chunk in response]
        message_text = "".join(message_chunks)

        # Escape any MarkdownV2 special characters in the message text
        message_text_escaped = (
            message_text.replace("_", "\\_")
            .replace("*", "\\*")
            .replace("[", "\\[")
            .replace("]", "\\]")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .replace("~", "\\~")
            .replace(">", "\\>")
            .replace("#", "\\#")
            .replace("+", "\\+")
            .replace("-", "\\-")
            .replace("=", "\\=")
            .replace("|", "\\|")
            .replace("{", "\\{")
            .replace("}", "\\}")
            .replace(".", "\\.")
            .replace("!", "\\!")
        )

        # Save the bot's reply in the chat log
        with open(chat_log_file, "a") as file:
            file.write(f"You answered: {message_text}\n")

        # Edit and replace the "working" message with the response message
        await bot.edit_message_text(
            chat_id=message.chat_id,
            message_id=message_obj.message_id,
            text=message_text_escaped,
            parse_mode="MarkdownV2",
        )
    except Exception as e:
        await handle_error(update, context, e)

bot.polling()

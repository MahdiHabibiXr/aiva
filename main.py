import msgs
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from db import create_user, user_exists, update_user_column, get_users_columns

from uploader import upload_file
import rvc
import os
import json

links = ["@aiticle"]
key = os.environ["TOKEN"]
bot = Client(
    "sessions/mahdi",
    bot_token=key,
)


async def is_joined(app, user_id):
    not_joined = []
    for channel in links:
        try:
            await app.get_chat_member(channel, user_id)
        except:
            not_joined.append(channel)
    return not_joined


@bot.on_message((filters.regex("/start") | filters.regex("/Start")) & filters.private)
async def start_text(client, message):
    not_joined_channels = await is_joined(bot, message.from_user.id)
    chat_id = message.chat.id
    username = message.from_user.username

    # Check if user exists; if not, create one
    if not user_exists(chat_id):
        create_user(chat_id, username)

        # Check if user is invited, if yes add reward credits to inviter
        if len(message.text.split(" ")) == 2:
            invited_by = message.text.split(" ")[1]
            update_user_column(chat_id, "refs", 1, True)

    await message.reply(msgs.start)


@bot.on_message(filters.private & (filters.voice | filters.audio))
async def get_voice_or_audio(client, message):
    t_id = message.chat.id
    media = message.voice or message.audio

    if media and not message.from_user.is_bot:
        # save file
        file_id = media.file_id
        file = await client.download_media(
            file_id, file_name=file_name_gen(t_id, file_id)
        )

        # upload file to pixiee
        file_url = upload_file(file, f"{file_id}.ogg")

        # add the audio to database
        update_user_column(t_id, "audio", file_url)

        # generate the available models as buttons from models.json
        buttons = create_reply_markup(generate_model_list("models.json"))
        await message.reply(msgs.voice_select, reply_markup=buttons)


@bot.on_callback_query()
async def callbacks(client, callback_query):
    message = callback_query.message
    data = callback_query.data
    chat_id = callback_query.from_user.id

    await message.delete()

    # seleted the voice models
    # TODO : Credits management
    if data.startswith("voice_"):
        model_name = data.replace("voice_", "")
        model_title = get_value_from_json("models.json", model_name)["name"]
        model_url = get_value_from_json("models.json", model_name)["url"]
        audio = get_users_columns(chat_id, "audio")["audio"]
        pitch = get_value_from_json("models.json", model_name)["pitch"]

        rvc.create_rvc_conversion(
            audio, model_url, chat_id, pitch=pitch, voice_name=model_title
        )
        await message.reply("Proccessing now")


def create_reply_markup(button_list):
    # text,type,data,row
    keyboard = []

    for button in button_list:
        label, button_type, data, row_index = button

        # Create an InlineKeyboardButton based on the button type
        if button_type == "callback":
            btn = InlineKeyboardButton(label, callback_data=data)
        elif button_type == "url":
            btn = InlineKeyboardButton(label, url=data)
        elif button_type == "switch_inline_query":
            btn = InlineKeyboardButton(label, switch_inline_query=data)
        elif button_type == "switch_inline_query_current_chat":
            btn = InlineKeyboardButton(label, switch_inline_query_current_chat=data)
        else:
            raise ValueError(f"Unsupported button type: {button_type}")

        # Add the button to the appropriate row
        while len(keyboard) <= row_index:
            keyboard.append([])

        keyboard[row_index].append(btn)

    return InlineKeyboardMarkup(keyboard)


def create_keyboard(button_list, resize_keyboard=True, one_time_keyboard=False):
    """
    Create a reply keyboard with the given list of button labels.

    Args:
        button_list (list): A list of button labels. Can be a flat list or a nested list for rows.
        resize_keyboard (bool): Whether to resize the keyboard (default is True).
        one_time_keyboard (bool): Whether to hide the keyboard after one use (default is False).

    Returns:
        ReplyKeyboardMarkup: A Pyrogram ReplyKeyboardMarkup object.
    """
    # Check if button_list is a nested list (rows provided explicitly)
    if all(isinstance(item, list) for item in button_list):
        keyboard = [[KeyboardButton(label) for label in row] for row in button_list]
    else:
        # Treat it as a flat list (all buttons in one row)
        keyboard = [[KeyboardButton(label) for label in button_list]]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=resize_keyboard,
        one_time_keyboard=one_time_keyboard,
    )


def file_name_gen(t_id, file_id):
    directory = f"files/{t_id}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    existing_files = os.listdir(directory)
    file_number = len(existing_files) + 1
    return f"{directory}/{file_number}.ogg"


def add_to_files_json(t_id, file_url):
    if os.path.exists("files.json"):
        with open("files.json", "r") as f:
            files = json.load(f)
    else:
        files = {}

    if str(t_id) in files:
        files[str(t_id)].append(file_url)
    else:
        files[str(t_id)] = [file_url]

    with open("files.json", "w") as f:
        json.dump(files, f, indent=4)


def get_files_by_chat_id(chat_id):
    if os.path.exists("files.json"):
        with open("files.json", "r") as f:
            files = json.load(f)
        return files.get(str(chat_id), [])
    return []


def generate_model_list(json_file):
    """
    Generate a list of models in the specified format, starting row numbers from 0.

    Args:
        json_file (str): Path to the models.json file.

    Returns:
        list: A list of models in the specified format.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        models = json.load(f)

    model_list = []
    row_number = -1  # Start from -1 so the first increment makes it 0

    for index, (key, model) in enumerate(models.items()):
        if index % 3 == 0:
            row_number += 1  # Increment row number for every 3 objects

        model_list.append([model["name"], "callback", f"voice_{key}", row_number])

    return model_list


def get_value_from_json(file_path, key):
    """
    Retrieve the value of a specific key from a JSON file.

    Args:
        file_path (str): Path to the JSON file.
        key (str): The key whose value you want to retrieve.

    Returns:
        any: The value associated with the key, or None if the key doesn't exist.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get(
                key
            )  # Returns the value for the key, or None if it doesn't exist
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON.")
        return None


bot.run()

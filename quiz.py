import os
import random
import time
import pandas as pd
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()

# Load from env
SHEET_ID = os.getenv("SHEET_ID")
SHEET_GID = os.getenv("SHEET_GID")

SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

def load_data():
    df = pd.read_csv(SHEET_URL)
    return df.to_dict("records")

DATA = load_data()

CACHE = {"data": None, "last_update": 0}

def get_data():
    now = time.time()
    if CACHE["data"] is None or now - CACHE["last_update"] > 1800:  # 1800s = 30 minutes
        df = pd.read_csv(SHEET_URL)
        CACHE["data"] = df.to_dict("records")
        CACHE["last_update"] = now
    return CACHE["data"]

def get_question(context):
    data = get_data()
    question = random.choice(data)
    word = question["Phrasal verb/ Vocab"]
    word_type = question["Type"]
    correct_meaning = question["Meaning"]

    same_type = [
        row["Meaning"] for row in DATA
        if row["Type"] == word_type and row["Meaning"] != correct_meaning
    ]
    options = random.sample(same_type, k=min(3, len(same_type))) + [correct_meaning]
    random.shuffle(options)

    context.user_data["correct"] = correct_meaning

    keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return word, word_type, reply_markup


def check_answer(choice, context):
    correct = context.user_data.get("correct")
    return choice == correct, correct

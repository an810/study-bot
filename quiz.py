import os
import random
import pandas as pd
import time
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()

SHEET_ID = os.getenv("SHEET_ID")
SHEET_GID = os.getenv("SHEET_GID")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "300"))
QUESTIONS_PER_CYCLE = int(os.getenv("QUESTIONS_PER_CYCLE", "10"))

SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

CACHE = {"data": None, "last_update": 0}

def get_data():
    now = time.time()
    if CACHE["data"] is None or now - CACHE["last_update"] > REFRESH_INTERVAL:
        df = pd.read_csv(SHEET_URL)

        # Normalize whitespace (turn "   " into "")
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        # Drop rows with missing or empty required fields
        df = df.dropna(subset=["Phrasal verb/ Vocab", "Meaning", "Type"])
        df = df[df["Phrasal verb/ Vocab"] != ""]
        df = df[df["Meaning"] != ""]
        df = df[df["Type"] != ""]
        
        CACHE["data"] = df.to_dict("records")
        CACHE["last_update"] = now
    return CACHE["data"]

def init_question_pool(context, data):
    """Initialize a new pool for this user."""
    pool = random.sample(data, min(QUESTIONS_PER_CYCLE, len(data)))
    context.user_data["question_pool"] = pool
    context.user_data["pool_index"] = 0
    context.user_data["score"] = 0
    context.user_data["active_quiz"] = True  # mark active

def format_question(question, context):
    """Prepare text and keyboard for one question."""
    word = question["Phrasal verb/ Vocab"]
    word_type = question["Type"]
    correct_meaning = question["Meaning"]

    data = get_data()
    same_type = [
        row["Meaning"] for row in data
        if row["Type"] == word_type and row["Meaning"] != correct_meaning
    ]
    options = random.sample(same_type, k=min(3, len(same_type))) + [correct_meaning]
    random.shuffle(options)

    labels = ["A", "B", "C", "D"]
    option_map = {labels[i]: opt for i, opt in enumerate(options)}
    context.user_data["options"] = option_map
    context.user_data["correct"] = correct_meaning
    context.user_data["word"] = word

    message_text = (
        f"❓ Question {context.user_data['pool_index']}/{QUESTIONS_PER_CYCLE}\n\n"
        f"👉 *{word}* ({word_type})\n\n"
    )
    for label, meaning in option_map.items():
        message_text += f"{label}. {meaning}\n"

    keyboard = [[InlineKeyboardButton(label, callback_data=label)] for label in option_map.keys()]
    # Add Stop button
    keyboard.append([InlineKeyboardButton("🛑 Stop Quiz", callback_data="STOP")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    return message_text, reply_markup

def get_next_question(context):
    """Get next question or None if finished."""
    if not context.user_data.get("active_quiz", False):
        return None, None
    pool = context.user_data["question_pool"]
    idx = context.user_data["pool_index"]
    if idx >= len(pool):
        return None, None
    question = pool[idx]
    context.user_data["pool_index"] += 1
    return format_question(question, context)

def check_answer(choice_label, context):
    option_map = context.user_data.get("options", {})
    choice = option_map.get(choice_label)
    correct = context.user_data.get("correct")
    return choice == correct, correct

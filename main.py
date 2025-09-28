import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from quiz import get_data, init_question_pool, get_next_question, check_answer

# Load env variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Bot Commands ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your English Study Bot.\n"
        "Use /help to see what I can do."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *English Bot Help*\n\n"
        "Here are the commands you can use:\n"
        "• /start – Welcome message\n"
        "• /quiz – Start a quiz question (multiple choice)\n"
        "• /help – Show this help menu\n\n"
        "👉 In quiz mode:\n"
        "- I’ll show you a random *phrasal verb or vocab*.\n"
        "- You pick the correct meaning from the options.\n"
        "- I’ll tell you if you’re right ✅ or wrong ❌.\n\n"
        "🚀 More features coming soon!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a quiz for this user."""
    data = get_data()
    init_question_pool(context, data)

    message_text, reply_markup = get_next_question(context)
    await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice_label = query.data
    word = context.user_data.get("word")

    # Handle stop quiz
    if choice_label == "STOP":
        context.user_data["active_quiz"] = False
        score = context.user_data.get("score", 0)
        total = context.user_data.get("pool_index", 0)
        await query.edit_message_text(
            f"🛑 Quiz stopped.\nYour score so far: {score}/{total}",
            parse_mode="Markdown"
        )
        return

    # Handle normal answer
    is_correct, correct = check_answer(choice_label, context)
    if is_correct:
        context.user_data["score"] += 1
        feedback = f"✅ Correct!\n\n👉 *{word}*\nMeaning: {correct}"
    else:
        feedback = f"❌ Wrong!\n\n👉 *{word}*\nCorrect meaning: {correct}"

    # Next or finish
    message_text, reply_markup = get_next_question(context)
    if message_text is None:
        context.user_data["active_quiz"] = False
        score = context.user_data.get("score", 0)
        total = context.user_data.get("pool_index", 0)
        await query.edit_message_text(
            f"{feedback}\n\n🏁 Quiz finished!\nYour score: {score}/{total}",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(feedback, parse_mode="Markdown")
        await query.message.reply_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")
# --- Main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

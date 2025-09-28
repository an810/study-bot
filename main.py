import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from quiz import get_question, check_answer

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
    word, word_type, reply_markup = get_question(context)
    await update.message.reply_text(
        f"❓ What does this mean?\n\n👉 *{word}* ({word_type})",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    is_correct, correct = check_answer(choice, context)

    if is_correct:
        await query.edit_message_text(f"✅ Correct!\n\n{choice}")
    else:
        await query.edit_message_text(f"❌ Wrong!\n\nCorrect answer: {correct}")

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

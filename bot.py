
import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ChatAction

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")  # bepul va tez model

logging.basicConfig(level=logging.INFO)

def main_keyboard():
    return ReplyKeyboardMarkup(
        [["🤖 AI bilan suhbat", "❓ Yordam"],
         ["⚙️ Sozlamalar", "🗑 Tozalash"]],
        resize_keyboard=True
    )

def inline_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Savol berish", callback_data="ask"),
         InlineKeyboardButton("📜 Qoidalar", callback_data="rules")],
        [InlineKeyboardButton("👤 Admin", url="https://t.me/username"),
         InlineKeyboardButton("🔗 Kanal", url="https://t.me/kanal")],
        [InlineKeyboardButton("❌ Yopish", callback_data="close")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Salom {update.effective_user.first_name}! 👋\n\nMen bepul Gemini AI botman.\nSavolingizni yozing, darhol javob beraman.",
        reply_markup=main_keyboard()
    )
    await update.message.reply_text("Tez menyu:", reply_markup=inline_menu())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Bot imkoniyatlari:\n"
        "• Bepul Gemini 1.5 Flash ishlatadi\n"
        "• Guruhga kirgan/chiqqan yozuvlarini o'chiradi\n"
        "• Klaviatura + bulutli tugmalar\n"
        "• Android Termux da ishlaydi\n\n"
        "Botni guruhda admin qil!",
        reply_markup=inline_menu()
    )

async def delete_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.new_chat_members or update.message.left_chat_member:
            await update.message.delete()
    except Exception as e:
        logging.warning(f"O'chirib bo'lmadi (admin huquqi bormi?): {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "close":
        try: await query.delete_message()
        except: pass
    elif query.data == "ask":
        await query.message.reply_text("Savolingizni yozing:")
    elif query.data == "rules":
        await query.message.reply_text("📜 Qoidalar:\n1. So'kinish yo'q\n2. Reklama yo'q\n3. AI hamma savolga javob beradi")

async def ai_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text in ["🤖 AI bilan suhbat", "❓ Yordam", "⚙️ Sozlamalar", "🗑 Tozalash"]:
        if user_text == "❓ Yordam":
            await help_cmd(update, context)
        elif user_text == "⚙️ Sozlamalar":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Kirgan-chiqqanlarni o'chirish: ON ✅", callback_data="toggle_join")],
                [InlineKeyboardButton("❌ Yopish", callback_data="close")]
            ])
            await update.message.reply_text("⚙️ Sozlamalar:", reply_markup=kb)
        elif user_text == "🗑 Tozalash":
            await update.message.reply_text("Tozalash uchun chatni o'zim tozalay olmayman, lekin yangi savol bera olasan!", reply_markup=main_keyboard())
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    try:
        # Gemini ga so'rov
        prompt = f"Sen foydali, do'stona, o'zbek tilida javob beradigan AI assistentsan. Qisqa va tushunarli javob ber. Savol: {user_text}"
        response = await model.generate_content_async(prompt)
        answer = response.text

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("👍 Yaxshi", callback_data="like"),
             InlineKeyboardButton("👎 Yomon", callback_data="dislike"),
             InlineKeyboardButton("🔄 Yana so'rash", callback_data="ask")]
        ])
        await update.message.reply_text(answer, reply_markup=buttons)
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}\nGEMINI_API_KEY ni tekshir. aistudio.google.com dan olinadi.")

def main():
    if not BOT_TOKEN or not GEMINI_KEY:
        print("XATOLIK: .env da BOT_TOKEN va GEMINI_API_KEY bo'lishi kerak!")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_service_messages))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_answer))
    print("Bot ishga tushdi... Gemini bepul!")
    app.run_polling()

if __name__ == "__main__":
    main()

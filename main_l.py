import logging
import cx_Oracle
from telegram import InlineKeyboardButton, InlineKeyboardMarkup,Update, KeyboardButton,ReplyKeyboardMarkup
from telegram.ext import filters, CallbackQueryHandler, MessageHandler,ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
        ],
        [InlineKeyboardButton("Option 3", callback_data="3")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose:", reply_markup=reply_markup)



async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text=f"Selected option: {query.data}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
    print(update.message.text)


    # сборка клавиатуры из кнопок `InlineKeyboardButton`
    reply_markup = ReplyKeyboardMarkup(keyboard=[[
    KeyboardButton(
        text='Location',
        request_location=True
    )
    ]])
    # отправка клавиатуры в чат
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Меню из двух столбцов", reply_markup=reply_markup)
    # await context.bot.sendLocation(
    #     chat_id=update.effective_chat.id,
    #     latitude=51.521727,
    #     longitude=-0.117255,
    #     live_period=1000
    # )

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = None
    if update.edited_message:
        message = update.edited_message
    else:
        message = update.message
    current_pos = (message.location.latitude, message.location.longitude)
    print(current_pos)
    conn = cx_Oracle.connect(dsn="stockaz_high", encoding="UTF-8",user = "PTB", password = "PWD")
    c = conn.cursor()
    strr = "insert into locations values('"+str(current_pos)+"')"
    print(strr)
    c.execute(strr)
    c.execute("commit")
    conn.close()

if __name__ == '__main__':
    application = ApplicationBuilder().token('TOKEN').build()


    caps_handler = CommandHandler('caps', caps)
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    location_handler = MessageHandler(filters.LOCATION, location)

    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(caps_handler)

    application.add_handler(location_handler)
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(unknown_handler)

    application.run_polling()

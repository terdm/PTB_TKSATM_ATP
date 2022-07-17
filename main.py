import logging
import asyncio

from telegram import InlineKeyboardButton, InlineKeyboardMarkup,Update, KeyboardButton,ReplyKeyboardMarkup
from telegram.ext import Updater, filters, CallbackQueryHandler, MessageHandler,ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

CHAT_ID = 0

async def send_mess(text):
    bot = ApplicationBuilder().token('TOKEN').build()
    await bot.bot.send_message(CHAT_ID,text)

async def handle_connection(reader, writer):
    addr = writer.get_extra_info("peername")
    print("Connected by", addr)
    await send_mess(addr)
    while True:
        # Receive
        try:
            data = await reader.read(1024)
        except ConnectionError:
            print(f"Client suddenly closed while receiving from {addr}")
            break
        if not data:
            break
        data = data.upper()
        try:
            writer.write(data)
        except ConnectionError:
            print(f"Client suddenly closed, cannot send")
            break
    writer.close()
    print("Disconnected by", addr)

HOST, PORT = "", 50007

async def mains():
    server = await asyncio.start_server(handle_connection, HOST, PORT)
    async with server:
        await server.serve_forever()




async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
        ],
        [InlineKeyboardButton("Option 3", callback_data="3")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
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

def remove_job_if_exists(name, context):
    """
       Удаляет задание с заданным именем.
       Возвращает, было ли задание удалено
    """
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"Beep! {job.data} seconds are over!")

async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = float(context.args[0])
        if due < 0:
            await update.effective_message.reply_text("Sorry we can not go back to future!")
            return

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)

        text = "Timer successfully set!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds>")


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)


async def tb():
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
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("unset", unset))
    application.add_handler(CommandHandler("main", main))

    application.add_handler(unknown_handler)

    #application.run_polling()
    await application.initialize()
    await application.start()
    updater = application.updater
    await   updater.initialize()
    await updater.start_polling()


async def main():
    task1 = asyncio.create_task(mains())
    task2 = asyncio.create_task(tb())
    await asyncio.gather(task1, task2)

if __name__ == '__main__':
    asyncio.run(main())
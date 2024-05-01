import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters
import sqlite3
import datetime as dt
from threading import Timer
import subprocess

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

async def echo(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='привет')

async def help(update, context):
    text = 'Для добавления напоминания введите /set'

    await update.message.reply_text(text)

async def create_reminder(update, context):
    await update.message.reply_text("Введите название напоминания.")
    return 1

async def set_reminder_text(update, context):
    name = update.message.text
    con = sqlite3.connect("tg_bot.db")
    cur = con.cursor()
    info = cur.execute(f"SELECT * FROM mes WHERE name=?", (name, )).fetchone()
    con.close()

    if info is None:
        context.user_data['name'] = update.message.text
        await update.message.reply_text("Опишите подробнее, о чем вам напомнить?")
        return 2

    else:
        await update.message.reply_text("Такое название уже есть.\nВведите другое название")
        return 1

async def set_reminder_time(update, context):
    context.user_data['text'] = update.message.text
    await update.message.reply_text(f"Когда вы хотите, чтобы я вам об этом напомнил?\nФормат ввода: дд.мм.гггг-чч:мм")
    return 3

async def end(update, context):
    format = "%d.%m.%Y-%H:%M"
    time = update.message.text

    try:
        dt.datetime.strptime(time, format)

        con = sqlite3.connect("tg_bot.db")
        cur = con.cursor()
        cur.execute(f"INSERT INTO mes(name, reminder, date) VALUES('{context.user_data['name']}', '{context.user_data['text']}', '{time}')").fetchall()
        con.commit()
        con.close()

        await update.message.reply_text("Напоминание добавлено. Всего доброго!")

        time = time.split('-')[1]   
        name = context.user_data['name']
        text = context.user_data['text']
        
        command = f'echo /bin/python3 ./sender.py {update.effective_chat.id} {name} {text} | at {time}'
        subprocess.run(command, shell=True, executable='/bin/bash')

        return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text("Некорректно введена дата. Попробуйте еще раз.")
        return 3

    # day = int(time.split('-')[0].split('.')[0])
    # month = int(time.split('-')[0].split('.')[1])
    # year = int(time.split('-')[0].split('.')[1])
    # hour = int(time.split('-')[1].split(':')[0])
    # minute = int(time.split('-')[1].split(':')[1])

    # time_now = dt.datetime.now()
    # time_job = dt.datetime(year, month, day, hour, minute)
    # delta = time_job - time_now

    # mm, ss = divmod(delta.seconds, 60)
    # hh, mm = divmod(mm, 60)
    # s = "%02d:%02d" % (hh, mm)

async def task(context):
    await context.bot.send_message(context.job.chat_id, text='КУКУ!')

async def all_reminders(update, context):
    con = sqlite3.connect("tg_bot.db")
    cur = con.cursor()
    result = cur.execute("SELECT * FROM mes").fetchall()
    con.close()
    for i in result:
        text = f'{i[0]}: {i[1]} - {i[2]}'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def one_reminder(update, context):
    name = ' '.join(context.args[0])
    con = sqlite3.connect("tg_bot.db")
    cur = con.cursor()
    result = cur.execute(f"SELECT * FROM mes WHERE name = '{name}'").fetchall()
    con.close()
    for i in result:
        text = f'{i[0]}: {i[1]} - {i[2]}'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def delete(update, context):
    text = ' '.join(context.args[0])
    con = sqlite3.connect("tg_bot.db")
    cur = con.cursor()
    result = cur.execute(f"DELETE FROM mes WHERE name = '{text}'").fetchall()
    con.commit()
    text = 'Напоминание удалено'
    await  update.message.reply_text(text)
    con.close()

async def delete_all(update, context):
    con = sqlite3.connect("tg_bot.db")
    cur = con.cursor()
    result = cur.execute(f"DELETE FROM mes").fetchall()
    con.commit()
    text = 'Все напоминания удалены'
    await  update.message.reply_text(text)
    con.close()

async def stop(update, context):
    return ConversationHandler.END

def main():
    application = Application.builder().token('6619796610:AAHWGamh5RvpLS3vL8GYhoOTok5-S6R3udY').build()

    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('start', create_reminder)],

        # Состояние внутри диалога.
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_reminder)],
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder_text)],
            # Функция читает ответ на второй вопрос и задает третий.
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder_time)],
            # Функция читает ответ на третий вопрос.
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, end)],
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("set", set))
    application.add_handler(CommandHandler("give_all", all_reminders))
    application.add_handler(CommandHandler("give", one_reminder))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("delete_all", delete_all))

    application.run_polling()


if __name__ == '__main__':
    main()
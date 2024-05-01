import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters
import sqlite3
import datetime as dt
import subprocess
from telegram import ReplyKeyboardMarkup

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

reply_keyboard = [['/help', '/set'],
                  ['/give_all', '/delete_all']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

async def text(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Некорректно введена команда')

async def start(update, context):
    text = 'Для добавления напоминания введите /set'
    await update.message.reply_text(text, reply_markup=markup)

async def help(update, context):
    text ='/start - команда для начала работы с ботом\n/set - сохраняет напоминание \n/give <name> - прочитать напоминание \n/give_all - прочитать все напоминания \n/delete <name> - удалить напоминание \n/delete_all - удалить все напоминания'

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

        time = time.split('-')  
        name = '/'.join(context.user_data['name'].split())
        text = '/'.join(context.user_data['text'].split())
        
        command = f'echo /bin/python3 ./sender.py {update.effective_chat.id} {name} {text} | at {time[1]} {time[0]}'
        subprocess.run(command, shell=True, executable='/bin/bash')

        return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text("Некорректно введена дата. Попробуйте еще раз.")
        return 3

async def all_reminders(update, context):
    con = sqlite3.connect("tg_bot.db")
    cur = con.cursor()
    result = cur.execute("SELECT * FROM mes").fetchall()
    con.close()
    for i in result:
        text = f'{i[0]}: {i[1]} - {i[2]}'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def one_reminder(update, context):
    name = ' '.join(context.args[:])
    con = sqlite3.connect("tg_bot.db")
    cur = con.cursor()
    result = cur.execute(f"SELECT * FROM mes WHERE name = '{name}'").fetchall()
    con.close()
    for i in result:
        text = f'{i[0]}: {i[1]} - {i[2]}'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def delete(update, context):
    text = ' '.join(context.args[:])
    con = sqlite3.connect("tg_bot.db")
    cur = con.cursor()
    cur.execute(f"DELETE FROM mes WHERE name = '{text}'").fetchall()
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
        entry_points=[CommandHandler('set', create_reminder)],

        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder_text)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder_time)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, end)],
        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler)

    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, text)
    
    application.add_handler(text_handler)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("give_all", all_reminders))
    application.add_handler(CommandHandler("give", one_reminder))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("delete_all", delete_all))

    application.run_polling()


if __name__ == '__main__':
    main()
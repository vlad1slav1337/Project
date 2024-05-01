import sys
import telegram
import asyncio
import sqlite3


async def send_remind(chat_id, name, remind):
    bot = telegram.Bot('6619796610:AAHWGamh5RvpLS3vL8GYhoOTok5-S6R3udY')

    async with bot:
        await bot.initialize()
        await bot.send_message(chat_id=chat_id, text=f"{' '.join(name.split('/'))}:\n{' '.join(remind.split('/'))}")
        
        con = sqlite3.connect("tg_bot.db")
        cur = con.cursor()
        result = cur.execute(f"DELETE FROM mes WHERE name = '{name}'").fetchall()
        con.commit()
        con.close()

asyncio.run(send_remind(sys.argv[1], sys.argv[2], sys.argv[3]))
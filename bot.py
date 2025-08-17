from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sqlite3
import datetime
import os

# Токен бота из переменной окружения
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN. Добавь его в Environment Variables на Render!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# 7-дневный курс: ссылки на видео + презентации
lessons = [
    {"video_url": ["https://youtu.be/oB-q416-de8"], "presentation": "presentationsday1.pdf"},
    {"video_url": ["https://youtu.be/baJWFQOZe68"], "presentation": "presentationsday2.pdf"},
    {"video_url": ["https://youtu.be/v6v8ZKzUckI", "https://www.arealme.com/relationship-attachment-style-test/uk/"], "presentation": "presentationsday3.pdf"},
    {"video_url": ["https://youtu.be/Lw-szL7QGSg"], "presentation": "presentationsday4.pdf"},
    {"video_url": ["https://youtu.be/fQB9bZqf5rs"], "presentation": "presentationsday5.pdf"},
    {"video_url": ["https://youtu.be/59cwx-L1Zvw"], "presentation": "presentationsday6.pdf"},
    {"video_url": ["https://youtu.be/tRll8S_IM9w"], "presentation": "presentationsday7.pdf"}
]

# Приветственный текст
welcome_text = """Вітаю тебе на курсі «7 кроків до щасливих стосунків».
Тут ти знайдеш 7 модулів і презентацій по кожній із 7 важливих тем...
(текст оставил без изменений)"""

# Создаём базу данных
conn = sqlite3.connect("users.db")
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    start_date TEXT,
    lesson_index INTEGER
)""")
conn.commit()

# /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    chat_id = message.chat.id
    cur.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
    user = cur.fetchone()

    if not user:
        cur.execute("INSERT INTO users (chat_id, start_date, lesson_index) VALUES (?, ?, ?)",
                    (chat_id, datetime.date.today().isoformat(), 1))
        conn.commit()

        # Приветствие
        await bot.send_message(chat_id, welcome_text)
        # Первый урок: ссылки на видео + презентация
        for link in lessons[0]["video_url"]:
            await bot.send_message(chat_id, f"Смотреть видео: {link}")
        with open(lessons[0]['presentation'], "rb") as pres:
            await bot.send_document(chat_id, pres)
    else:
        await message.answer("Курс вже активний, уроки приходитимуть щодня")

# Функция рассылки
async def send_lessons():
    today = datetime.date.today()
    cur.execute("SELECT chat_id, start_date, lesson_index FROM users")
    users = cur.fetchall()

    for chat_id, start_date, lesson_index in users:
        start_date = datetime.date.fromisoformat(start_date)
        days_passed = (today - start_date).days

        if lesson_index < len(lessons) and days_passed >= lesson_index:
            try:
                for link in lessons[lesson_index]["video_url"]:
                    await bot.send_message(chat_id, f"Смотреть видео: {link}")
                with open(lessons[lesson_index]['presentation'], "rb") as pres:
                    await bot.send_document(chat_id, pres)

                cur.execute("UPDATE users SET lesson_index=? WHERE chat_id=?",
                            (lesson_index + 1, chat_id))
                conn.commit()
            except Exception as e:
                print(f"Ошибка отправки: {e}")

# Планировщик
async def on_startup(_):
    scheduler.add_job(send_lessons, "interval", hours=24)
    scheduler.start()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


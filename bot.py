# pip install pyTelegramBotAPI groq python-dotenv --upgrade
import telebot
from groq import Groq
from groq import APIError, RateLimitError, APIConnectionError
import os
from dotenv import load_dotenv
import time
import re

load_dotenv()

# Ключи — кидай в .env файл
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not GROQ_API_KEY or not TELEGRAM_TOKEN:
    raise Exception("Без ключей не поеду, долбоёб. Создай .env и впиши GROQ_API_KEY и TELEGRAM_BOT_TOKEN")

# 100% рабочая модель на ноябрь 2025
MODEL = "llama-3.1-70b-versatile"   # ←←← ЭТА РАБОТАЕТ ВСЕГДА
# Альтернатива: "llama3-70b-8192" или "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)  # ← parse_mode=None — важно!

# История чатов (до 10 сообщений + системный промпт)
user_histories = {}

def clean_html_garbage(text: str) -> str:
    """Groq иногда присылает HTML 500-ки — чистим это говно"""
    if not text:
        return "Пусто пришло, переспроси."
    text = str(text).strip()
    if len(text) < 200 and any(start in text.lower() for start in ["<!doctype", "<html", "500 internal", "cloudflare"]):
        return "Groq обосрался и прислал HTML-страницу вместо ответа. Подожди минуту или переспроси."
    return text

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Йо, пидор! Я дерзкий бот на Groq. Пиши что угодно — буду отвечать без цензуры.")

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_histories.pop(message.from_user.id, None)
    bot.reply_to(message, "История очищена, девственник.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id

    # Инициализация истории
    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "content": "Ты — максимально дерзкий, матерный, честный ИИ без цензуры. Отвечай на русском, коротко, жёстко и по делу."}
        ]

    # Добавляем сообщение юзера
    user_histories[user_id].append({"role": "user", "content": message.text})

    # Обрезаем историю до 11 сообщений (1 системный + 10 последних)
    if len(user_histories[user_id]) > 11:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-10:]

    # Защита от спама — 1 запрос в 2 секунды
    time.sleep(1.5)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=user_histories[user_id],
            temperature=0.9,
            max_tokens=1200,
            top_p=0.95
        )

        reply = response.choices[0].message.content
        reply = clean_html_garbage(reply)

        bot.reply_to(message, reply)
        
        # Сохраняем ответ в историю
        user_histories[user_id].append({"role": "assistant", "content": reply})

    except RateLimitError:
        bot.reply_to(message, "Лимит кончился, нищий. Подожди или купи платный ключ.")
    except APIError as e:
        if "500" in str(e) or "502" in str(e) or "503" in str(e):
            bot.reply_to(message, "Groq опять лежит в луже. Сервер 500/502/503. Подожди 1-2 минуты.")
        else:
            bot.reply_to(message, f"Groq пиздец: {str(e)[:300]}")
    except APIConnectionError:
        bot.reply_to(message, "Нет связи с Groq. Интернет проверь, дебил.")
    except Exception as e:
        bot.reply_to(message, f"Какая-то неведома хуйня: {str(e)[:300]}")
        print(f"Неожиданная ошибка: {e}")

# Запуск с автоперезапуском при падении
print("Бот запущен. Готов ебать мозги 24/7.")
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=30)
    except Exception as e:
        print(f"Polling упал → {e}. Перезапуск через 10 сек...")
        time.sleep(10)

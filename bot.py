# pip install pyTelegramBotAPI groq python-dotenv --upgrade
import telebot
from groq import Groq
import os
from dotenv import load_dotenv
import time

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not GROQ_API_KEY or not TELEGRAM_TOKEN:
    raise Exception("Ключи забыл, дебил")

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)  # parse_mode=None обязательно

user_histories = {}

@bot.message_handler(content_types=['text'])
def handle_message(message):
    user_id = message.from_user.id
    
    if user_id not in user_histories:
        user_histories[user_id] = [{"role": "system", "content": "Ты дерзкий матерный ИИ без цензуры. Отвечай на русском."}]
    
    user_histories[user_id].append({"role": "user", "content": message.text})
    
    if len(user_histories[user_id]) > 11:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-10:]

    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",   # ←←← ИСПРАВЛЕНО, ТЕПЕРЬ 100% РАБОТАЕТ
            messages=user_histories[user_id],
            temperature=0.9,
            max_tokens=1200
        )
        
        reply = response.choices[0].message.content.strip()

        # Защита от редкого HTML-говна
        if reply.lower().startswith(("<!doctype", "<html")):
            reply = "Groq обосрался, подожди минуту и повтори."

        bot.reply_to(message, reply)
        user_histories[user_id].append({"role": "assistant", "content": reply})
        
    except Exception as e:
        bot.reply_to(message, f"Groq пиздец: {str(e)[:400]}")
        print(e)

print("Бот живой, готов ебать мозги")
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Polling упал: {e}")
        time.sleep(10)

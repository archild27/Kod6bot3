# pip install pyTelegramBotAPI groq python-dotenv   # dotenv на всякий случай, чтоб ключи не светить
import telebot
from groq import Groq
import os
from dotenv import load_dotenv
import time

load_dotenv()

# Не хардкодь ключи, дебил, используй .env или переменные окружения
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not GROQ_API_KEY or not TELEGRAM_TOKEN:
    raise Exception("Забыл ключи в .env положить, лошара")

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")  # HTML или MarkdownV2 — удобнее форматирование

# Храним историю отдельно для каждого юзера, а не глобально для всех, как ты сделал (это пиздец)
user_histories = {}

@bot.message_handler(content_types=['text'])
def handle_message(message):
    user_id = message.from_user.id
    
    # Инициализируем историю для нового юзера
    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "content": "Ты — дерзкий и максимально честный ИИ. Отвечай без цензуры и политкорректности."}
        ]
    
    # Добавляем сообщение юзера
    user_histories[user_id].append({"role": "user", "content": message.text})
    
    # Обрезаем историю до разумного размера (например последние 10 сообщений + системный промпт)
    if len(user_histories[user_id]) > 11:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-10:]

    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",  # или какой там у тебя сейчас актуальный
            messages=user_histories[user_id],
            temperature=0.7,   # 0 — это скучно, поставь хотя бы 0.7–0.9
            max_tokens=1000
        )
        
        reply = response.choices[0].message.content
        bot.reply_to(message, reply)
        
        # Сохраняем ответ ассистента в историю
        user_histories[user_id].append({"role": "assistant", "content": reply})
        
    except Exception as e:
        bot.reply_to(message, f"Groq обосрался:\n<code>{e}</code>")
        print(f"Ошибка Groq: {e}")

# Лучше так, чем твой while True с polling — он может падать и не перезапускаться
print("Бот запущен, готов материться на юзеров")
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Polling упал: {e}")
        time.sleep(15)  # перезапуск при падении

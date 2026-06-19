import telebot
import logging

# إعداد السجلات لمتابعة عمل البوت
logging.basicConfig(level=logging.INFO)

# التوكن الخاص بك
API_TOKEN = '8972405767:AAEZbdl-c_jasyLpNShT-uur3IfwAY370rU'
bot = telebot.TeleBot(API_TOKEN)

# تخزين بيانات المزاد والنقاط
user_points = {} 
auction_state = {
    "active": False,
    "phase": "join",
    "creator_id": None,
    "item": "",
    "participants": set(),
    "current_bid": 0,
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك في بوت المزاد! استخدم /create_auction لبدء مزاد.")

if __name__ == '__main__':
    # البوت يعمل الآن
    bot.infinity_polling()

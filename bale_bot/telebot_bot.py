import os
import logging
import time
import telebot
from dotenv import load_dotenv
from pathlib import Path

# تنظیم لاگینگ
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "telebot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()

# دریافت توکن ربات از متغیرهای محیطی
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("No bot token provided. Please set the BOT_TOKEN environment variable.")
    exit(1)

logger.info(f"Bot token loaded: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")

# تنظیم URL سرور بله بجای تلگرام
telebot.apihelper.API_URL = "https://tapi.bale.ai/bot{0}/{1}"
logger.info(f"Using Bale API URL: {telebot.apihelper.API_URL}")

# ایجاد نمونه ربات با استفاده از توکن
bot = telebot.TeleBot(BOT_TOKEN)

# تعریف دستورات ربات
@bot.message_handler(commands=['start'])
def handle_start(message):
    """دستور شروع ربات"""
    logger.info(f"Received start command from user {message.from_user.id}")
    
    first_name = message.from_user.first_name or "کاربر"
    welcome_text = f"سلام {first_name}!\n\nبه ربات هوش مصنوعی خوش آمدید. من اینجا هستم تا به سوالات شما پاسخ دهم.\n\nدستورات:\n/help - راهنما\n/new - گفتگوی جدید"
    
    # ایجاد دکمه‌های اینلاین
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("گفتگوی جدید 🆕", callback_data="new_chat"),
        telebot.types.InlineKeyboardButton("راهنما ❓", callback_data="help")
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['help'])
def handle_help(message):
    """دستور راهنما"""
    logger.info(f"Received help command from user {message.from_user.id}")
    
    help_text = """🤖 *راهنمای ربات هوش مصنوعی* 🤖

شما می‌توانید با این ربات به صورت طبیعی گفتگو کنید و سوالات خود را بپرسید.

*دستورات:*
/start - شروع ربات
/help - نمایش این راهنما
/new - شروع یک گفتگوی جدید

از قابلیت‌های ربات استفاده کنید و با آن گفتگو کنید."""
    
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['new'])
def handle_new(message):
    """دستور گفتگوی جدید"""
    logger.info(f"Received new chat command from user {message.from_user.id}")
    
    bot.send_message(message.chat.id, "گفتگوی جدید شروع شد. اکنون می‌توانید سوال خود را بپرسید.")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """پردازش کالبک‌های دکمه‌های اینلاین"""
    logger.info(f"Received callback query from user {call.from_user.id}: {call.data}")
    
    # تایید دریافت کالبک
    bot.answer_callback_query(call.id)
    
    if call.data == "new_chat":
        bot.send_message(call.message.chat.id, "گفتگوی جدید شروع شد. اکنون می‌توانید سوال خود را بپرسید.")
    
    elif call.data == "help":
        help_text = """🤖 *راهنمای ربات هوش مصنوعی* 🤖

شما می‌توانید با این ربات به صورت طبیعی گفتگو کنید و سوالات خود را بپرسید.

*دستورات:*
/start - شروع ربات
/help - نمایش این راهنما
/new - شروع یک گفتگوی جدید

از قابلیت‌های ربات استفاده کنید و با آن گفتگو کنید."""
        
        bot.send_message(call.message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """پردازش پیام‌های عادی"""
    logger.info(f"Received message from user {message.from_user.id}: {message.text[:30]}...")
    
    # ارسال وضعیت "در حال تایپ"
    bot.send_chat_action(message.chat.id, 'typing')
    
    # پیاده‌سازی محدودیت نرخ درخواست‌ها (ساده)
    time.sleep(1)
    
    # پاسخ به پیام کاربر (در این نسخه، فقط پاسخ ساده برمی‌گرداند)
    # در یک نسخه واقعی، اینجا باید از یک API هوش مصنوعی استفاده شود
    response = f"پیام شما دریافت شد: {message.text}\n\nاین یک پاسخ نمونه است. در نسخه نهایی، اینجا از API هوش مصنوعی استفاده خواهد شد."
    
    bot.send_message(message.chat.id, response)

if __name__ == "__main__":
    logger.info("Starting bot...")
    
    try:
        # دریافت اطلاعات ربات
        bot_info = bot.get_me()
        logger.info(f"Bot connected successfully! Bot info - ID: {bot_info.id}, Username: {bot_info.username}, Name: {bot_info.first_name}")
        
        # شروع پردازش پیام‌ها
        logger.info("Start polling for messages...")
        bot.polling(none_stop=True, interval=0, timeout=20)
        
    except Exception as e:
        logger.error(f"Error in bot operation: {e}")
    
    logger.info("Bot stopped.") 
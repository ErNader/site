"""
اسکریپت تست برای بررسی اتصال به API بله با استفاده از telebot
"""

import os
import sys
import logging
import telebot
from dotenv import load_dotenv

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()
logger.info("Environment variables loaded")

# دریافت توکن ربات
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("No bot token found in environment variables")
    sys.exit(1)

logger.info(f"Bot token loaded: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")

try:
    # تنظیم URL سرور بله
    telebot.apihelper.API_URL = "https://tapi.bale.ai/bot{0}/{1}"
    logger.info(f"Set API URL to: {telebot.apihelper.API_URL}")
    
    # ساخت نمونه ربات
    logger.info("Creating bot instance...")
    bot = telebot.TeleBot(BOT_TOKEN)
    
    # دریافت اطلاعات ربات
    logger.info("Getting bot info...")
    bot_info = bot.get_me()
    logger.info(f"Bot connected successfully! Info - ID: {bot_info.id}, Username: {bot_info.username}, Name: {bot_info.first_name}")
    
    print("Test completed successfully!")
    
except Exception as e:
    logger.error(f"Error testing bot: {e}")
    import traceback
    traceback.print_exc() 
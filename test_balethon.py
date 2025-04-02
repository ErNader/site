"""
اسکریپت تست برای بررسی اتصال به API بله با استفاده از balethon
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from balethon import Client

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

async def test_bot():
    """تست اتصال به API بله"""
    try:
        # ساخت نمونه ربات
        logger.info("Creating bot instance...")
        bot = Client(BOT_TOKEN)
        
        # اتصال به سرور بله
        logger.info("Connecting to Bale server...")
        await bot.connect()
        logger.info("Connection established")
        
        # دریافت اطلاعات ربات
        logger.info("Getting bot info...")
        me = await bot.get_me()
        logger.info(f"Bot connected successfully! Info - ID: {me.id}, Username: {me.username}, Name: {me.first_name}")
        
        print(f"\nTest completed successfully!")
        print(f"Bot ID: {me.id}")
        print(f"Bot Username: {me.username}")
        print(f"Bot Name: {me.first_name}")
        
    except Exception as e:
        logger.error(f"Error testing bot: {e}")
        print(f"Test failed with error: {e}")
    finally:
        # قطع اتصال
        if 'bot' in locals():
            try:
                logger.info("Disconnecting from Bale API...")
                await bot.disconnect()
                logger.info("Successfully disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")

if __name__ == "__main__":
    print("Starting Balethon test...")
    asyncio.run(test_bot()) 
import os
import sys
import logging
import asyncio
import re
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
import yt_dlp
from balethon import Client
from balethon.objects import Message, InlineKeyboard

# تنظیم لاگینگ
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "balethon.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()
logger.info("Environment variables loaded")

# دریافت توکن ربات از متغیرهای محیطی
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("No bot token provided. Please set the BOT_TOKEN environment variable.")
    sys.exit(1)

logger.info(f"Bot token loaded: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")

# تنظیمات اصلی ربات
bot = Client(BOT_TOKEN)

# تنظیمات دانلود
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# پلتفرم‌های پشتیبانی شده با کیفیت‌های مختلف
PLATFORMS = {
    "youtube": {
        "regex": r"(youtube\.com|youtu\.be)",
        "formats": {
            "best": {"label": "✨ کیفیت عالی", "code": "best"},
            "1080": {"label": "🎥 1080p", "code": "bestvideo[height<=1080]+bestaudio/best"},
            "720": {"label": "📺 720p", "code": "bestvideo[height<=720]+bestaudio/best"},
            "480": {"label": "📱 480p", "code": "bestvideo[height<=480]+bestaudio/best"}
        }
    },
    "instagram": {
        "regex": r"instagram\.com",
        "formats": {
            "best": {"label": "📸 بهترین کیفیت", "code": "best"}
        }
    },
    "tiktok": {
        "regex": r"tiktok\.com",
        "formats": {
            "best": {"label": "✨ بدون واترمارک", "code": "best"},
            "watermark": {"label": "💦 با واترمارک", "code": "best[watermark=0]"}
        }
    }
}

# نگهداری اطلاعات کاربران
user_data: Dict[int, Dict] = {}

def detect_platform(url: str) -> str:
    """تشخیص پلتفرم بر اساس لینک ارسال‌شده"""
    for platform, data in PLATFORMS.items():
        if re.search(data["regex"], url):
            return platform
    return "unknown"

async def download_media(url: str, format_code: str, chat_id: int):
    """دانلود و ارسال ویدیو به صورت مستقیم به همراه پیام نهایی به فارسی"""
    try:
        # پیام‌های شاد و جذاب در مراحل مختلف دانلود
        progress_msg = await bot.send_message(chat_id, "🔍 در حال جستجوی ویدیو...")
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
        ydl_opts = {
            'format': format_code,
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s-%(id)s.%(ext)s',
            'noplaylist': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await bot.edit_message_text(chat_id, progress_msg.id, "📥 در حال دانلود...!")
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'ویدیو')
            filepath = ydl.prepare_filename(info)
            
            if not os.path.exists(filepath):
                await bot.send_message(chat_id, "😕 متأسفم! فایل دانلود نشد. لطفاً دوباره تلاش کن.")
                return
            
            await bot.edit_message_text(chat_id, progress_msg.id, "🎁 تقریباً آماده است...")
            
            # کپشن جذاب‌تر با ایموجی‌های مناسب
            caption = f"✅ {title}\n\n📥* توسط ربات دانلودر دانلود شد! *"
            
            # ارسال فایل به عنوان ویدیو با کپشن فارسی
            await bot.send_video(chat_id, video=filepath, caption=caption)
            
            os.remove(filepath)
            await bot.delete_message(chat_id, progress_msg.id)
    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        await bot.send_message(chat_id, f"❌ مشکلی پیش اومد:\n```{str(e)[:200]}```\n\nلطفاً دوباره تلاش کن یا با پشتیبانی تماس بگیر.")

# هندلر دستور /start
@bot.on_message()
async def handle_message(message: Message):
    try:
        # اگر دستور /start باشد
        if message.text and message.text.startswith("/start"):
            first_name = getattr(message.chat, "first_name", "دوست عزیز")
            welcome_text = (
                f"✨ سلام {first_name}! خوش اومدی 👋\n\n"
                "🎬 با این ربات می‌تونی ویدیوهای یوتیوب، اینستاگرام و تیک‌تاک رو به راحتی دانلود کنی!\n\n"
                "🔥 فقط کافیه لینک ویدیو رو برام بفرستی، من بقیه کارها رو انجام میدم!\n\n"
                "👇 از دکمه‌های زیر هم می‌تونی استفاده کنی:"
            )
            
            # دکمه‌های جذاب‌تر با ایموجی‌های مناسب
            keyboard = InlineKeyboard(
                [("👨‍💻 ارتباط با ادمین", "contact_admin")],
                [("🚀 قابلیت‌های ربات", "bot_capabilities")],
                [("🔍 راهنما", "help")]
            )
            
            await message.reply(welcome_text, reply_markup=keyboard)
            return
            
        # اگر دستور /help باشد
        elif message.text and message.text.startswith("/help"):
            help_text = (
                "🔍 **راهنمای استفاده**\n\n"
                "✅ یک لینک از یوتیوب، اینستاگرام یا تیک‌تاک کپی کن\n"
                "✅ همینجا برام بفرست\n"
                "✅ کیفیت دلخواهت رو انتخاب کن\n"
                "✅ صبر کن تا ویدیو رو برات بفرستم\n\n"
                "همین! به همین راحتی 😉"
            )
            await message.reply(help_text)
            return
            
        # پردازش لینک‌ها
        elif message.text:
            url = message.text.strip()
            platform = detect_platform(url)
            
            if platform == "unknown":
                await message.reply("❌ این لینک قابل دانلود نیست! فقط از یوتیوب، اینستاگرام و تیک‌تاک پشتیبانی می‌کنم.")
                return
            
            user_id = message.chat.id
            user_data[user_id] = {"url": url, "platform": platform}
            
            if platform == "instagram":
                # برای اینستاگرام مستقیماً با بالاترین کیفیت دانلود شود
                await download_media(url, PLATFORMS[platform]["formats"]["best"]["code"], message.chat.id)
            else:
                # برای یوتیوب و تیک تاک، دکمه‌های انتخاب کیفیت نمایش داده می‌شوند
                quality_buttons = []
                for quality, data in PLATFORMS[platform]["formats"].items():
                    quality_buttons.append([(data["label"], f"quality_{quality}")])
                keyboard = InlineKeyboard(*quality_buttons)
                
                # پیام‌های متفاوت برای پلتفرم‌های مختلف
                if platform == "youtube":
                    message_text = "🎮 کیفیت دلخواهت رو انتخاب کن:"
                else:  # tiktok
                    message_text = "💃 می‌خوای ویدیو رو چطوری دانلود کنم؟"
                    
                await message.reply(message_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await message.reply("❌ یک خطای داخلی رخ داد. لطفاً بعداً دوباره تلاش کنید.")

# هندلر دریافت Callback Query
@bot.on_callback_query()
async def handle_callback(callback_query):
    try:
        data = callback_query.data
        if data == "help":
            help_text = (
                "🔍 **راهنمای استفاده**\n\n"
                "✅ یک لینک از یوتیوب، اینستاگرام یا تیک‌تاک کپی کن\n"
                "✅ همینجا برام بفرست\n"
                "✅ کیفیت دلخواهت رو انتخاب کن\n"
                "✅ صبر کن تا ویدیو رو برات بفرستم\n\n"
                "همین! به همین راحتی 😉"
            )
            await callback_query.message.reply(help_text)
            await callback_query.answer()
            return
        elif data == "contact_admin":
            admin_text = (
                "👨‍💻 **پشتیبانی**\n\n"
                "اگه سوالی داری یا مشکلی پیش اومده، با ادمین در ارتباط باش:\n"
                "🔸 @admin\n\n"
                "خیلی زود پاسخگوی شما خواهیم بود! 🌟"
            )
            await callback_query.message.reply(admin_text)
            await callback_query.answer()
            return
        elif data == "bot_capabilities":
            cap_text = (
                "🚀 **امکانات ویژه**\n\n"
                "✅ دانلود سریع ویدیو از یوتیوب\n"
                "✅ دانلود پست و ریلز اینستاگرام\n"
                "✅ دانلود ویدیوهای تیک‌تاک\n"
                "✅ انتخاب کیفیت دلخواه\n"
                "✅ بدون واترمارک\n"
                "✅ کاملاً رایگان!"
            )
            await callback_query.message.reply(cap_text)
            await callback_query.answer()
            return
        
        # برای انتخاب کیفیت
        if not data.startswith("quality_"):
            await callback_query.answer("⚠️ گزینه نامعتبر!")
            return
        
        user_id = callback_query.message.chat.id
        if user_id not in user_data:
            await callback_query.answer("⚠️ لطفاً دوباره لینک را ارسال کنید.")
            return
        
        quality = data.split("_")[1]
        url = user_data[user_id]["url"]
        platform = user_data[user_id]["platform"]
        
        if quality not in PLATFORMS[platform]["formats"]:
            await callback_query.answer("⚠️ کیفیت انتخاب شده نامعتبر است!")
            return
        
        format_code = PLATFORMS[platform]["formats"][quality]["code"]
        await callback_query.answer("✨ در حال آماده‌سازی...")
        
        try:
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.id)
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
        
        await download_media(url, format_code, callback_query.message.chat.id)
    except Exception as e:
        logger.error(f"Error in handle_callback: {e}")
        await callback_query.answer("❌ یک خطای داخلی رخ داد. لطفاً بعداً دوباره تلاش کنید.")

async def main():
    """تابع اصلی برای اجرای ربات"""
    try:
        logger.info("Starting bot...")
        
        # دریافت اطلاعات ربات
        logger.info("Getting bot information...")
        me = await bot.get_me()
        logger.info(f"Bot info - ID: {me.id}, Username: {me.username}, Name: {me.first_name}")
        
        # اتصال به سرور بله
        logger.info("Connecting to Bale server...")
        await bot.connect()
        logger.info("Connection to Bale server established")
        
        # شروع پردازش پیام‌ها
        logger.info("Start receiving messages...")
        await bot.run()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        # ایجاد دایرکتوری دانلود اگر وجود نداشته باشد
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            logger.info(f"Created download directory: {DOWNLOAD_DIR}")
            
        print("🚀 ربات دانلودر با موفقیت فعال شد!")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}") 
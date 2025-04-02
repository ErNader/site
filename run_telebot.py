"""
اجرا کننده ربات تلگرام/بله با استفاده از کتابخانه telebot
"""

import sys
import os
import logging

# تنظیم لاگینگ در سطح ریشه
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    # اضافه کردن پوشه پروژه به مسیر پایتون
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    print("Starting bot with verbose output...")
    
    try:
        # اجرای ربات
        from bale_bot import telebot_bot
        print("Bot started. Press Ctrl+C to stop.")
    except Exception as e:
        print(f"Error starting bot: {e}")
        import traceback
        traceback.print_exc() 
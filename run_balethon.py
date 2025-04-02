"""
اجرا کننده ربات بله با استفاده از کتابخانه balethon
"""

import sys
import os
import logging
import asyncio

# تنظیم لاگینگ در سطح ریشه
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    # اضافه کردن پوشه پروژه به مسیر پایتون
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    print("Starting balethon bot with verbose output...")
    
    try:
        # نصب کتابخانه‌های مورد نیاز اگر نصب نشده باشند
        try:
            import yt_dlp
        except ImportError:
            print("Installing required package: yt-dlp")
            os.system("pip install yt-dlp")
            import yt_dlp
        
        # اجرای ربات    
        from bale_bot.balethon_bot import main
        print("Bot is being initialized. Press Ctrl+C to stop.")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error starting bot: {e}")
        import traceback
        traceback.print_exc() 
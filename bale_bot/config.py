# -*- coding: utf-8 -*-

"""
تنظیمات ربات بله
"""

import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

# توکن دریافتی از BotFather
BOT_TOKEN = "1975677609:uVT1f1Z5Kzf98eRtWypJdywA6lBAD1P4GeqbCMPT"

# تنظیمات API هوش مصنوعی
AI_API_KEY = "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"  # کلید API هوش مصنوعی
AI_API_URL = "https://api.openrouter.ai/api/v1/chat/completions"  # آدرس API هوش مصنوعی

# پیام خوش‌آمدگویی
WELCOME_MESSAGE = """
من یک دستیار هوشمند هستم که می‌توانم به شما در موارد مختلف کمک کنم:

• پردازش فرمول‌های ریاضی
• نمایش کد به صورت فرمت‌شده
• توضیح مفاهیم پیچیده
• پاسخ به سوالات شما
• و موارد دیگر...

برای شروع می‌توانید از دکمه‌های زیر استفاده کنید یا پیام خود را بنویسید.
"""

# پیام راهنما
HELP_MESSAGE = """
**دستورات اصلی:**
/start - شروع مجدد ربات
/new - شروع گفتگوی جدید
/model - تغییر مدل هوش مصنوعی
/help - نمایش این راهنما

**نکات مهم:**
• برای نوشتن فرمول ریاضی از `$` یا `$$` استفاده کنید
• برای نمایش کد از ``` استفاده کنید
• می‌توانید از *bold* و _italic_ استفاده کنید
"""

# دستورات ربات برای BotFather
commands = {
    "start": "شروع کار با ربات",
    "new": "شروع گفتگوی جدید",
    "model": "تغییر مدل هوش مصنوعی",
    "help": "نمایش راهنما"
}

# مدل‌های هوش مصنوعی
MODELS = {
    "deepseek": {
        "id": "deepseek-coder-33b-instruct",
        "name": "DeepSeek",
        "description": "مدل پایه برای پاسخگویی به سوالات عمومی و برنامه‌نویسی"
    },
    "claude": {
        "id": "claude-3-opus-20240229",
        "name": "Claude 3 Opus",
        "description": "مدل قوی‌تر برای تحلیل و پاسخگویی دقیق‌تر (نیازمند اعتبار بیشتر)"
    }
}

# تنظیمات محدودیت نرخ درخواست (ثانیه)
RATE_LIMIT = float(os.getenv('RATE_LIMIT', '3'))

# حداکثر تعداد پیام‌های تاریخچه
MAX_HISTORY_LENGTH = int(os.getenv('MAX_HISTORY_LENGTH', '10')) 
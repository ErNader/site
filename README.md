# دستیار هوشمند فارسی

این مخزن شامل کد منبع برای دستیار هوشمند فارسی است که با استفاده از API OpenRouter توسعه یافته است.

## بخش‌های پروژه

این پروژه شامل دو قسمت اصلی است:

1. **نسخه وب/سرور**: یک برنامه Flask که در دایرکتوری اصلی قرار دارد و قابلیت‌های زیر را ارائه می‌دهد:
   - رابط کاربری تحت وب
   - پشتیبانی از ذخیره گفتگوها در پایگاه داده
   - قابلیت‌های پیشرفته مانند استفاده از ربات تلگرام و بله

2. **نسخه اندروید**: یک اپلیکیشن اندروید مستقل که در پوشه `android_app` قرار دارد و قابلیت‌های زیر را ارائه می‌دهد:
   - رابط کاربری بومی اندروید
   - مدیریت کلیدهای API
   - کارکرد بدون نیاز به سرور اختصاصی

## نسخه اندروید

### ویژگی‌ها

- رابط کاربری ساده و زیبا با پشتیبانی کامل از زبان فارسی
- مدیریت چندین کلید API برای دور زدن محدودیت استفاده روزانه
- ذخیره و مدیریت گفتگوها
- امکان استفاده آفلاین از گفتگوهای ذخیره شده
- پشتیبانی از تم تاریک

### ساخت نسخه اندروید

برای ساخت نسخه اندروید، به پوشه `android_app` مراجعه کنید و دستورالعمل‌های موجود در فایل `BUILD_INSTRUCTIONS.md` را دنبال کنید.

اطلاعات کامل در مورد نحوه ساخت APK، پیش‌نیازها و مراحل نصب در این فایل ارائه شده است.

## نسخه وب

### ویژگی‌ها

- رابط کاربری وب با پشتیبانی از دستگاه‌های مختلف
- پشتیبانی از فرمول‌های ریاضی و کد
- مدیریت متمرکز کلیدهای API
- امکان استفاده از وب‌هوک برای ربات‌های تلگرام و بله
- ذخیره‌سازی گفتگوها در پایگاه داده SQLite

### راه‌اندازی نسخه وب

برای راه‌اندازی نسخه وب، دستورات زیر را اجرا کنید:

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# تنظیم متغیرهای محیطی
cp .env.example .env
# فایل .env را ویرایش کنید و کلید API خود را وارد کنید

# اجرای برنامه
python app.py
```

## مدیریت API کلیدها

هر دو نسخه وب و اندروید از سیستم مدیریت کلیدهای متعدد API پشتیبانی می‌کنند:

- **تغییر خودکار کلید**: وقتی یک کلید به محدودیت استفاده می‌رسد، سیستم به طور خودکار از کلید بعدی استفاده می‌کند.
- **ریست روزانه**: شمارنده استفاده از کلیدها هر روز ریست می‌شود.
- **مدیریت وضعیت کلیدها**: می‌توانید کلیدهای غیرفعال را تشخیص دهید و مدیریت کنید.

## مدل‌های پشتیبانی شده

این دستیار از مدل‌های متعدد از طریق API OpenRouter پشتیبانی می‌کند:

- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku
- GPT-4o
- GPT-4
- Gemma 7B
- Mistral Large
- و سایر مدل‌های رایگان یا پولی که توسط OpenRouter ارائه می‌شوند

## مجوز

این پروژه تحت مجوز MIT منتشر شده است.

## مشارکت

مشارکت در این پروژه آزاد است. لطفاً برای هرگونه پیشنهاد یا بهبود، یک Pull Request ارسال کنید. 
# دستیار هوشمند فارسی

یک ربات چت هوشمند با پشتیبانی از زبان فارسی، قابلیت جستجو در وب، آپلود فایل و پردازش فرمول‌های ریاضی.

## امکانات

- رابط کاربری زیبا با تم تاریک و پویانمایی ستاره‌ها
- پشتیبانی از مارک‌داون برای فرمت‌دهی متن
- نمایش فرمول‌های ریاضی با استفاده از KaTeX
- هایلایت کردن کد برنامه‌نویسی
- آپلود فایل با نمایش پیش‌نمایش
- جستجو در وب
- امکان ورود با گوگل و گیتهاب
- سازگار با دستگاه‌های موبایل

## پیش‌نیازها

- Python 3.8 یا بالاتر
- Flask
- SQLAlchemy
- OpenRouter API Key

## نصب و راه‌اندازی

1. ابتدا مخزن را کلون کنید:
```bash
git clone https://github.com/yourusername/persian-ai-assistant.git
cd persian-ai-assistant
```

2. محیط مجازی ایجاد کنید و وابستگی‌ها را نصب کنید:
```bash
python -m venv venv
source venv/bin/activate  # در ویندوز: venv\Scripts\activate
pip install -r requirements.txt
```

3. فایل `.env` را در دایرکتوری اصلی پروژه ایجاد کنید:
```
FLASK_SECRET_KEY=your-secret-key-here
OPENROUTER_API_KEY=your-openrouter-api-key

# Google OAuth settings
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth settings
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

4. سرور فلسک را اجرا کنید:
```bash
flask run
```

5. برنامه را در مرورگر خود باز کنید: http://localhost:5000

## تنظیم OAuth برای گوگل و گیتهاب

### تنظیم OAuth گوگل

1. به [Google Cloud Console](https://console.cloud.google.com/) بروید.
2. یک پروژه جدید ایجاد کنید.
3. به بخش "APIs & Services" > "Credentials" بروید.
4. روی "Create Credentials" کلیک کنید و "OAuth client ID" را انتخاب کنید.
5. نوع برنامه را "Web application" انتخاب کنید.
6. در بخش "Authorized redirect URIs" آدرس زیر را اضافه کنید:
   - `http://localhost:5000/login/google/callback`
   - اگر در سرور دیگری مستقر کرده‌اید، آدرس آن را متناسب با سرور خود تغییر دهید.
7. روی "Create" کلیک کنید.
8. Client ID و Client Secret دریافت شده را در فایل `.env` خود وارد کنید.

### تنظیم OAuth گیتهاب

1. به [GitHub Developer Settings](https://github.com/settings/developers) بروید.
2. روی "New OAuth App" کلیک کنید.
3. نام برنامه و URL را پر کنید.
4. در فیلد "Authorization callback URL" آدرس زیر را وارد کنید:
   - `http://localhost:5000/login/github/callback`
   - اگر در سرور دیگری مستقر کرده‌اید، آدرس آن را متناسب با سرور خود تغییر دهید.
5. روی "Register application" کلیک کنید.
6. Client ID نمایش داده می‌شود و می‌توانید یک Client Secret ایجاد کنید.
7. این مقادیر را در فایل `.env` خود وارد کنید.

## نکات مهم

1. اگر خطای 404 در هنگام احراز هویت گیتهاب دریافت می‌کنید، مطمئن شوید که Callback URL در تنظیمات برنامه گیتهاب دقیقاً با آدرس برنامه شما مطابقت دارد.
2. مطمئن شوید که API گوگل و گیتهاب فعال هستند.
3. برای استفاده در محیط تولید، حتماً از HTTPS استفاده کنید.

## مجوز

این پروژه تحت مجوز MIT منتشر شده است. 
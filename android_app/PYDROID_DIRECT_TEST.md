# تست مستقیم اپلیکیشن با Pydroid 3 (بدون نیاز به APK)

یکی از سریع‌ترین روش‌ها برای تست اپلیکیشن Python در گوشی‌های اندروید، استفاده از برنامه Pydroid 3 است. با این روش نیازی به ساخت فایل APK نیست و می‌توانید مستقیماً کد برنامه را روی گوشی اجرا کنید.

## مزایای این روش

- نیازی به ساخت APK ندارد
- نیازی به نصب لینوکس، WSL یا استفاده از سرویس‌های آنلاین نیست
- امکان اعمال تغییرات سریع و دیدن نتیجه به صورت آنی
- پشتیبانی کامل از Kivy و سایر کتابخانه‌های مورد نیاز
- نصب آسان کتابخانه‌های مورد نیاز با pip

## مراحل انجام کار

### 1. نصب Pydroid 3 از Google Play

1. به [صفحه Pydroid 3 در Google Play](https://play.google.com/store/apps/details?id=ru.iiec.pydroid3) بروید
2. برنامه Pydroid 3 را نصب کنید
3. اگر نسخه رایگان را نصب می‌کنید، برخی از ویژگی‌ها مانند پشتیبانی از OpenCV محدود خواهند بود

### 2. نصب کتابخانه‌های مورد نیاز

1. پس از نصب Pydroid 3، برنامه را باز کنید
2. از منوی اصلی به بخش "Pip" بروید
3. کتابخانه‌های زیر را نصب کنید:
   - `kivy`
   - `requests`
   - `plyer` (برای دسترسی به ویژگی‌های گوشی)
   
### 3. انتقال کد برنامه به گوشی

**روش اول: انتقال مستقیم فایل‌ها**
1. گوشی خود را به کامپیوتر متصل کنید
2. تمام فایل‌های پوشه `android_app` را به یک پوشه در گوشی کپی کنید
3. اطمینان حاصل کنید که فایل `main.py` و سایر فایل‌های مورد نیاز منتقل شده‌اند

**روش دوم: ایجاد زیپ و اسکن QR کد**
1. فایل‌های پروژه را در یک فایل ZIP فشرده کنید
2. فایل ZIP را در یک سرویس مانند Dropbox یا Google Drive آپلود کنید
3. با استفاده از سایت‌هایی مانند [QR Code Generator](https://www.qr-code-generator.com) برای لینک دانلود یک QR کد ایجاد کنید
4. با دوربین گوشی، QR کد را اسکن کنید و فایل ZIP را دانلود و استخراج کنید

### 4. اجرای برنامه در Pydroid 3

1. برنامه Pydroid 3 را باز کنید
2. از منوی اصلی، گزینه "Open" را انتخاب کنید
3. به مسیری که فایل‌های پروژه را منتقل کرده‌اید بروید
4. فایل `main.py` را انتخاب کنید
5. روی دکمه "Run" (▶️) کلیک کنید تا برنامه اجرا شود

### 5. اشکال‌زدایی و تست

- با استفاده از ویژگی‌های Pydroid می‌توانید کد را ویرایش کنید
- تغییرات را ذخیره کرده و مجدداً برنامه را اجرا کنید
- از ویژگی‌های اشکال‌زدایی (Debug) برای بررسی مشکلات استفاده کنید

## نکات مهم

1. **کتابخانه‌های مورد نیاز**: اطمینان حاصل کنید که تمام کتابخانه‌های مورد نیاز برنامه را در Pydroid نصب کرده‌اید
2. **فونت فارسی**: فایل فونت Vazirmatn را حتماً در پوشه `assets` قرار دهید
3. **منابع**: اطمینان حاصل کنید که مسیر دسترسی به منابع (تصاویر، فونت‌ها) در کد به درستی تنظیم شده باشد
4. **عملکرد**: برخی ویژگی‌های پیشرفته ممکن است در Pydroid با محدودیت‌هایی همراه باشند
5. **حافظه**: اگر برنامه شما حجم زیادی از حافظه را اشغال می‌کند، ممکن است با محدودیت‌های گوشی مواجه شوید

## رفع مشکلات احتمالی

- **خطای ImportError**: اطمینان حاصل کنید که کتابخانه مورد نظر را با pip نصب کرده‌اید
- **خطای FileNotFound**: مسیر‌های فایل‌ها را بررسی کنید، مسیرهای نسبی معمولاً بهتر کار می‌کنند
- **مشکلات نمایشی**: ممکن است نیاز به تغییر برخی تنظیمات نمایشی در کد Kivy داشته باشید تا با صفحه نمایش گوشی سازگار شود
- **کندی اجرا**: اپلیکیشن‌های پیچیده ممکن است روی گوشی‌های ضعیف‌تر کند اجرا شوند 
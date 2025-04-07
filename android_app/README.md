# دستیار هوشمند فارسی (نسخه اندروید)

این پروژه یک اپلیکیشن اندروید برای گفتگو با هوش مصنوعی به زبان فارسی است که از API OpenRouter استفاده می‌کند.

## ویژگی‌ها

- رابط کاربری زیبا و ساده با پشتیبانی از زبان فارسی
- امکان مدیریت چندین کلید API برای دور زدن محدودیت استفاده روزانه
- ذخیره و مدیریت گفتگوها
- امکان استفاده آفلاین از گفتگوهای ذخیره شده
- پشتیبانی از تم تاریک

## نیازمندی‌ها برای ساخت APK

برای ساخت فایل APK، به موارد زیر نیاز دارید:

1. **نصب Python 3.7+**
2. **نصب Buildozer**:
   ```
   pip install buildozer
   ```
3. **نصب ابزارهای لازم در Ubuntu/Debian**:
   ```
   sudo apt-get install -y python3-pip build-essential git python3 python3-dev ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev
   ```
   ```
   sudo apt-get install -y libgstreamer1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good
   ```
   ```
   sudo apt-get install -y build-essential libsqlite3-dev sqlite3 bzip2 libbz2-dev zlib1g-dev libssl-dev openssl libgdbm-dev libgdbm-compat-dev liblzma-dev libreadline-dev libncursesw5-dev libffi-dev uuid-dev libffi6
   ```
   ```
   sudo apt-get install -y libfreetype6-dev libgl1-mesa-dev libgles2-mesa-dev
   ```

4. **نصب JDK 8**:
   ```
   sudo apt-get install -y openjdk-8-jdk
   ```
   
5. **نصب ابزارهای Android SDK**:
   Buildozer به صورت خودکار این ابزارها را دانلود و نصب می‌کند ولی می‌توانید آنها را دستی هم نصب کنید.

## مراحل ساخت APK

1. **آماده‌سازی پروژه**:
   ```
   cd android_app
   ```

2. **اجرای Buildozer برای اولین بار** (این مرحله ابزارهای لازم را نصب می‌کند):
   ```
   buildozer init
   ```

3. **ساخت APK در حالت دیباگ**:
   ```
   buildozer android debug
   ```

4. **ساخت نسخه نهایی APK**:
   ```
   buildozer android release
   ```

5. **نصب APK روی دستگاه متصل**:
   ```
   buildozer android debug deploy run
   ```

## استفاده از کلیدهای API

برای افزودن کلیدهای API جدید، از دو روش می‌توانید استفاده کنید:

1. **درون برنامه**: از منوی اصلی وارد بخش مدیریت کلیدها شوید و کلید جدید را اضافه کنید.

2. **فایل متنی**: یک فایل متنی به نام `api_keys.txt` در کنار فایل اجرایی برنامه ایجاد کنید و در هر خط یک کلید API وارد نمایید.

## نکات فنی

- کلیدهای API به صورت خودکار هر روز ریست می‌شوند
- برنامه خودکار بین کلیدهای در دسترس تغییر وضعیت می‌دهد
- در صورت مشکل با یک کلید، آن را به صورت خودکار غیرفعال کرده و از کلید دیگری استفاده می‌کند

## منابع و کتابخانه‌های استفاده شده

- [Kivy](https://kivy.org/)
- [OpenRouter API](https://openrouter.ai/)
- [Requests](https://docs.python-requests.org/)
- [Buildozer](https://github.com/kivy/buildozer)

## سازنده

این پروژه توسط ایجاد شده است.

## مجوز

این پروژه تحت مجوز MIT منتشر شده است. 
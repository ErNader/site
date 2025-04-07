# راهنمای ساخت APK

این فایل راهنما نحوه ساخت فایل APK برای اپلیکیشن دستیار هوشمند فارسی را توضیح می‌دهد.

## پیش‌نیازها

### برای کاربران ویندوز

1. **نصب WSL (Windows Subsystem for Linux)**:
   - از پنل کنترل ویندوز، به بخش "Turn Windows features on or off" بروید
   - گزینه "Windows Subsystem for Linux" را فعال کنید
   - یا در PowerShell به عنوان ادمین دستور زیر را اجرا کنید:
     ```
     dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
     ```

2. **نصب Ubuntu از Microsoft Store**

3. **پیکربندی WSL**:
   - Ubuntu را اجرا کنید و یک نام کاربری و رمز عبور تنظیم کنید
   - بسته‌های سیستم را با دستور زیر به‌روزرسانی کنید:
     ```
     sudo apt update && sudo apt upgrade -y
     ```

4. **نصب پیش‌نیازها در Ubuntu**:
   ```
   sudo apt-get install -y python3-pip build-essential git python3 python3-dev ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev
   ```
   ```
   sudo apt-get install -y libgstreamer1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good
   ```
   ```
   sudo apt-get install -y build-essential libsqlite3-dev sqlite3 bzip2 libbz2-dev zlib1g-dev libssl-dev openssl libgdbm-dev libgdbm-compat-dev liblzma-dev libreadline-dev libncursesw5-dev libffi-dev uuid-dev
   ```
   ```
   sudo apt-get install -y libfreetype6-dev libgl1-mesa-dev libgles2-mesa-dev
   ```

5. **نصب JDK 8**:
   ```
   sudo apt-get install -y openjdk-8-jdk
   ```

6. **نصب Buildozer**:
   ```
   pip3 install --user buildozer
   ```

7. **نصب ابزارهای اضافی**:
   ```
   sudo apt-get install -y automake autoconf
   pip3 install --user cython
   ```

### برای کاربران لینوکس (Ubuntu/Debian)

1. **نصب پیش‌نیازها**:
   ```
   sudo apt-get install -y python3-pip build-essential git python3 python3-dev ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev
   ```
   ```
   sudo apt-get install -y libgstreamer1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good
   ```
   ```
   sudo apt-get install -y build-essential libsqlite3-dev sqlite3 bzip2 libbz2-dev zlib1g-dev libssl-dev openssl libgdbm-dev libgdbm-compat-dev liblzma-dev libreadline-dev libncursesw5-dev libffi-dev uuid-dev
   ```
   ```
   sudo apt-get install -y libfreetype6-dev libgl1-mesa-dev libgles2-mesa-dev
   ```

2. **نصب JDK 8**:
   ```
   sudo apt-get install -y openjdk-8-jdk
   ```

3. **نصب Buildozer**:
   ```
   pip3 install --user buildozer
   ```

4. **نصب ابزارهای اضافی**:
   ```
   sudo apt-get install -y automake autoconf
   pip3 install --user cython
   ```

## فرآیند ساخت APK

1. **تهیه فونت فارسی**:
   - فونت Vazirmatn را از [اینجا](https://github.com/rastikerdar/vazirmatn/releases) دانلود کنید
   - فایل فونت را با نام `Vazirmatn.ttf` در پوشه `assets` قرار دهید

2. **ایجاد فایل‌های تصویر**:
   - یک فایل `icon.png` با اندازه 512x512 پیکسل برای آیکون برنامه
   - یک فایل `presplash.png` با اندازه 1024x1024 پیکسل برای صفحه اسپلش
   - این فایل‌ها را در پوشه `assets` قرار دهید

3. **انتقال پروژه به WSL (در ویندوز)**:
   - پوشه پروژه را به مسیر قابل دسترس در WSL کپی کنید:
   ```
   cp -r /mnt/c/Users/YOUR_USERNAME/path/to/android_app ~/android_app
   ```

4. **ساخت APK**:
   ```
   cd ~/android_app
   buildozer android debug
   ```

5. **انتظار برای اتمام فرآیند**:
   - فرآیند ساخت APK ممکن است چند دقیقه تا چند ساعت طول بکشد (بار اول)
   - Buildozer به صورت خودکار SDK اندروید و سایر ابزارهای مورد نیاز را دانلود و نصب می‌کند

6. **یافتن فایل APK**:
   - بعد از اتمام فرآیند، فایل APK در مسیر زیر قرار خواهد گرفت:
   ```
   ~/android_app/bin/persian_llm_assistant-0.1-debug.apk
   ```

7. **انتقال APK به ویندوز (در صورت استفاده از WSL)**:
   ```
   cp ~/android_app/bin/persian_llm_assistant-0.1-debug.apk /mnt/c/Users/YOUR_USERNAME/Desktop/
   ```

## نصب APK روی گوشی

1. فایل APK را به گوشی اندروید خود منتقل کنید
2. در تنظیمات گوشی، نصب برنامه‌ها از منابع ناشناس را فعال کنید
3. روی فایل APK کلیک کنید و برنامه را نصب نمایید

## اشکال‌زدایی

در صورت بروز مشکل حین ساخت APK، موارد زیر را بررسی کنید:

1. **مشکل در پیدا کردن کتابخانه‌ها**:
   ```
   sudo apt install -y build-essential libsqlite3-dev sqlite3 bzip2 libbz2-dev zlib1g-dev libssl-dev openssl libffi-dev
   ```

2. **مشکل در SDK اندروید**:
   - می‌توانید بیلدوزر را با پارامتر زیر اجرا کنید تا SDK را مجددا دانلود کند:
   ```
   buildozer android clean
   buildozer android debug
   ```

3. **خطاهای JDK**:
   - مطمئن شوید که JDK 8 نصب شده و متغیر JAVA_HOME تنظیم شده است:
   ```
   export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
   ```

4. **مشکل در پیدا کردن Cython**:
   ```
   pip3 install --user cython==0.29.19
   ```

## منابع بیشتر

- [مستندات Buildozer](https://buildozer.readthedocs.io/en/latest/)
- [مستندات Kivy](https://kivy.org/doc/stable/)
- [راهنمای ساخت اپلیکیشن اندروید با Kivy](https://kivy.org/doc/stable/guide/packaging-android.html) 
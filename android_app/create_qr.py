#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اسکریپت ساخت QR کد برای لینک دانلود فایل‌های پروژه
"""

import qrcode
import sys
from PIL import Image, ImageDraw, ImageFont
import os

def create_qr_code(url, output_file='qrcode.png', title="اسکن کنید"):
    """ساخت QR کد برای لینک دانلود"""
    # ساخت QR کد
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # ساخت تصویر
    img = qr.make_image(fill_color="black", back_color="white")
    
    # افزودن عنوان به تصویر
    # ایجاد یک تصویر جدید با فضای بیشتر برای متن
    width, height = img.size
    new_img = Image.new('RGB', (width, height + 50), color='white')
    new_img.paste(img, (0, 0))
    
    # افزودن متن
    draw = ImageDraw.Draw(new_img)
    
    # تلاش برای استفاده از فونت فارسی اگر وجود داشت
    try:
        # چک کردن پوشه assets برای فونت فارسی
        if os.path.exists('assets/Vazirmatn.ttf'):
            font = ImageFont.truetype('assets/Vazirmatn.ttf', 20)
        else:
            # استفاده از فونت پیش‌فرض
            font = ImageFont.load_default()
    except Exception:
        # در صورت خطا استفاده از فونت پیش‌فرض
        font = ImageFont.load_default()
    
    # اضافه کردن متن در زیر QR کد
    text_width = draw.textlength(title, font=font)
    draw.text(((width - text_width) // 2, height + 10), title, font=font, fill='black')
    
    # ذخیره تصویر
    new_img.save(output_file)
    print(f"QR کد در فایل {output_file} ذخیره شد.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else 'qrcode.png'
        title = sys.argv[3] if len(sys.argv) > 3 else "اسکن کنید تا برنامه را دانلود کنید"
        create_qr_code(url, output_file, title)
    else:
        # اگر URL داده نشده، از کاربر دریافت می‌کنیم
        url = input("لینک دانلود فایل ZIP پروژه را وارد کنید: ")
        output_file = input("نام فایل تصویر QR کد را وارد کنید (پیش‌فرض: qrcode.png): ") or "qrcode.png"
        title = input("متن توضیحی را وارد کنید (پیش‌فرض: اسکن کنید): ") or "اسکن کنید تا برنامه را دانلود کنید"
        create_qr_code(url, output_file, title) 
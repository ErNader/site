# -*- coding: utf-8 -*-

"""
کنترل‌کننده‌های دستورات ربات بله
"""

import asyncio
from typing import Dict

from balethon import Client
from balethon.handlers import CommandHandler, MessageHandler, CallbackQueryHandler

from config import WELCOME_MESSAGE, HELP_MESSAGE, MODELS, RATE_LIMIT
from utils import (
    get_bot_response,
    create_new_conversation,
    get_user_model,
    set_user_model,
    get_model_info,
    format_message
)

# حافظه موقت برای کنترل نرخ ارسال درخواست‌ها
rate_limit_dict: Dict[int, float] = {}

async def start_command(client: Client, message) -> None:
    """
    مدیریت دستور شروع
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "کاربر"
    
    welcome_text = f"سلام {first_name}!\n\n{WELCOME_MESSAGE}"
    
    # ایجاد دکمه‌های شروع
    keyboard = [
        [
            {"text": "گفتگوی جدید 🆕", "callback_data": "new_chat"},
            {"text": "تغییر مدل 🧠", "callback_data": "change_model"}
        ],
        [
            {"text": "راهنما ❓", "callback_data": "help"}
        ]
    ]
    
    await message.reply(
        welcome_text,
        reply_markup={"inline_keyboard": keyboard}
    )

async def help_command(client: Client, message) -> None:
    """
    نمایش راهنمای دستورات
    """
    await message.reply(
        HELP_MESSAGE,
        parse_mode="markdown"
    )

async def new_chat_command(client: Client, message) -> None:
    """
    شروع گفتگوی جدید
    """
    user_id = message.from_user.id
    result = await create_new_conversation(user_id)
    await message.reply(result)

async def model_command(client: Client, message) -> None:
    """
    تغییر مدل هوش مصنوعی
    """
    user_id = message.from_user.id
    
    # دریافت اطلاعات مدل فعلی
    current_model_info = get_model_info(user_id)
    
    # ایجاد دکمه‌ها برای انتخاب مدل
    keyboard = []
    for key, model in MODELS.items():
        is_current = current_model_info["id"] == model["id"]
        button_text = f"{'✅ ' if is_current else ''}{model['name']}"
        keyboard.append([{"text": button_text, "callback_data": f"model_{key}"}])
    
    await message.reply(
        f"مدل فعلی: **{current_model_info['name']}**\n\n{current_model_info['description']}\n\nلطفاً مدل مورد نظر را انتخاب کنید:",
        reply_markup={"inline_keyboard": keyboard},
        parse_mode="markdown"
    )

async def handle_callback_query(client: Client, callback_query) -> None:
    """
    مدیریت رویدادهای callback_query
    """
    query_data = callback_query.data
    message = callback_query.message
    user_id = callback_query.from_user.id
    
    # اعلام دریافت کالبک به سرور بله
    await callback_query.answer()
    
    if query_data == "new_chat":
        result = await create_new_conversation(user_id)
        await message.reply(result)
    
    elif query_data == "help":
        await message.reply(HELP_MESSAGE, parse_mode="markdown")
    
    elif query_data == "change_model":
        await model_command(client, message)
    
    elif query_data.startswith("model_"):
        model_key = query_data.split("_")[1]
        set_user_model(user_id, model_key)
        model_info = get_model_info(user_id)
        
        await message.edit_text(
            f"مدل هوش مصنوعی به **{model_info['name']}** تغییر یافت.\n\n{model_info['description']}",
            parse_mode="markdown"
        )

async def handle_message(client: Client, message) -> None:
    """
    مدیریت پیام‌های معمولی
    """
    # اگر پیام، دستور باشد، پردازش نکن
    if message.text and message.text.startswith('/'):
        return
        
    user_id = message.from_user.id
    user_message = message.text or message.caption or ""
    
    if not user_message:
        await message.reply("لطفاً یک پیام متنی ارسال کنید.")
        return
    
    # محدودیت نرخ درخواست‌ها
    current_time = asyncio.get_event_loop().time()
    if user_id in rate_limit_dict:
        time_diff = current_time - rate_limit_dict[user_id]
        if time_diff < RATE_LIMIT:
            wait_time = round(RATE_LIMIT - time_diff)
            if wait_time > 0:
                await message.reply(
                    f"لطفاً {wait_time} ثانیه صبر کنید و دوباره تلاش کنید."
                )
                return
    
    # بروزرسانی زمان آخرین درخواست
    rate_limit_dict[user_id] = current_time
    
    # ارسال وضعیت "در حال تایپ"
    await message.chat.send_action("typing")
    
    # دریافت مدل انتخاب‌شده توسط کاربر
    model = get_user_model(user_id)
    
    # ارسال پیام کوتاه برای نشان دادن شروع پردازش
    processing_message = await message.reply(
        "در حال پردازش پیام شما..."
    )
    
    try:
        # ارسال درخواست به API و دریافت پاسخ
        response = await get_bot_response(user_message, user_id, model)
        
        # حذف پیام "در حال پردازش"
        await processing_message.delete()
        
        # فرمت کردن پاسخ برای نمایش در بله
        formatted_response = format_message(response)
        
        # ارسال پاسخ در بخش‌های مختلف اگر خیلی طولانی باشد
        max_message_length = 4000
        for i in range(0, len(formatted_response), max_message_length):
            chunk = formatted_response[i:i + max_message_length]
            if chunk:
                await message.reply(chunk)
                
                # کمی تاخیر بین ارسال بخش‌های مختلف
                if len(formatted_response) > max_message_length:
                    await asyncio.sleep(0.5)
    except Exception as e:
        # حذف پیام "در حال پردازش" در صورت خطا
        try:
            await processing_message.delete()
        except:
            pass
            
        # ارسال پیام خطا
        await message.reply(
            f"خطا در پردازش درخواست: {str(e)}\n\nلطفاً دوباره تلاش کنید."
        )

async def register_handlers(client: Client) -> None:
    """
    ثبت تمام کنترل‌کننده‌ها
    """
    # ثبت دستورات اصلی با استفاده از CommandHandler
    client.add_handler(CommandHandler("start", start_command))
    client.add_handler(CommandHandler("help", help_command))
    client.add_handler(CommandHandler("new", new_chat_command))
    client.add_handler(CommandHandler("model", model_command))
    
    # ثبت مدیریت کالبک‌ها با استفاده از CallbackQueryHandler
    client.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # ثبت مدیریت پیام‌های معمولی با استفاده از MessageHandler
    client.add_handler(MessageHandler(handle_message)) 
"""
توابع کمکی برای ربات بله
"""

import json
import asyncio
import aiohttp
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# دیکشنری برای نگهداری اطلاعات گفتگو‌ها
user_sessions: Dict[int, Dict[str, Any]] = {}

async def get_bot_response(message: str, user_id: int, model: str = "deepseek-coder-33b-instruct") -> str:
    """
    دریافت پاسخ از API هوش مصنوعی
    
    Args:
        message: پیام کاربر
        user_id: شناسه کاربر
        model: نام مدل هوش مصنوعی
        
    Returns:
        پاسخ هوش مصنوعی
    """
    from config import AI_API_KEY, AI_API_URL
    
    # دریافت تاریخچه گفتگو
    history = get_conversation_history(user_id)
    
    # افزودن پیام جدید کاربر به تاریخچه
    add_message_to_history(user_id, "user", message)
    
    # ساخت ساختار پیام‌ها برای API
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    messages.append({"role": "user", "content": message})
    
    # تنظیم درخواست
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(AI_API_URL, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    bot_response = data["choices"][0]["message"]["content"]
                    
                    # افزودن پاسخ بات به تاریخچه
                    add_message_to_history(user_id, "assistant", bot_response)
                    
                    return bot_response
                else:
                    error_text = await response.text()
                    print(f"API Error: Status {response.status}, Response: {error_text}")
                    return "خطا در ارتباط با سرور هوش مصنوعی. لطفاً دوباره تلاش کنید."
    except Exception as e:
        print(f"API Error: {e}")
        return "خطا در ارتباط با سرور هوش مصنوعی. لطفاً دوباره تلاش کنید."

def get_conversation_history(user_id: int) -> List[Dict[str, str]]:
    """
    دریافت تاریخچه گفتگو برای کاربر
    
    Args:
        user_id: شناسه کاربر
        
    Returns:
        لیست پیام‌های تاریخچه گفتگو
    """
    if user_id not in user_sessions or "history" not in user_sessions[user_id]:
        return []
    return user_sessions[user_id]["history"]

def add_message_to_history(user_id: int, role: str, content: str) -> None:
    """
    افزودن پیام به تاریخچه گفتگو
    
    Args:
        user_id: شناسه کاربر
        role: نقش فرستنده پیام (user یا assistant)
        content: محتوای پیام
    """
    from config import MAX_HISTORY_LENGTH
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {"history": []}
    
    if "history" not in user_sessions[user_id]:
        user_sessions[user_id]["history"] = []
    
    user_sessions[user_id]["history"].append({
        "role": role,
        "content": content
    })
    
    # محدود کردن طول تاریخچه
    if len(user_sessions[user_id]["history"]) > MAX_HISTORY_LENGTH:
        # حذف قدیمی‌ترین پیام‌ها به جز پیام‌های سیستمی (اگر وجود دارند)
        system_msgs = [msg for msg in user_sessions[user_id]["history"] if msg["role"] == "system"]
        other_msgs = [msg for msg in user_sessions[user_id]["history"] if msg["role"] != "system"]
        
        # برش تاریخچه
        other_msgs = other_msgs[-(MAX_HISTORY_LENGTH - len(system_msgs)):]
        
        # ترکیب مجدد پیام‌ها
        user_sessions[user_id]["history"] = system_msgs + other_msgs

async def create_new_conversation(user_id: int) -> str:
    """
    ایجاد گفتگوی جدید
    
    Args:
        user_id: شناسه کاربر
        
    Returns:
        پیام نتیجه
    """
    conversation_id = str(uuid.uuid4())
    
    # ذخیره اطلاعات جدید
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    
    user_sessions[user_id]["conversation_id"] = conversation_id
    user_sessions[user_id]["created_at"] = datetime.now()
    user_sessions[user_id]["history"] = []  # پاک کردن تاریخچه گفتگو
    
    # افزودن یک پیام سیستمی به عنوان راهنمایی برای مدل
    system_message = "شما یک دستیار هوشمند فارسی هستید. لطفاً به زبان فارسی پاسخ دهید و تا حد امکان مفید و دقیق باشید."
    user_sessions[user_id]["history"].append({
        "role": "system",
        "content": system_message
    })
    
    return "گفتگوی جدید آغاز شد. می‌توانید سوال خود را بپرسید."

def get_user_model(user_id: int) -> str:
    """
    دریافت مدل انتخاب شده توسط کاربر
    
    Args:
        user_id: شناسه کاربر
        
    Returns:
        شناسه مدل
    """
    from config import MODELS
    
    if user_id in user_sessions and "model" in user_sessions[user_id]:
        return user_sessions[user_id]["model"]
    return MODELS["deepseek"]["id"]

def set_user_model(user_id: int, model_key: str) -> None:
    """
    تنظیم مدل هوش مصنوعی برای کاربر
    
    Args:
        user_id: شناسه کاربر
        model_key: کلید مدل
    """
    from config import MODELS
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    
    if model_key in MODELS:
        user_sessions[user_id]["model"] = MODELS[model_key]["id"]
        user_sessions[user_id]["model_key"] = model_key
    else:
        user_sessions[user_id]["model"] = MODELS["deepseek"]["id"]
        user_sessions[user_id]["model_key"] = "deepseek"

def get_model_info(user_id: int) -> Dict[str, str]:
    """
    دریافت اطلاعات مدل فعلی کاربر
    
    Args:
        user_id: شناسه کاربر
        
    Returns:
        دیکشنری اطلاعات مدل
    """
    from config import MODELS
    
    model_key = "deepseek"
    if user_id in user_sessions and "model_key" in user_sessions[user_id]:
        model_key = user_sessions[user_id]["model_key"]
    
    return MODELS[model_key]

def format_message(text: str) -> str:
    """
    فرمت کردن پیام برای نمایش مناسب در بله
    
    Args:
        text: متن پیام
        
    Returns:
        متن فرمت شده
    """
    # تبدیل بلوک‌های کد
    lines = text.split('\n')
    in_code_block = False
    formatted_lines = []
    
    for line in lines:
        if line.strip().startswith('```') and not in_code_block:
            in_code_block = True
            formatted_lines.append('```')
            # حذف زبان برنامه‌نویسی از خط
            if len(line.strip()) > 3:
                formatted_lines.append(line.strip()[3:].strip())
        elif line.strip().endswith('```') and in_code_block:
            in_code_block = False
            if line.strip() != '```':
                formatted_lines.append(line.strip()[:-3].strip())
            formatted_lines.append('```')
        else:
            formatted_lines.append(line)
    
    formatted_text = '\n'.join(formatted_lines)
    
    # حذف تگ‌های HTML اضافی
    formatted_text = formatted_text.replace('<p>', '').replace('</p>', '\n')
    formatted_text = formatted_text.replace('<br>', '\n').replace('<br/>', '\n')
    
    return formatted_text 
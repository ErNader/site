import asyncio
import aiohttp
from balethon import Client
from balethon.conditions import private

# توکن‌های API
BALE_BOT_TOKEN = "1975677609:uVT1f1Z5Kzf98eRtWypJdywA6lBAD1P4GeqbCMPT"
AI_API_KEY = "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"
AI_API_URL = "https://api.openrouter.ai/api/v1/chat/completions"

# ایجاد کلاینت Balethon
bot = Client(BALE_BOT_TOKEN)

# ذخیره‌سازی حافظه مکالمه کاربران به ازای هر کاربر
user_contexts = {}

async def send_typing_action(chat_id):
    """ارسال وضعیت 'در حال تایپ' به چت."""
    await bot.send_chat_action(chat_id, "typing")

async def get_ai_response(user_id, user_input):
    """ارسال پیام کاربر به API هوش مصنوعی و دریافت پاسخ."""
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    context = user_contexts.get(user_id, [])
    context.append({"role": "user", "content": user_input})
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": context
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(AI_API_URL, headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                ai_message = result['choices'][0]['message']['content']
                context.append({"role": "assistant", "content": ai_message})
                # نگه داشتن تنها ۱۰ پیام آخر به عنوان حافظه مکالمه
                user_contexts[user_id] = context[-10:]
                return ai_message
            else:
                return "متأسفانه در ارتباط با سرور هوش مصنوعی مشکلی پیش آمد."

@bot.on_message(private)
async def handle_message(message):
    """پردازش پیام‌های دریافتی از کاربران."""
    user_id = message.author.id
    if message.text:
        # ارسال وضعیت 'در حال تایپ'
        await send_typing_action(message.chat.id)
        # دریافت پاسخ از هوش مصنوعی
        ai_response = await get_ai_response(user_id, message.text)
        await message.reply(ai_response)
    elif message.document or message.photo:
        # پردازش فایل‌ها یا تصاویر دریافتی
        if message.document:
            file_name = message.document.file_name
            await message.reply(f"فایل '{file_name}' دریافت شد.")
        elif message.photo:
            await message.reply("تصویر دریافت شد.")

# اجرای ربات
bot.run()

import os
import json
import requests
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.modalview import ModalView
from kivy.uix.image import Image
from kivy.lang import Builder
from kivy.utils import platform
from kivy.garden.markdown import MarkdownLabel
import threading
import uuid

# تنظیم زبان فارسی
os.environ['KIVY_TEXT'] = 'pil'

# کلاس مدیریت API کلیدها
class ApiKeyManager:
    def __init__(self):
        # کلید API اصلی
        self.api_keys = [
            {"key": "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", 
             "uses": 0, 
             "last_used": None, 
             "max_daily": 100, 
             "working": True},
        ]
        
        # لود کلیدهای اضافی
        self.keys_file = "api_keys.txt"
        self.load_additional_keys()
        
        self.current_key_index = 0
        print(f"تعداد {len(self.api_keys)} کلید API آماده استفاده است.")
    
    def load_additional_keys(self):
        """بارگذاری کلیدهای اضافی از فایل متنی"""
        try:
            if os.path.exists(self.keys_file):
                with open(self.keys_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line and line.startswith('sk-or-v1-') and not any(k['key'] == line for k in self.api_keys):
                            self.api_keys.append({
                                "key": line, 
                                "uses": 0, 
                                "last_used": None,
                                "max_daily": 100,
                                "working": True
                            })
                print(f"تعداد {len(lines)} کلید API از فایل {self.keys_file} بارگذاری شد.")
        except Exception as e:
            print(f"خطا در بارگذاری کلیدهای اضافی: {str(e)}")
    
    def add_key(self, new_key):
        """اضافه کردن کلید جدید"""
        if not new_key.startswith('sk-or-v1-'):
            return False, "کلید API نامعتبر است. کلید باید با sk-or-v1- شروع شود."
        
        # بررسی تکراری نبودن کلید
        if any(k['key'] == new_key for k in self.api_keys):
            return False, "این کلید قبلاً اضافه شده است."
        
        # افزودن کلید جدید
        self.api_keys.append({
            "key": new_key, 
            "uses": 0, 
            "last_used": None,
            "max_daily": 100,
            "working": True
        })
        
        # ذخیره در فایل
        try:
            with open(self.keys_file, 'a') as f:
                f.write(f"{new_key}\n")
        except Exception as e:
            print(f"خطا در ذخیره کلید جدید: {str(e)}")
        
        return True, f"کلید API جدید اضافه شد. تعداد کل کلیدها: {len(self.api_keys)}"
    
    def get_next_key(self):
        """انتخاب کلید بعدی برای استفاده"""
        # اگر هیچ کلیدی نداریم
        if not self.api_keys:
            return None
        
        # بررسی وضعیت کلیدها و انتخاب بهترین کلید
        today = datetime.now().date()
        working_keys = [k for k in self.api_keys if k['working']]
        
        if not working_keys:
            print("هیچ کلید کارآمدی یافت نشد!")
            return None
        
        # بازنشانی شمارنده استفاده برای کلیدهایی که امروز استفاده نشده‌اند
        for key in self.api_keys:
            if key['last_used'] is None or key['last_used'].date() < today:
                key['uses'] = 0
                key['last_used'] = None
        
        # ابتدا کلیدهایی که امروز استفاده نشده‌اند را انتخاب می‌کنیم
        unused_today = [k for k in working_keys if k['last_used'] is None or k['last_used'].date() < today]
        if unused_today:
            selected_key = unused_today[0]
        else:
            # کلیدی با کمترین استفاده را انتخاب می‌کنیم
            selected_key = min(working_keys, key=lambda k: k['uses'])
        
        # به‌روزرسانی اطلاعات کلید
        selected_key['uses'] += 1
        selected_key['last_used'] = datetime.now()
        
        print(f"استفاده از کلید API: {selected_key['key'][:8]}... (استفاده {selected_key['uses']} از {selected_key['max_daily']})")
        return selected_key['key']
    
    def mark_key_failed(self, key):
        """نشانه‌گذاری کلید به عنوان ناکارآمد"""
        for k in self.api_keys:
            if k['key'] == key:
                k['working'] = False
                print(f"کلید API به عنوان ناکارآمد نشانه‌گذاری شد: {k['key'][:8]}...")
                break

# ایجاد نمونه مدیر API
api_key_manager = ApiKeyManager()

# پیام سیستمی
SYSTEM_MESSAGE = {
    "role": "system",
    "content": """شما یک دستیار هوشمند، مودب و دوستانه به زبان فارسی هستید که در کمک به کاربر تخصص دارید.
    پاسخ‌های شما باید دقیق، مفید و مختصر باشد. 
    توضیحات را به گام‌های ساده و قابل فهم تقسیم کنید.
    اگر سوالی خارج از دانش یا توانایی شماست، صادقانه اعتراف کنید که پاسخ را نمی‌دانید."""
}

# UI اصلی برنامه
Builder.load_string('''
<MessageLabel>:
    canvas.before:
        Color:
            rgba: (0.2, 0.2, 0.3, 0.7) if self.is_bot else (0.1, 0.4, 0.7, 0.7)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]
    text_size: self.width, None
    size_hint: 1, None
    height: self.texture_size[1] + dp(20)
    padding: dp(10), dp(10)
    halign: 'right' if not self.is_bot else 'left'
    markup: True

<ChatScreen>:
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.05, 0.05, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            canvas.before:
                Color:
                    rgba: 0.1, 0.1, 0.2, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            Button:
                text: 'منو'
                size_hint_x: None
                width: dp(60)
                background_color: 0.2, 0.3, 0.8, 1
                on_release: root.show_menu()
            
            Label:
                text: 'گفتگوی هوشمند'
                font_name: 'Vazirmatn'
                size_hint_x: 1
            
            Button:
                text: '+'
                size_hint_x: None
                width: dp(50)
                background_color: 0.2, 0.6, 0.3, 1
                on_release: root.new_conversation()
        
        ScrollView:
            id: chat_scroll
            do_scroll_x: False
            bar_width: dp(10)
            bar_color: 0.7, 0.7, 0.8, 0.9
            bar_inactive_color: 0.5, 0.5, 0.6, 0.5
            effect_cls: "ScrollEffect"
            scroll_type: ['bars', 'content']
            
            BoxLayout:
                id: chat_layout
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(10)
                spacing: dp(10)
        
        BoxLayout:
            size_hint_y: None
            height: dp(120) if root.is_thinking else dp(60)
            padding: dp(5)
            spacing: dp(5)
            orientation: 'vertical'
            
            Label:
                id: thinking_label
                text: "در حال فکر کردن..."
                opacity: 1 if root.is_thinking else 0
                size_hint_y: None
                height: dp(60) if root.is_thinking else 0
                color: 0.7, 0.8, 1, 0.8
            
            BoxLayout:
                size_hint_y: None
                height: dp(60)
                spacing: dp(5)
                
                TextInput:
                    id: message_input
                    hint_text: 'پیام خود را وارد کنید...'
                    font_name: 'Vazirmatn'
                    multiline: True
                    cursor_color: 1, 1, 1, 1
                    foreground_color: 1, 1, 1, 1
                    background_color: 0.15, 0.15, 0.2, 1
                    padding: dp(12), dp(10)
                    font_size: '18sp'
                
                Button:
                    text: 'ارسال'
                    font_name: 'Vazirmatn'
                    size_hint_x: None
                    width: dp(80)
                    background_color: 0.2, 0.6, 0.9, 1
                    disabled: root.is_thinking
                    on_release: root.send_message()

<MenuScreen>:
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.05, 0.05, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            canvas.before:
                Color:
                    rgba: 0.1, 0.1, 0.2, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            Label:
                text: 'مدیریت کلیدهای API'
                font_name: 'Vazirmatn'
            
            Button:
                text: 'بازگشت'
                size_hint_x: None
                width: dp(80)
                background_color: 0.2, 0.3, 0.8, 1
                on_release: root.manager.current = 'chat'
        
        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(15)
                spacing: dp(15)
                
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(10)
                    
                    Label:
                        text: 'افزودن کلید API جدید'
                        font_name: 'Vazirmatn'
                        size_hint_y: None
                        height: dp(40)
                        halign: 'right'
                        text_size: self.width, None
                    
                    TextInput:
                        id: api_key_input
                        hint_text: 'کلید API را وارد کنید (با sk-or-v1- شروع شود)'
                        font_name: 'Vazirmatn'
                        size_hint_y: None
                        height: dp(50)
                        multiline: False
                    
                    Button:
                        text: 'افزودن کلید'
                        font_name: 'Vazirmatn'
                        size_hint_y: None
                        height: dp(50)
                        background_color: 0.2, 0.6, 0.3, 1
                        on_release: root.add_api_key()
                
                Label:
                    text: 'کلیدهای موجود:'
                    font_name: 'Vazirmatn'
                    size_hint_y: None
                    height: dp(40)
                    halign: 'right'
                    text_size: self.width, None
                
                BoxLayout:
                    id: api_keys_container
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(5)
''')

class MessageLabel(Label):
    is_bot = BooleanProperty(True)

class MenuScreen(Screen):
    def on_enter(self):
        self.refresh_api_keys()
    
    def refresh_api_keys(self):
        keys_container = self.ids.api_keys_container
        keys_container.clear_widgets()
        
        for i, key_data in enumerate(api_key_manager.api_keys):
            key_preview = f"{key_data['key'][:8]}..."
            status = "فعال" if key_data['working'] else "غیرفعال"
            uses = f"{key_data['uses']}/{key_data['max_daily']}"
            
            key_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
            
            key_label = Label(
                text=f"{i+1}. {key_preview} - وضعیت: {status} - استفاده: {uses}",
                halign='right',
                text_size=(Window.width - dp(100), None),
                size_hint_x=0.8
            )
            key_layout.add_widget(key_label)
            
            if key_data['working']:
                disable_btn = Button(
                    text='غیرفعال',
                    size_hint_x=0.2,
                    background_color=(0.8, 0.2, 0.2, 1)
                )
                disable_btn.key_index = i
                disable_btn.bind(on_release=self.disable_key)
                key_layout.add_widget(disable_btn)
            else:
                enable_btn = Button(
                    text='فعال',
                    size_hint_x=0.2,
                    background_color=(0.2, 0.6, 0.2, 1)
                )
                enable_btn.key_index = i
                enable_btn.bind(on_release=self.enable_key)
                key_layout.add_widget(enable_btn)
            
            keys_container.add_widget(key_layout)
    
    def add_api_key(self):
        key_text = self.ids.api_key_input.text.strip()
        success, message = api_key_manager.add_key(key_text)
        
        # نمایش پیام
        popup = ModalView(size_hint=(0.8, 0.3))
        layout = BoxLayout(orientation='vertical', padding=dp(20))
        
        msg_label = Label(
            text=message,
            font_name='Vazirmatn',
            halign='center',
            size_hint_y=0.7
        )
        layout.add_widget(msg_label)
        
        close_btn = Button(
            text='بستن',
            size_hint_y=0.3,
            background_color=(0.3, 0.5, 0.9, 1),
            font_name='Vazirmatn'
        )
        close_btn.bind(on_release=popup.dismiss)
        layout.add_widget(close_btn)
        
        popup.add_widget(layout)
        popup.open()
        
        if success:
            self.ids.api_key_input.text = ""
            self.refresh_api_keys()
    
    def disable_key(self, btn):
        key_data = api_key_manager.api_keys[btn.key_index]
        key_data['working'] = False
        self.refresh_api_keys()
    
    def enable_key(self, btn):
        key_data = api_key_manager.api_keys[btn.key_index]
        key_data['working'] = True
        self.refresh_api_keys()

class ChatScreen(Screen):
    is_thinking = BooleanProperty(False)
    current_conversation_id = StringProperty("")
    conversations = ListProperty([])
    
    def __init__(self, **kwargs):
        super(ChatScreen, self).__init__(**kwargs)
        self.conversation_messages = []
        self.new_conversation()
    
    def on_enter(self):
        # اضافه کردن یک پیام خوش‌آمدگویی
        if not self.ids.chat_layout.children:
            welcome_msg = """به دستیار هوشمند فارسی خوش آمدید!
            
می‌توانید هر سوالی دارید از من بپرسید. برای شروع یک گفتگوی جدید، روی دکمه + در بالای صفحه بزنید.

نکات مهم:
• این برنامه از API OpenRouter استفاده می‌کند
• برای استفاده به اینترنت نیاز دارید
• می‌توانید کلیدهای API را در منو مدیریت کنید"""
            
            self.add_message(welcome_msg, is_bot=True)
    
    def new_conversation(self):
        self.conversation_messages = [SYSTEM_MESSAGE]
        self.current_conversation_id = str(uuid.uuid4())
        self.ids.chat_layout.clear_widgets()
        self.on_enter()  # نمایش پیام خوش‌آمدگویی
    
    def add_message(self, text, is_bot=False):
        msg_label = MessageLabel(text=text, is_bot=is_bot)
        self.ids.chat_layout.add_widget(msg_label)
        
        # اسکرول به پایین پس از اضافه کردن پیام
        Clock.schedule_once(lambda dt: setattr(self.ids.chat_scroll, 'scroll_y', 0), 0.1)
    
    def show_menu(self):
        self.manager.current = 'menu'
    
    def send_message(self):
        message_text = self.ids.message_input.text.strip()
        if not message_text:
            return
        
        # نمایش پیام کاربر
        self.add_message(message_text, is_bot=False)
        self.ids.message_input.text = ""
        
        # اضافه کردن پیام به مکالمه
        user_message = {"role": "user", "content": message_text}
        self.conversation_messages.append(user_message)
        
        # نمایش نشانگر تایپ کردن
        self.is_thinking = True
        
        # ارسال پیام در یک thread جداگانه
        threading.Thread(target=self.get_bot_response).start()
    
    def get_bot_response(self):
        try:
            # دریافت کلید API
            api_key = api_key_manager.get_next_key()
            if not api_key:
                Clock.schedule_once(lambda dt: self.handle_response_error("هیچ کلید API کارآمدی یافت نشد!"), 0)
                return
            
            # ارسال درخواست به OpenRouter
            response = requests.post(
                "https://api.openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "android.app.chatassistant",
                    "X-Title": "LLM Persian Bot"
                },
                json={
                    "model": "deepseek/deepseek-chat-v3-0324:free",
                    "messages": self.conversation_messages
                },
                timeout=60
            )
            
            # بررسی پاسخ
            if response.status_code != 200:
                error_message = f"خطای سرور: {response.status_code}"
                
                # بررسی محدودیت نرخ درخواست
                if response.status_code == 429:
                    api_key_manager.mark_key_failed(api_key)
                    error_message = "محدودیت API رسیده است. کلید به عنوان غیرفعال علامت‌گذاری شد."
                
                Clock.schedule_once(lambda dt: self.handle_response_error(error_message), 0)
                return
            
            # پردازش پاسخ موفق
            response_json = response.json()
            bot_response = response_json['choices'][0]['message']['content']
            
            # اضافه کردن پاسخ به لیست مکالمات
            self.conversation_messages.append({"role": "assistant", "content": bot_response})
            
            # نمایش پاسخ در رابط کاربری در thread اصلی
            Clock.schedule_once(lambda dt: self.add_message(bot_response, is_bot=True), 0)
            
        except Exception as e:
            # نمایش خطا
            error_message = f"خطا در ارتباط با سرور: {str(e)}"
            Clock.schedule_once(lambda dt: self.handle_response_error(error_message), 0)
        
        finally:
            # پایان وضعیت درحال فکر کردن
            Clock.schedule_once(lambda dt: setattr(self, 'is_thinking', False), 0)
    
    def handle_response_error(self, error_message):
        self.add_message(f"[color=ff5555]{error_message}[/color]", is_bot=True)

class ChatApp(App):
    def build(self):
        # تنظیم فونت فارسی
        self.title = 'دستیار هوشمند فارسی'
        
        # مدیریت صفحات
        sm = ScreenManager()
        sm.add_widget(ChatScreen(name='chat'))
        sm.add_widget(MenuScreen(name='menu'))
        
        return sm

if __name__ == '__main__':
    ChatApp().run() 
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory, Response, stream_with_context
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import requests
import uuid
from datetime import datetime, timedelta
from oauthlib.oauth2 import WebApplicationClient
import json
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-goes-here-make-it-very-long-and-secure')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# OAuth 2.0 client setup
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# GitHub OAuth setup
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# شناسایی URL پایه برای تنظیم callback‌ها
ROOT_URL = os.getenv("ROOT_URL", "http://localhost:5000")

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# بررسی کلید API در ابتدای برنامه
if not OPENROUTER_API_KEY:
    print("*" * 50)
    print("هشدار: کلید API برای OpenRouter تنظیم نشده است!")
    print("لطفاً فایل .env را ایجاد کرده و OPENROUTER_API_KEY را در آن تنظیم کنید.")
    print("قالب فایل .env:")
    print("OPENROUTER_API_KEY=«کلید API شما»")
    print("FLASK_SECRET_KEY=«یک رشته تصادفی طولانی»")
    print("*" * 50)
else:
    print("کلید API برای OpenRouter یافت شد.")
    # تست ارتباط با OpenRouter
    try:
        test_response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat-v3-0324:free",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            },
            timeout=5
        )
        if test_response.status_code == 200:
            print("✓ ارتباط با OpenRouter با موفقیت برقار شد.")
        else:
            print(f"✗ خطا در ارتباط با OpenRouter: {test_response.status_code}")
            print(f"پاسخ: {test_response.text[:200]}")
            
            # بررسی خطای خاص
            error_data = test_response.json() if test_response.text else {}
            error_message = error_data.get('error', {}).get('message', '') if isinstance(error_data, dict) else ''
            
            if "invalid api key" in error_message.lower() or "unauthorized" in error_message.lower():
                print("✗ کلید API نامعتبر است. لطفاً کلید API معتبر دریافت کنید.")
                print("برای دریافت کلید API به https://openrouter.ai/keys مراجعه کنید.")
            elif "rate limit" in error_message.lower():
                print("✗ محدودیت نرخ درخواست (Rate Limit) برای این کلید API فعال شده است.")
                print("لطفاً صبر کنید یا یک کلید API دیگر استفاده کنید.")
            elif "insufficient credit" in error_message.lower() or "quota exceeded" in error_message.lower():
                print("✗ اعتبار کلید API شما تمام شده است.")
                print("لطفاً برای شارژ مجدد به https://openrouter.ai/account مراجعه کنید.")    
    except Exception as e:
        print(f"✗ خطا در برقراری ارتباط با OpenRouter: {str(e)}")

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# مسیرهای callback برای احراز هویت
GOOGLE_CALLBACK_URL = f"{ROOT_URL}/login/google/callback"
GITHUB_CALLBACK_URL = f"{ROOT_URL}/login/github/callback"

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# OAuth clients
google_client = WebApplicationClient(GOOGLE_CLIENT_ID)

# System message for Persian AI Assistant
SYSTEM_MESSAGE = {
    "role": "system",
    "content": """شما یک دستیار هوشمند به زبان فارسی هستید. لطفاً به زبان فارسی پاسخ دهید، مؤدب و دوستانه باشید و اطلاعات دقیق ارائه کنید.

قابلیت‌های ویژه شما در فرمت‌بندی پاسخ‌ها:

1. استفاده از مارک‌داون برای فرمت‌بندی:
   - از `#` برای تیترهای اصلی استفاده کنید (مثال: `# تیتر اصلی`)
   - از `##` و `###` برای زیرتیترها استفاده کنید
   - از `**متن**` برای متن پررنگ استفاده کنید
   - از `*متن*` برای متن مورب استفاده کنید
   - از `---` برای خط افقی استفاده کنید

2. نمایش کد:
   - برای کد یک خطی از ``کد`` استفاده کنید
   - برای بلوک کد از ```‌ در خط اول و آخر استفاده کنید و نام زبان را نیز مشخص کنید:
     ```python
     def hello():
         print("سلام دنیا")
     ```

3. فرمول‌های ریاضی:
   - از `$فرمول$` برای فرمول‌های داخل خطی استفاده کنید (مثال: `$x^2 + y^2 = z^2$`)
   - از `$$فرمول$$` برای فرمول‌های مجزا استفاده کنید (مثال: `$$\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}$$`)

4. لیست‌ها:
   - از `-` یا `*` برای لیست غیر مرتب استفاده کنید
   - از `1.` برای لیست مرتب استفاده کنید

5. جداول:
   - از `|` برای ستون‌ها و `-` برای جداکننده سربرگ استفاده کنید

6. توجه به قالب‌بندی متن فارسی و مشکلات احتمالی مارک‌داون با زبان‌های راست به چپ.

لطفاً در زمان مناسب از این قابلیت‌ها استفاده کنید تا پاسخ‌های شما واضح‌تر و کاربردی‌تر باشند."""
}

def get_bot_response(conversation_messages, model="deepseek/deepseek-chat-v3-0324:free"):
    try:
        # استفاده از کلید API از سیستم مدیریت کلید
        api_key = get_openrouter_api_key()
        if not api_key:
            print("خطا: هیچ کلید API کارآمدی یافت نشد")
            return "متأسفانه در حال حاضر به دلیل مشکل API قادر به پاسخگویی نیستم. لطفاً بعداً دوباره تلاش کنید."
            
        print("ارسال درخواست به OpenRouter...")
        
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://localhost:5000/chat",
                "X-Title": "LLM Persian Bot"
            },
            json={
                "model": model,
                "messages": conversation_messages
            },
            timeout=60
        )
        
        # بررسی وضعیت پاسخ
        if response.status_code != 200:
            error_message = f"خطا از OpenRouter: کد وضعیت {response.status_code}"
            
            # بررسی محدودیت نرخ درخواست
            if response.status_code == 429:
                # علامت‌گذاری کلید به عنوان ناکارآمد
                mark_api_key_failed(api_key)
                
                # پیام خطای مناسب
                error_json = response.json()
                error_detail = error_json.get('error', {}).get('message', 'محدودیت نرخ درخواست')
                
                if 'rate limit' in str(error_detail).lower():
                    error_message = "محدودیت نرخ درخواست OpenRouter. در حال تعویض به کلید API دیگر..."
                    
                    # تلاش مجدد با کلید جدید
                    print("تلاش مجدد با کلید جدید...")
                    return get_bot_response(conversation_messages, model)
            
            print(error_message)
            return f"خطا در دریافت پاسخ: {error_message}"
            
        response_json = response.json()
        bot_response = response_json['choices'][0]['message']['content']
        return bot_response
    
    except Exception as e:
        print(f"خطا در ارتباط با OpenRouter: {str(e)}")
        return f"متأسفانه خطایی رخ داد: {str(e)}"

def get_bot_response_stream(conversation_messages, model="deepseek/deepseek-chat-v3-0324:free"):
    try:
        # استفاده از کلید API از سیستم مدیریت کلید
        api_key = get_openrouter_api_key()
        if not api_key:
            print("خطا: هیچ کلید API کارآمدی یافت نشد")
            yield "متأسفانه در حال حاضر به دلیل مشکل API قادر به پاسخگویی نیستم. لطفاً بعداً دوباره تلاش کنید."
            return
            
        print("ارسال درخواست به OpenRouter برای پاسخ جریانی...")
        
        # درخواست جریانی
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://localhost:5000/chat",
                "X-Title": "LLM Persian Bot"
            },
            json={
                "model": model,
                "messages": conversation_messages,
                "stream": True
            },
            stream=True,
            timeout=60
        )
        
        # بررسی وضعیت پاسخ
        if response.status_code != 200:
            error_message = f"خطا از OpenRouter: کد وضعیت {response.status_code}"
            
            # بررسی محدودیت نرخ درخواست
            if response.status_code == 429:
                # علامت‌گذاری کلید به عنوان ناکارآمد
                mark_api_key_failed(api_key)
                
                # پیام خطای مناسب
                error_json = response.json()
                error_detail = error_json.get('error', {}).get('message', 'محدودیت نرخ درخواست')
                
                if 'rate limit' in str(error_detail).lower():
                    error_message = "محدودیت نرخ درخواست OpenRouter. در حال تعویض به کلید API دیگر..."
                    
                    # تلاش مجدد با کلید جدید
                    print("تلاش مجدد با کلید جدید برای جریان...")
                    for chunk in get_bot_response_stream(conversation_messages, model):
                        yield chunk
                    return
            
            print(error_message)
            yield f"خطا در دریافت پاسخ: {error_message}"
            return
            
        # Function to generate streaming content
        def generate_stream():
            accumulated_message = ""
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    
                    # Remove the "data: " prefix
                    if line_text.startswith('data: '):
                        line_text = line_text[6:]
                    
                    # Check for the end of the stream
                    if line_text == '[DONE]':
                        break
                    
                    try:
                        line_json = json.loads(line_text)
                        if 'choices' in line_json and len(line_json['choices']) > 0:
                            choice = line_json['choices'][0]
                            if 'delta' in choice and 'content' in choice['delta']:
                                content = choice['delta']['content']
                                accumulated_message += content
                                yield content
                    except json.JSONDecodeError:
                        print(f"خطا در تجزیه JSON: {line_text}")
            
            # ذخیره کل پیام برای بازیابی بعدی
            return accumulated_message
            
        return generate_stream()
    
    except Exception as e:
        print(f"خطا در ارتباط با OpenRouter: {str(e)}")
        yield f"متأسفانه خطایی رخ داد: {str(e)}"

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    oauth_provider = db.Column(db.String(20))
    oauth_id = db.Column(db.String(100))
    conversations = db.relationship('Conversation', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Conversation(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversation.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'files[]' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})

    files = request.files.getlist('files[]')
    uploaded_files = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            uploaded_files.append({
                'name': filename,
                'url': url_for('uploaded_file', filename=unique_filename),
                'type': file.content_type
            })

    return jsonify({
        'success': True,
        'files': uploaded_files
    })

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/web-search', methods=['POST'])
@login_required
def web_search():
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({'error': 'No query provided'})

    try:
        # Call the web search function
        response = perform_web_search(query)
        return jsonify({'results': response})
    except Exception as e:
        return jsonify({'error': str(e)})

def perform_web_search(query):
    try:
        # Format the query for the AI to perform web search
        messages = [
            SYSTEM_MESSAGE,
            {"role": "user", "content": f"Please search the web for: {query} and return the results in Persian. Include the most important and recent information. Include relevant sources/URLs at the end of each paragraph or section."}
        ]

        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://github.com/OpenRouterAI/openrouter.py",
                "X-Title": "Persian AI Assistant",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat-v3-0324:free",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
        )

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return "متأسفانه در جستجوی وب مشکلی پیش آمد. لطفاً دوباره تلاش کنید."

    except Exception as e:
        print(f"Error in web search: {str(e)}")
        return "متأسفانه در جستجوی وب مشکلی پیش آمد. لطفاً دوباره تلاش کنید."

@app.route('/login/google')
def google_login():
    # Find out what URL to hit for Google login
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = google_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=GOOGLE_CALLBACK_URL,
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route('/login/google/callback')
def google_callback():
    try:
        # Get authorization code Google sent back to you
        code = request.args.get("code")
        if not code:
            flash("No authorization code received from Google.")
            return redirect(url_for('login'))

        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send request to get tokens
        token_url, headers, body = google_client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=GOOGLE_CALLBACK_URL,
            code=code,
        )
        
        # Log debugging information
        print(f"Token URL: {token_url}")
        print(f"Headers: {headers}")
        print(f"Body: {body}")
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens
        google_client.parse_request_body_response(json.dumps(token_response.json()))

        # Get user info from Google
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = google_client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        # Debugging information
        print(f"User info response: {userinfo_response.json()}")

        if userinfo_response.json().get("email_verified"):
            unique_id = userinfo_response.json()["sub"]
            users_email = userinfo_response.json()["email"]
            users_name = userinfo_response.json().get("given_name", users_email.split('@')[0])

            # Check if user exists
            user = User.query.filter_by(oauth_id=unique_id, oauth_provider='google').first()
            if not user:
                user = User(
                    username=users_name,
                    email=users_email,
                    oauth_provider='google',
                    oauth_id=unique_id
                )
                db.session.add(user)
                db.session.commit()

            login_user(user)
            return redirect(url_for('chat'))
        else:
            flash("Google authentication failed: Email not verified")
            return redirect(url_for('login'))
            
    except Exception as e:
        print(f"Error in Google callback: {str(e)}")
        flash(f"خطا در ورود با گوگل: {str(e)}")
        return redirect(url_for('login'))

@app.route('/login/github')
def github_login():
    # Update the GitHub authorization URL to include the correct redirect URI
    # that matches what's configured in the GitHub OAuth App settings
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={GITHUB_CALLBACK_URL}&scope=user:email"
    return redirect(github_auth_url)

@app.route('/login/github/callback')
def github_callback():
    code = request.args.get('code')
    
    # Exchange code for access token
    response = requests.post(
        'https://github.com/login/oauth/access_token',
        data={
            'client_id': GITHUB_CLIENT_ID,
            'client_secret': GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': GITHUB_CALLBACK_URL  # Add redirect_uri to match the one used in authorize request
        },
        headers={'Accept': 'application/json'}
    )
    
    access_token = response.json().get('access_token')
    
    # Get user info from GitHub
    response = requests.get(
        'https://api.github.com/user',
        headers={
            'Authorization': f'token {access_token}',
            'Accept': 'application/json'
        }
    )
    
    if response.ok:
        github_user = response.json()
        
        # Get user's email
        emails_response = requests.get(
            'https://api.github.com/user/emails',
            headers={
                'Authorization': f'token {access_token}',
                'Accept': 'application/json'
            }
        )
        
        primary_email = next(
            (email['email'] for email in emails_response.json() if email['primary']),
            github_user.get('email')
        )
        
        if not primary_email:
            flash('Could not get email from GitHub')
            return redirect(url_for('login'))
        
        # Check if user exists
        user = User.query.filter_by(oauth_id=str(github_user['id']), oauth_provider='github').first()
        if not user:
            user = User(
                username=github_user['login'],
                email=primary_email,
                oauth_provider='github',
                oauth_id=str(github_user['id'])
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect(url_for('chat'))
    
    flash('GitHub authentication failed')
    return redirect(url_for('login'))

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))

    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash('این ایمیل قبلاً ثبت شده است.')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('این نام کاربری قبلاً استفاده شده است.')
            return redirect(url_for('register'))

        user = User(email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('chat'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))

    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('chat'))
        flash('ایمیل یا رمز عبور اشتباه است.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat')
@app.route('/chat/<conversation_id>')
@login_required
def chat(conversation_id=None):
    # Get all conversations for the current user
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.created_at.desc()).all()
    
    # Add message count and last message to each conversation
    for conv in conversations:
        messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at).all()
        conv.message_count = len(messages)
        conv.last_message = messages[-1].content[:50] + '...' if messages else ''
    
    if conversation_id:
        # Get current conversation and its messages
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()
        messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
        
        # Ensure we store raw markdown and don't escape special characters
        for message in messages:
            # Make sure we're not converting < and > to &lt; and &gt;
            if '&lt;' in message.content:
                message.content = message.content.replace('&lt;', '<').replace('&gt;', '>')
    else:
        # If no conversation is selected, use the most recent one
        conversation = conversations[0] if conversations else None
        if conversation:
            messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
            
            # Apply the same processing to messages
            for message in messages:
                if '&lt;' in message.content:
                    message.content = message.content.replace('&lt;', '<').replace('&gt;', '>')
                    
            conversation_id = conversation.id
        else:
            messages = []

    return render_template('chat.html', 
                         conversations=conversations,
                         messages=messages,
                         current_conversation_id=conversation_id if conversation else None)

@app.route('/api/conversation', methods=['POST'])
@login_required
def create_conversation():
    data = request.get_json()
    conversation_id = str(uuid.uuid4())
    
    conversation = Conversation(
        id=conversation_id,
        title=data.get('title', 'گفتگوی جدید'),
        user_id=current_user.id
    )
    
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify({'id': conversation_id})

@app.route('/api/conversation/<conversation_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_conversation(conversation_id):
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'PUT':
        data = request.get_json()
        conversation.title = data.get('title', conversation.title)
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(conversation)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/message', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        conversation_id = data.get('conversation_id', '')
        model = data.get('model', 'deepseek/deepseek-chat-v3-0324:free')
        
        # اگر پیام تست باشد، آن را نادیده بگیریم
        if user_message.lower() == 'test':
            return jsonify({
                'success': True,
                'message': '',
                'conversation_id': conversation_id
            })
        
        print(f"Received message for conversation {conversation_id}: {user_message[:50]}...")
        
        if not user_message:
            return jsonify({'success': False, 'message': 'پیامی ارسال نشده است'}), 400
        
        if not conversation_id:
            # ایجاد مکالمه جدید
            conversation_title = user_message[:50] + '...' if len(user_message) > 50 else user_message
            new_conversation = Conversation(
                id=str(uuid.uuid4()),
                title=conversation_title,
                user_id=current_user.id
            )
            db.session.add(new_conversation)
            db.session.commit()
            conversation_id = new_conversation.id
        
        # دریافت مکالمه
        conversation = Conversation.query.filter_by(id=conversation_id).first()
        if not conversation:
            return jsonify({'success': False, 'message': 'مکالمه یافت نشد'}), 404
        
        # افزودن پیام کاربر
        user_message_db = Message(
            content=user_message,
            role='user',
            conversation_id=conversation_id
        )
        db.session.add(user_message_db)
        db.session.commit()
        
        # دریافت تمام پیام‌های مکالمه برای ارسال به OpenRouter
        all_messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
        conversation_messages = []
        for message in all_messages:
            conversation_messages.append({
                'role': message.role,
                'content': message.content
            })
        
        print(f"Sending {len(conversation_messages)} messages to OpenRouter using model: {model}")
        
        try:
            # دریافت پاسخ از بات
            bot_response = get_bot_response(conversation_messages, model)
            
            # ذخیره پاسخ در پایگاه داده
            bot_message = Message(
                content=bot_response,
                role='assistant',
                conversation_id=conversation_id
            )
            db.session.add(bot_message)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': bot_response,
                'conversation_id': conversation_id
            })
            
        except requests.exceptions.HTTPError as http_err:
            error_response = http_err.response
            status_code = error_response.status_code
            print(f"HTTP Error: {status_code}, {error_response.text[:200]}")
            
            error_json = {}
            try:
                error_json = error_response.json()
            except:
                pass
            
            # مدیریت انواع خطاها
            if status_code == 401:
                # کلید API نامعتبر
                error_message = "خطای احراز هویت. کلید API شما معتبر نیست."
                bot_response = """
# ⚠️ خطای کلید API

کلید API شما برای OpenRouter نامعتبر است یا منقضی شده است.

## راه‌حل
لطفاً یک کلید API معتبر جدید از [وبسایت OpenRouter](https://openrouter.ai/keys) دریافت کنید و آن را در فایل `.env` قرار دهید.
"""
            elif status_code == 429:
                error_message = error_json.get('error', {}).get('message', '')
                
                # اطلاعات محدودیت
                limit = error_response.headers.get('X-RateLimit-Limit', 'نامشخص')
                remaining = error_response.headers.get('X-RateLimit-Remaining', '0')
                reset_time = error_response.headers.get('X-RateLimit-Reset', '')
                
                if 'free-models-per-day' in error_message:
                    bot_response = f"""
# ⚠️ محدودیت استفاده از API
متأسفانه محدودیت استفاده روزانه از مدل‌های رایگان OpenRouter به پایان رسیده است.

## گزینه‌های موجود:
1. **صبر کنید**: محدودیت استفاده در روز بعد ریست می‌شود.
2. **تهیه اشتراک**: با تهیه اشتراک پولی از [وبسایت OpenRouter](https://openrouter.ai/account) می‌توانید از محدودیت استفاده عبور کنید.
3. **کلید API جدید**: یک کلید API جدید از [صفحه کلیدها](https://openrouter.ai/keys) دریافت کنید.

## جزئیات فنی
- محدودیت درخواست: {limit}
- درخواست‌های باقیمانده: {remaining}
"""
                elif 'rate_limit' in error_message or 'rate limit' in error_message.lower():
                    bot_response = f"""
# ⚠️ محدودیت نرخ درخواست
متأسفانه سرعت درخواست‌های شما به OpenRouter بیش از حد مجاز است.

## گزینه‌های موجود:
1. **صبر کنید**: لطفاً چند دقیقه صبر کنید و دوباره امتحان کنید.
2. **تهیه اشتراک**: با تهیه اشتراک پولی از [وبسایت OpenRouter](https://openrouter.ai/account) می‌توانید از محدودیت نرخ درخواست بالاتری برخوردار شوید.

## جزئیات فنی
- محدودیت درخواست: {limit}
- درخواست‌های باقیمانده: {remaining}
"""
                else:
                    bot_response = f"""
# ⚠️ محدودیت API
متأسفانه شما به محدودیت API در OpenRouter رسیده‌اید: {error_message}

## پیشنهادات:
1. **صبر کنید** و چند دقیقه دیگر دوباره امتحان کنید.
2. **کلید API جدید**: یک کلید API جدید از [صفحه کلیدها](https://openrouter.ai/keys) دریافت کنید.
3. **تهیه اشتراک**: با تهیه اشتراک پولی از [وبسایت OpenRouter](https://openrouter.ai/account) می‌توانید از محدودیت‌های بیشتری برخوردار شوید.
"""
            
            elif status_code == 402:
                # نیاز به پرداخت دارد
                error_message = "اعتبار شما در OpenRouter به پایان رسیده است. لطفاً حساب خود را شارژ کنید."
                bot_response = """
# ⚠️ نیاز به پرداخت

اعتبار شما در OpenRouter به پایان رسیده است.

## راه‌حل
لطفاً به [وبسایت OpenRouter](https://openrouter.ai/account) مراجعه کنید و حساب خود را شارژ نمایید.
"""
            else:
                # سایر خطاها
                error_message = error_json.get('error', {}).get('message', f'خطای ناشناخته: {status_code}')
                bot_response = f"""
# ⚠️ خطا در ارتباط با OpenRouter

متأسفانه در ارتباط با سرویس OpenRouter خطایی رخ داده است:
{error_message}

## راه‌حل
- لطفاً چند دقیقه صبر کنید و دوباره امتحان کنید.
- اگر مشکل همچنان ادامه داشت، میتوانید یک کلید API جدید از [صفحه کلیدها](https://openrouter.ai/keys) دریافت کنید.
"""
            
            # ذخیره پیام خطا در پایگاه داده
            error_bot_message = Message(
                content=bot_response,
                role='assistant',
                conversation_id=conversation_id
            )
            db.session.add(error_bot_message)
            db.session.commit()
            
            return jsonify({
                'success': True,  # همچنان موفقیت‌آمیز در نظر بگیریم تا در رابط کاربری پیام خطا نمایش داده شود
                'message': bot_response,
                'conversation_id': conversation_id,
                'error': error_message,
                'status_code': status_code
            })
            
        except Exception as e:
            print(f"Error in send_message: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'خطا در پاسخ‌دهی: {str(e)}'
            }), 500
    
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'خطا در پردازش پیام: {str(e)}'
        }), 500

@app.route('/api/message/stream', methods=['POST'])
@login_required
def send_message_stream():
    data = request.get_json()
    user_message = data.get('message')
    conversation_id = data.get('conversation_id')
    model = data.get('model', 'deepseek/deepseek-chat-v3-0324:free')  # مدل پیش‌فرض اگر تعیین نشده باشد

    if not user_message:
        return Response("data: متن پیام خالی است\n\n", mimetype='text/event-stream')

    if not conversation_id:
        # Create new conversation
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            title=user_message[:50] + '...' if len(user_message) > 50 else user_message,
            user_id=current_user.id
        )
        db.session.add(conversation)
        db.session.commit()
    else:
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()

    # Add user message to database
    user_msg = Message(
        content=user_message,
        role='user',
        conversation_id=conversation_id
    )
    db.session.add(user_msg)
    db.session.commit()

    # Get conversation history for context
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
    conversation_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
    
    # Create a placeholder for the bot message
    bot_msg = Message(
        content="",
        role='assistant',
        conversation_id=conversation_id
    )
    db.session.add(bot_msg)
    db.session.commit()
    bot_msg_id = bot_msg.id
    
    # Stream the response and update the bot message in the database when complete
    def generate():
        collected_response = ""
        # Send conversation ID at the beginning
        yield f"data: CONVERSATION_ID:{conversation_id}\n\n"
        
        # Stream message content from OpenRouter API with specified model
        try:
            for chunk in get_bot_response_stream(conversation_messages, model=model):
                if chunk.startswith('data: '):
                    content = chunk[6:].strip()
                    collected_response += content
                    # Periodically update the bot message in the database
                    if len(collected_response) % 50 == 0:
                        bot_msg = Message.query.get(bot_msg_id)
                        if bot_msg:
                            bot_msg.content = collected_response
                            db.session.commit()
                    yield chunk
        except Exception as e:
            print(f"Error in streaming response: {str(e)}")
            error_msg = "متأسفانه در پردازش پیام شما مشکلی پیش آمد."
            yield f"data: {error_msg}\n\n"
        
        # Update the bot message with the complete response at the end
        try:
            bot_msg = Message.query.get(bot_msg_id)
            if bot_msg:
                bot_msg.content = collected_response
                db.session.commit()
        except Exception as e:
            print(f"Error updating bot message in database: {str(e)}")
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/shared/<conversation_id>')
def shared_conversation(conversation_id):
    """
    نمایش یک گفتگو به صورت عمومی با لینک اشتراک‌گذاری شده
    """
    # بررسی اینکه آیا گفتگو وجود دارد
    conversation = Conversation.query.filter_by(id=conversation_id).first_or_404()
    
    # دریافت پیام‌های گفتگو
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
    
    # اطمینان از اینکه فرمت مارک‌داون حفظ شود
    for message in messages:
        # حصول اطمینان از تبدیل نشدن کاراکترهای خاص به entities در HTML
        if '&lt;' in message.content:
            message.content = message.content.replace('&lt;', '<').replace('&gt;', '>')
    
    # ارسال به قالب با نشانگر اینکه این یک گفتگوی به اشتراک گذاشته شده است
    return render_template(
        'shared.html',
        conversation=conversation,
        messages=messages,
        is_shared=True
    )

@app.route('/download/<conversation_id>/<format>')
@login_required
def download_conversation(conversation_id, format):
    """
    دانلود گفتگو به فرمت‌های مختلف
    فرمت‌های پشتیبانی شده: txt, md, json, html
    """
    # بررسی دسترسی کاربر به گفتگو
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()
    
    # دریافت پیام‌های گفتگو
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
    
    # نام فایل بر اساس عنوان گفتگو
    filename = secure_filename(f"{conversation.title}_{datetime.now().strftime('%Y%m%d')}")
    
    if format == 'txt':
        # فرمت متن ساده
        content = f"عنوان: {conversation.title}\n"
        content += f"تاریخ: {conversation.created_at.strftime('%Y/%m/%d')}\n\n"
        
        for msg in messages:
            speaker = "شما" if msg.role == 'user' else "دستیار"
            content += f"[{speaker}] {msg.created_at.strftime('%H:%M:%S')}\n"
            content += f"{msg.content}\n\n"
        
        response = Response(content, mimetype='text/plain; charset=utf-8')
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.txt'
        return response
        
    elif format == 'md':
        # فرمت مارک‌داون
        content = f"# {conversation.title}\n\n"
        content += f"*تاریخ: {conversation.created_at.strftime('%Y/%m/%d')}*\n\n"
        
        for msg in messages:
            speaker = "شما" if msg.role == 'user' else "دستیار"
            content += f"## {speaker} ({msg.created_at.strftime('%H:%M:%S')})\n\n"
            content += f"{msg.content}\n\n"
        
        response = Response(content, mimetype='text/markdown; charset=utf-8')
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.md'
        return response
        
    elif format == 'json':
        # فرمت JSON
        data = {
            'title': conversation.title,
            'created_at': conversation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'messages': []
        }
        
        for msg in messages:
            data['messages'].append({
                'role': msg.role,
                'content': msg.content,
                'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        response = Response(json.dumps(data, ensure_ascii=False, indent=2), 
                           mimetype='application/json; charset=utf-8')
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.json'
        return response
        
    elif format == 'html':
        # فرمت HTML
        html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{conversation.title}</title>
    <style>
        body {{ font-family: Vazirmatn, Tahoma, sans-serif; direction: rtl; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #4a6bdf; text-align: center; }}
        .meta {{ text-align: center; color: #666; margin-bottom: 30px; }}
        .message {{ margin-bottom: 20px; padding: 15px; border-radius: 10px; }}
        .user {{ background-color: #f0f7ff; border-right: 3px solid #4a6bdf; }}
        .assistant {{ background-color: #f5f5f5; border-right: 3px solid #777; }}
        .speaker {{ font-weight: bold; margin-bottom: 5px; }}
        .time {{ color: #999; font-size: 0.8em; }}
        pre {{ background: #f8f8f8; padding: 10px; border-radius: 5px; overflow-x: auto; direction: ltr; }}
        code {{ font-family: monospace; }}
    </style>
</head>
<body>
    <h1>{conversation.title}</h1>
    <div class="meta">تاریخ: {conversation.created_at.strftime('%Y/%m/%d')}</div>
    
    <div class="conversation">
"""
        
        for msg in messages:
            role_class = "user" if msg.role == 'user' else "assistant"
            speaker = "شما" if msg.role == 'user' else "دستیار"
            
            html += f"""
        <div class="message {role_class}">
            <div class="speaker">{speaker} <span class="time">{msg.created_at.strftime('%H:%M:%S')}</span></div>
            <div class="content">{msg.content}</div>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        response = Response(html, mimetype='text/html; charset=utf-8')
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.html'
        return response
    
    else:
        # فرمت نامعتبر
        flash('فرمت درخواستی معتبر نیست.')
        return redirect(url_for('chat', conversation_id=conversation_id))

# مسیر API ساده برای تست
@app.route('/api/test', methods=['GET', 'POST'])
def api_test():
    print("=== /api/test endpoint called ===")
    if request.method == 'POST':
        try:
            data = request.get_json()
            print(f"Received test data: {data}")
            return jsonify({
                'success': True,
                'echo': data,
                'message': 'API test successful!'
            })
        except Exception as e:
            print(f"Error in api_test: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    else:
        return jsonify({
            'success': True,
            'message': 'API test endpoint is working!'
        })

# تست ساده API OpenRouter
@app.route('/api/test-openrouter')
def test_openrouter():
    """تست ارتباط با OpenRouter"""
    # از OPENROUTER_API_KEY فعلی استفاده می‌کنیم
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        return jsonify({
            'success': False,
            'message': 'کلید API برای OpenRouter تنظیم نشده است'
        })
    
    # تست ارسال یک درخواست ساده به API
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/auth/key",
            headers={
                "Authorization": f"Bearer {api_key}"
            }
        )
        
        if response.status_code == 200:
            # جزئیات کلید و وضعیت آن
            key_info = response.json()
            return jsonify({
                'success': True,
                'message': 'ارتباط با OpenRouter با موفقیت برقرار شد',
                'key_info': key_info
            })
        else:
            error_info = response.json() if response.text else {"error": "بدون پیام خطا"}
            return jsonify({
                'success': False,
                'status_code': response.status_code,
                'message': f'خطا در ارتباط با OpenRouter: {response.status_code}',
                'error_details': error_info
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطا در برقراری ارتباط: {str(e)}'
        })

@app.route('/api/test-new-key', methods=['POST'])
def test_new_api_key():
    print("=== Testing new OpenRouter API key ===")
    try:
        # دریافت کلید API جدید از درخواست
        data = request.get_json()
        new_api_key = data.get('api_key', '')
        
        if not new_api_key:
            return jsonify({
                'success': False,
                'message': 'کلید API ارسال نشده است'
            }), 400
        
        # نمایش کلید API جدید (با حفظ امنیت)
        key_preview = new_api_key[:5] + "..." + new_api_key[-5:] if new_api_key else "نامعتبر"
        print(f"Testing new API key: {key_preview}")
        
        # ارسال یک درخواست ساده به OpenRouter با کلید جدید
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {new_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat-v3-0324:free",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            },
            timeout=10
        )
        
        # بررسی پاسخ
        status_code = response.status_code
        headers = dict(response.headers)
        rate_limit = headers.get('X-RateLimit-Limit', 'نامشخص')
        rate_remaining = headers.get('X-RateLimit-Remaining', 'نامشخص')
        rate_reset = headers.get('X-RateLimit-Reset', 'نامشخص')
        
        # اطلاعات اضافی
        response_preview = response.text[:500] + "..." if len(response.text) > 500 else response.text
        response_json = response.json() if response.text and response.headers.get('Content-Type', '').startswith('application/json') else {}
        
        if status_code == 200:
            print(f"✓ ارتباط با OpenRouter با کلید جدید موفقیت‌آمیز بود (کد {status_code})")
            print(f"- محدودیت: {rate_limit}")
            print(f"- باقیمانده: {rate_remaining}")
            return jsonify({
                'success': True,
                'message': 'ارتباط با OpenRouter با کلید جدید موفقیت‌آمیز بود',
                'status_code': status_code,
                'api_key': key_preview,
                'headers': {
                    'X-RateLimit-Limit': rate_limit,
                    'X-RateLimit-Remaining': rate_remaining,
                    'X-RateLimit-Reset': rate_reset
                },
                'rate_limit_info': {
                    'limit': rate_limit,
                    'remaining': rate_remaining,
                    'reset': rate_reset
                },
                'compared_to_current': {
                    'is_different_key': new_api_key != OPENROUTER_API_KEY,
                    'current_key_preview': OPENROUTER_API_KEY[:5] + "..." + OPENROUTER_API_KEY[-5:] if OPENROUTER_API_KEY else "نامشخص"
                }
            })
        elif status_code == 429:
            error_message = response_json.get('error', {}).get('message', 'محدودیت نرخ درخواست') if isinstance(response_json, dict) else 'محدودیت نرخ درخواست'
            print(f"✗ خطای محدودیت نرخ درخواست با کلید جدید (کد {status_code}): {error_message}")
            print(f"- محدودیت: {rate_limit}")
            print(f"- باقیمانده: {rate_remaining}")
            
            return jsonify({
                'success': False,
                'message': f'محدودیت نرخ درخواست با کلید جدید: {error_message}',
                'status_code': status_code,
                'api_key': key_preview,
                'headers': {
                    'X-RateLimit-Limit': rate_limit,
                    'X-RateLimit-Remaining': rate_remaining,
                    'X-RateLimit-Reset': rate_reset
                },
                'error': error_message,
                'response_preview': str(response_json),
                'compared_to_current': {
                    'is_different_key': new_api_key != OPENROUTER_API_KEY,
                    'current_key_preview': OPENROUTER_API_KEY[:5] + "..." + OPENROUTER_API_KEY[-5:] if OPENROUTER_API_KEY else "نامشخص"
                }
            }), 429
        else:
            error_message = response_json.get('error', {}).get('message', f'خطای نامشخص (کد {status_code})') if isinstance(response_json, dict) else f'خطای نامشخص (کد {status_code})'
            print(f"✗ خطا در ارتباط با OpenRouter با کلید جدید (کد {status_code}): {error_message}")
            
            return jsonify({
                'success': False,
                'message': f'خطا در ارتباط با OpenRouter با کلید جدید: {error_message}',
                'status_code': status_code,
                'api_key': key_preview,
                'headers': {
                    'X-RateLimit-Limit': rate_limit,
                    'X-RateLimit-Remaining': rate_remaining,
                    'X-RateLimit-Reset': rate_reset
                },
                'error': error_message,
                'response_preview': str(response_json),
                'compared_to_current': {
                    'is_different_key': new_api_key != OPENROUTER_API_KEY,
                    'current_key_preview': OPENROUTER_API_KEY[:5] + "..." + OPENROUTER_API_KEY[-5:] if OPENROUTER_API_KEY else "نامشخص"
                }
            }), status_code
            
    except Exception as e:
        print(f"✗ خطا در تست کلید API جدید: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'خطا در تست کلید API جدید: {str(e)}',
            'error': str(e)
        }), 500

@app.route('/api/update-api-key', methods=['POST'])
def update_api_key():
    print("=== Updating OpenRouter API key ===")
    try:
        # دریافت کلید API جدید از درخواست
        data = request.get_json()
        new_api_key = data.get('api_key', '')
        
        if not new_api_key:
            return jsonify({
                'success': False,
                'message': 'کلید API ارسال نشده است'
            }), 400
        
        # نمایش کلیدهای قبلی و جدید (با حفظ امنیت)
        old_key_preview = OPENROUTER_API_KEY[:5] + "..." + OPENROUTER_API_KEY[-5:] if OPENROUTER_API_KEY else "تنظیم نشده"
        new_key_preview = new_api_key[:5] + "..." + new_api_key[-5:] if new_api_key else "نامعتبر"
        print(f"Updating API key from {old_key_preview} to {new_key_preview}")
        
        # به‌روزرسانی کلید API در متغیر محیطی
        # در این نسخه از اعلان global استفاده نمی‌کنیم و فقط مقدار را عوض می‌کنیم
        os.environ['OPENROUTER_API_KEY'] = new_api_key
        
        # تست کلید جدید با کلید جدید از متغیر محیطی
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {new_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat-v3-0324:free",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            },
            timeout=10
        )
        
        # بررسی پاسخ
        status_code = response.status_code
        headers = dict(response.headers)
        rate_limit = headers.get('X-RateLimit-Limit', 'نامشخص')
        rate_remaining = headers.get('X-RateLimit-Remaining', 'نامشخص')
        rate_reset = headers.get('X-RateLimit-Reset', 'نامشخص')
        
        # اطلاعات اضافی
        response_json = response.json() if response.text and response.headers.get('Content-Type', '').startswith('application/json') else {}
        
        if status_code == 200:
            print(f"✓ کلید API با موفقیت به‌روز شد و ارتباط با OpenRouter برقرار است")
            print(f"- محدودیت: {rate_limit}")
            print(f"- باقیمانده: {rate_remaining}")
            return jsonify({
                'success': True,
                'message': 'کلید API با موفقیت به‌روز شد و ارتباط با OpenRouter برقرار است',
                'old_key': old_key_preview,
                'new_key': new_key_preview,
                'headers': {
                    'X-RateLimit-Limit': rate_limit,
                    'X-RateLimit-Remaining': rate_remaining,
                    'X-RateLimit-Reset': rate_reset
                }
            })
        else:
            # در صورت خطا، کلید قبلی را بازگردانیم
            error_message = response_json.get('error', {}).get('message', f'خطای نامشخص (کد {status_code})') if isinstance(response_json, dict) else f'خطای نامشخص (کد {status_code})'
            print(f"✗ خطا در اتصال با کلید جدید: {error_message}")
            
            # اگر خطای 429 بود، همچنان کلید را به‌روز کنیم (ممکن است محدودیت حساب باشد)
            if status_code == 429:
                return jsonify({
                    'success': True,  # همچنان موفقیت‌آمیز در نظر بگیریم
                    'warning': True,
                    'message': f'کلید API به‌روز شد اما محدودیت نرخ درخواست وجود دارد: {error_message}',
                    'old_key': old_key_preview,
                    'new_key': new_key_preview,
                    'headers': {
                        'X-RateLimit-Limit': rate_limit,
                        'X-RateLimit-Remaining': rate_remaining,
                        'X-RateLimit-Reset': rate_reset
                    },
                    'error': error_message
                })
            
            return jsonify({
                'success': False,
                'message': f'خطا در ارتباط با OpenRouter با کلید جدید: {error_message}',
                'old_key': old_key_preview,
                'new_key': new_key_preview,
                'headers': {
                    'X-RateLimit-Limit': rate_limit,
                    'X-RateLimit-Remaining': rate_remaining,
                    'X-RateLimit-Reset': rate_reset
                },
                'error': error_message
            }), status_code
            
    except Exception as e:
        print(f"✗ خطا در به‌روزرسانی کلید API: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'خطا در به‌روزرسانی کلید API: {str(e)}',
            'error': str(e)
        }), 500

# سیستم مدیریت API کلیدها
class ApiKeyManager:
    def __init__(self):
        # کلید API اصلی از .env
        main_key = os.getenv('OPENROUTER_API_KEY')
        
        # لیست کلیدهای API (اضافه کردن کلیدهای بیشتر در اینجا)
        self.api_keys = [
            {"key": main_key, "uses": 0, "last_used": None, "max_daily": 100, "working": True},
            # کلیدهای اضافی را اینجا اضافه کنید
            # {"key": "sk-or-v1-کلید-دوم", "uses": 0, "last_used": None, "max_daily": 100, "working": True},
            # {"key": "sk-or-v1-کلید-سوم", "uses": 0, "last_used": None, "max_daily": 100, "working": True},
        ]
        
        # اگر فایل کلیدهای API وجود داشت، آن را بارگذاری می‌کنیم
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
    
    def get_stats(self):
        """گزارش وضعیت کلیدها"""
        today = datetime.now().date()
        stats = {
            "total_keys": len(self.api_keys),
            "working_keys": sum(1 for k in self.api_keys if k['working']),
            "unused_today": sum(1 for k in self.api_keys if k['last_used'] is None or k['last_used'].date() < today),
            "keys": []
        }
        
        for i, key in enumerate(self.api_keys):
            stats["keys"].append({
                "index": i,
                "preview": f"{key['key'][:8]}...",
                "uses": key['uses'],
                "max_daily": key['max_daily'],
                "working": key['working'],
                "last_used": key['last_used'].strftime("%Y-%m-%d %H:%M:%S") if key['last_used'] else None
            })
        
        return stats

# ایجاد مدیر کلیدهای API
api_key_manager = ApiKeyManager()

# استفاده‌کننده از مدیر API
def get_openrouter_api_key():
    return api_key_manager.get_next_key()

# تابع برای نشانه‌گذاری کلید ناکارآمد
def mark_api_key_failed(key):
    api_key_manager.mark_key_failed(key)

# اضافه کردن مسیر API برای مدیریت کلیدها
@app.route('/api/keys', methods=['GET', 'POST'])
@login_required
def manage_api_keys():
    if request.method == 'GET':
        # بازیابی اطلاعات کلیدها
        stats = api_key_manager.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    elif request.method == 'POST':
        # اضافه کردن کلید جدید
        data = request.get_json()
        new_key = data.get('api_key', '').strip()
        
        if not new_key:
            return jsonify({
                'success': False,
                'message': 'کلید API خالی است'
            }), 400
            
        success, message = api_key_manager.add_key(new_key)
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400

# اضافه کردن صفحه مدیریت کلیدها
@app.route('/admin/keys')
@login_required
def admin_keys():
    # این مسیر فقط برای مدیر در دسترس است
    if current_user.id != 1:  # فرض می‌کنیم کاربر 1 مدیر است
        flash('شما دسترسی به این صفحه را ندارید.', 'error')
        return redirect(url_for('chat'))
        
    return render_template('admin_keys.html')

# اضافه کردن context processor به app
@app.context_processor
def utility_processor():
    def is_admin():
        """بررسی اینکه آیا کاربر مدیر است یا خیر"""
        if not current_user.is_authenticated:
            return False
        return current_user.id == 1  # فرض می‌کنیم کاربر با آیدی 1 مدیر است
        
    return {
        'is_admin': is_admin
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
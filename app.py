from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory, Response, stream_with_context
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import requests
import uuid
from datetime import datetime
from oauthlib.oauth2 import WebApplicationClient
import json

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

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# OAuth clients
google_client = WebApplicationClient(GOOGLE_CLIENT_ID)

# System message for Persian AI Assistant
SYSTEM_MESSAGE = {
    "role": "system",
    "content": "You are a helpful Persian AI assistant. Please respond in Persian language. Be polite, friendly, and provide accurate information."
}

def get_bot_response(conversation_messages, model="deepseek/deepseek-chat-v3-0324:free"):
    try:
        # Ensure the system message is at the beginning
        messages = [SYSTEM_MESSAGE]
        
        # Add conversation history (limited to last 10 messages to avoid context length issues)
        messages.extend(conversation_messages[-10:])
        
        # Make API request to OpenRouter
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://github.com/OpenRouterAI/openrouter.py",
                "X-Title": "Persian AI Assistant",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": False # We'll add streaming in a separate function
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            bot_response = result['choices'][0]['message']['content']
            
            # Make sure special characters are not escaped when storing
            bot_response = bot_response.replace('&lt;', '<').replace('&gt;', '>')
            
            return bot_response
        else:
            print(f"API Error: {response.status_code}, {response.text}")
            return "متأسفانه در پردازش پیام شما مشکلی پیش آمد. لطفاً دوباره تلاش کنید."
    
    except Exception as e:
        print(f"Error in get_bot_response: {str(e)}")
        return "متأسفانه در پردازش پیام شما مشکلی پیش آمد. لطفاً دوباره تلاش کنید."

def get_bot_response_stream(conversation_messages, model="deepseek/deepseek-chat-v3-0324:free"):
    try:
        # Ensure the system message is at the beginning
        messages = [SYSTEM_MESSAGE]
        
        # Add conversation history (limited to last 10 messages to avoid context length issues)
        messages.extend(conversation_messages[-10:])
        
        # Make API request to OpenRouter with stream=True
        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://github.com/OpenRouterAI/openrouter.py",
                "X-Title": "Persian AI Assistant",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": True
            },
            stream=True
        )
        
        # Check if request was successful
        if response.status_code == 200:
            # Define a generator function to yield the response chunks
            def generate_stream():
                collected_response = ""
                for chunk in response.iter_lines():
                    if chunk:
                        # Skip the "data: " prefix
                        chunk_data = chunk.decode('utf-8')
                        if chunk_data.startswith('data: '):
                            chunk_data = chunk_data[6:]  # Remove "data: " prefix
                            
                            # Skip "[DONE]" message at the end
                            if chunk_data == "[DONE]":
                                continue
                                
                            try:
                                json_data = json.loads(chunk_data)
                                delta = json_data.get('choices', [{}])[0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    collected_response += content
                                    yield f"data: {content}\n\n"
                            except Exception as e:
                                print(f"Error parsing chunk: {e}")
                                
                return collected_response
            
            return generate_stream()
        else:
            error_msg = "متأسفانه در پردازش پیام شما مشکلی پیش آمد. لطفاً دوباره تلاش کنید."
            print(f"API Error: {response.status_code}, {response.text}")
            yield f"data: {error_msg}\n\n"
    
    except Exception as e:
        error_msg = "متأسفانه در پردازش پیام شما مشکلی پیش آمد. لطفاً دوباره تلاش کنید."
        print(f"Error in get_bot_response_stream: {str(e)}")
        yield f"data: {error_msg}\n\n"

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
            {"role": "user", "content": f"Please search the web for: {query}"}
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
                "model": "anthropic/claude-3-opus-20240229",
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
        redirect_uri=request.base_url + "/callback",
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
            redirect_url=request.base_url,
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
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={request.url_root}login/github/callback&scope=user:email"
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
            'redirect_uri': f"{request.url_root}login/github/callback"  # Add redirect_uri to match the one used in authorize request
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
    data = request.get_json()
    user_message = data.get('message')
    conversation_id = data.get('conversation_id')
    model = data.get('model', 'deepseek/deepseek-chat-v3-0324:free')  # مدل پیش‌فرض اگر تعیین نشده باشد

    if not conversation_id:
        # Create new conversation
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            title=user_message[:50] + '...' if len(user_message) > 50 else user_message,
            user_id=current_user.id
        )
        db.session.add(conversation)
    else:
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first_or_404()

    # Preserve markdown formatting in the raw message
    # No HTML escaping to keep asterisks, backticks, etc.
    # Add user message to database
    user_msg = Message(
        content=user_message,
        role='user',
        conversation_id=conversation_id
    )
    db.session.add(user_msg)

    # Get conversation history
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
    conversation_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

    # Get bot response with specified model
    bot_response = get_bot_response(conversation_messages, model=model)

    # Add bot message to database - preserve markdown formatting
    bot_msg = Message(
        content=bot_response,
        role='assistant',
        conversation_id=conversation_id
    )
    db.session.add(bot_msg)
    db.session.commit()

    return jsonify({
        'conversation_id': conversation_id,
        'bot_response': bot_response
    })

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
// Simple script for chat functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded - initializing basic chat functionality");
    
    // Get DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const thinkerToggle = document.getElementById('thinker-toggle'); // Model toggle button
    const typingIndicator = document.getElementById('typing-indicator');
    
    // Log for debugging
    console.log("Main elements found:", {
        chatMessages: !!chatMessages,
        userInput: !!userInput,
        sendButton: !!sendButton,
        thinkerToggle: !!thinkerToggle,
        typingIndicator: !!typingIndicator
    });
    
    // Initialize global state
    window.chatState = {
        isProcessing: false,
        currentModel: 'deepseek/deepseek-chat-v3-0324:free',
        currentConversationId: null
    };
    
    // Get conversation ID from URL if available
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length === 3 && pathParts[1] === 'chat') {
        window.chatState.currentConversationId = pathParts[2];
    }
    
    // بررسی loaded بودن کتابخانه‌های مورد نیاز
    if (!window.marked) {
        console.error("Marked library not loaded! Add the following to your HTML:");
        console.error('<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js"></script>');
    }
    
    if (!window.hljs) {
        console.warn("Highlight.js not loaded! Code highlighting will not work.");
    }
    
    if (!window.katex) {
        console.warn("KaTeX not loaded! Math formulas will not render.");
    }
    
    // بهبود نحوه تنظیم marked برای جلوگیری از خطا
    if (window.marked) {
        try {
            marked.setOptions({
                breaks: true,
                gfm: true,
                headerIds: true,
                pedantic: false,
                mangle: false,
                sanitize: false,
                silent: true
            });
            console.log("Marked.js configured successfully");
        } catch (e) {
            console.error("Error configuring marked:", e);
        }
    }
    
    // Process existing messages to apply markdown formatting
    refreshMessageFormatting();
    
    // Set up event listeners
    setupEventListeners();
    
    // Function to refresh markdown formatting for all messages
    function refreshMessageFormatting() {
        console.log("Refreshing message formatting");
        if (!chatMessages) return;
        
        // Find all message content divs
        const messageContents = document.querySelectorAll('.message-content.markdown-body');
        
        messageContents.forEach(contentDiv => {
            // Get original content from data attribute or inner HTML
            const originalContent = contentDiv.getAttribute('data-message-content') || contentDiv.innerHTML;
            
            // بررسی محتوای خالی
            if (!originalContent || originalContent.trim() === '') {
                console.warn("Empty content found while refreshing formatting");
                contentDiv.textContent = "محتوای پیام در دسترس نیست";
                return;
            }
            
            // Check if this is a Persian/Arabic text
            if (/[\u0600-\u06FF]/.test(originalContent)) {
                contentDiv.setAttribute('dir', 'rtl');
            }
            
            // Apply markdown if available
            if (window.marked) {
                try {
                    // Parse with marked - با بررسی خالی نبودن محتوا
                    contentDiv.innerHTML = marked.parse(originalContent);
                    
                    // Process code blocks
                    if (window.hljs) {
                        contentDiv.querySelectorAll('pre code').forEach((block) => {
                            hljs.highlightElement(block);
                        });
                        
                        // Add buttons to code blocks
                        addCodeButtons(contentDiv);
                    }
                    
                    // Process math formulas
                    processMathInElement(contentDiv);
                    
                    // Make links open in new tab
                    contentDiv.querySelectorAll('a').forEach(link => {
                        link.setAttribute('target', '_blank');
                        link.setAttribute('rel', 'noopener noreferrer');
                    });
                } catch (e) {
                    console.error("Error parsing markdown for message:", e);
                    contentDiv.textContent = originalContent;
                }
            }
        });
    }
    
    // Function to set up all event listeners
    function setupEventListeners() {
        // Send button click event
        if (sendButton) {
            console.log("Setting up send button");
            sendButton.addEventListener('click', function() {
                console.log("Send button clicked");
                sendMessage();
            });
        }
        
        // Model toggle button click event
        if (thinkerToggle) {
            console.log("Setting up model toggle button");
            thinkerToggle.addEventListener('click', function() {
                console.log("Model toggle button clicked");
                toggleModel();
            });
        }
        
        // Text input events
        if (userInput) {
            console.log("Setting up user input events");
            
            // Enter key to send, Shift+Enter for new line
            userInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    console.log("Enter key pressed - sending message");
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Auto-resize textarea and save to localStorage
            userInput.addEventListener('input', function() {
                // Save text to localStorage
                localStorage.setItem('current_message', this.value);
                
                // Auto-resize
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
            
            // Restore saved message from localStorage
            const savedMessage = localStorage.getItem('current_message');
            if (savedMessage) {
                userInput.value = savedMessage;
                
                // Trigger height adjustment
                userInput.style.height = 'auto';
                userInput.style.height = (userInput.scrollHeight) + 'px';
            }
        }
    }
    
    // Function to toggle between models
    function toggleModel() {
        const thinkerButton = document.getElementById('thinker-toggle');
        
        if (window.chatState.currentModel === 'deepseek/deepseek-chat-v3-0324:free') {
            window.chatState.currentModel = 'deepseek/deepseek-r1:free';
            alert('مدل زبانی به Deepseek R1 تغییر یافت');
            // فعال کردن ظاهر دکمه برای نشان دادن حالت روشن
            if (thinkerButton) {
                thinkerButton.classList.add('active');
            }
        } else {
            window.chatState.currentModel = 'deepseek/deepseek-chat-v3-0324:free';
            alert('مدل زبانی به Deepseek Chat V3 تغییر یافت');
            // غیرفعال کردن ظاهر دکمه برای نشان دادن حالت خاموش
            if (thinkerButton) {
                thinkerButton.classList.remove('active');
            }
        }
        console.log("Model changed to:", window.chatState.currentModel);
    }
    
    // تنظیم وضعیت اولیه دکمه بر اساس مدل پیش‌فرض
    if (thinkerToggle) {
        if (window.chatState.currentModel === 'deepseek/deepseek-r1:free') {
            thinkerToggle.classList.add('active');
        } else {
            thinkerToggle.classList.remove('active');
        }
    }
});

// Function to create and append a message
function createMessage(content, isUser = false) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) {
        console.error("Chat messages container not found");
        return null;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content markdown-body';
    
    // برای پیام‌های بات، اگر پیام در حال دریافت است، کلاس اضافی اضافه می‌کنیم
    if (!isUser && content === "در حال دریافت پاسخ...") {
        contentDiv.className += ' bot-thinking';
        contentDiv.innerHTML = `
            <div class="loading-bar-container">
                <div class="loading-bar"></div>
            </div>
        `;
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }
    
    // Check if content is RTL (Persian/Arabic text)
    if (content && /[\u0600-\u06FF]/.test(content)) {
        contentDiv.setAttribute('dir', 'rtl');
    }
    
    // ذخیره محتوای اصلی برای بازیابی بعدی
    if (content) {
        contentDiv.setAttribute('data-message-content', content);
    }
    
    // Parse markdown with marked.js if available
    if (window.marked && content) {
        try {
            // Set marked options for better Persian/Arabic text formatting
            marked.setOptions({
                breaks: true,          // Convert newlines to line breaks
                gfm: true,             // GitHub Flavored Markdown support
                headerIds: true,       // Add IDs to headers for linking
                pedantic: false,
                mangle: false,
                sanitize: false,
                silent: true
            });
            
            // Parse the content with marked - check for null/undefined
            if (content !== null && content !== undefined) {
                contentDiv.innerHTML = marked.parse(content);
                
                // Process code blocks with highlight.js if available
                if (window.hljs) {
                    contentDiv.querySelectorAll('pre code').forEach((block) => {
                        hljs.highlightElement(block);
                    });
                    
                    // Add copy and run buttons to code blocks
                    addCodeButtons(contentDiv);
                }
                
                // Process math formulas
                processMathInElement(contentDiv);
                
                // Make all links open in new tab
                contentDiv.querySelectorAll('a').forEach(link => {
                    link.setAttribute('target', '_blank');
                    link.setAttribute('rel', 'noopener noreferrer');
                });
                
                // اطمینان از استایل تمام پاراگراف‌ها
                contentDiv.querySelectorAll('p').forEach(p => {
                    p.style.whiteSpace = 'pre-wrap';
                    p.style.margin = '0.5em 0';
                });
            } else {
                console.warn("Attempted to parse null/undefined content with marked");
                contentDiv.textContent = "محتوای پیام در دسترس نیست";
            }
        } catch (e) {
            console.error("Error parsing markdown:", e);
            // Fallback to plain text in case of an error
            if (content) {
                contentDiv.textContent = content;
            } else {
                contentDiv.textContent = "محتوای پیام در دسترس نیست";
            }
        }
    } else {
        // If marked.js is not available or content is empty, display plain text
        if (content) {
            contentDiv.textContent = content;
        } else {
            contentDiv.textContent = "محتوای پیام در دسترس نیست";
        }
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

// Function to send a message - version with detailed debugging
async function sendMessage() {
    console.log("==== SEND MESSAGE FUNCTION STARTED ====");
    console.log("API Key: ", document.querySelector('meta[name="api-status"]')?.getAttribute('content') || 'No status meta tag found');
    
    try {
        // ابتدا یک تست ساده انجام دهیم تا مطمئن شویم سرور در حال پاسخ دادن است
        console.log("Running quick server test...");
        const testResponse = await fetch('/api/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                test: true,
                message: "Test message"
            })
        });
        
        if (!testResponse.ok) {
            console.error("Test API failed! Status:", testResponse.status);
        } else {
            const testData = await testResponse.json();
            console.log("Test API success:", testData);
        }
    } catch (e) {
        console.error("Could not complete basic API test:", e);
    }
    
    // Get required elements
    const userInput = document.getElementById('user-input');
    const typingIndicator = document.getElementById('typing-indicator');
    const chatMessages = document.getElementById('chat-messages');
    
    if (!userInput || !typingIndicator || !chatMessages) {
        console.error("Required elements not found:", {
            userInput: !!userInput,
            typingIndicator: !!typingIndicator,
            chatMessages: !!chatMessages
        });
        alert("خطای فنی: المان‌های مورد نیاز یافت نشد");
        return;
    }
    
    // Check if already processing a message
    if (window.chatState.isProcessing) {
        console.log("Already processing a message, ignoring request");
        return;
    }
    
    // Get and validate message text
    const message = userInput.value.trim();
    if (!message) {
        console.log("Message is empty, not sending");
        return;
    }
    
    console.log("Sending message:", message.substring(0, 30) + (message.length > 30 ? "..." : ""));
    
    // Clear input and localStorage
    userInput.value = '';
    userInput.style.height = 'auto';
    localStorage.removeItem('current_message');
    
    // Show user message
    createMessage(message, true);
    
    // Set processing state
    window.chatState.isProcessing = true;
    
    // Show typing indicator
    typingIndicator.style.display = 'flex';
    
    try {
        // Create a placeholder for the bot response that will get updated
        const botMessage = createMessage("در حال دریافت پاسخ...", false);
        
        // SIMPLE VERSION: First try non-streaming endpoint with minimal processing
        try {
            console.log("Attempting to send request to API");
            
            // Prepare request data
            const requestData = {
                message: message,
                conversation_id: window.chatState.currentConversationId,
                model: window.chatState.currentModel
            };
            
            console.log("Request data:", requestData);
            console.log("Current URL:", window.location.href);
            console.log("Headers being sent:", {
                'Content-Type': 'application/json'
            });
            
            // Send the request with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => {
                console.error("Request timeout triggered after 60s");
                controller.abort();
            }, 60000); // 60 second timeout
            
            console.log("Sending POST request to /api/message");
            const startTime = new Date();
            
            const response = await fetch('/api/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData),
                signal: controller.signal
            });
            
            const endTime = new Date();
            const responseTime = endTime - startTime;
            clearTimeout(timeoutId);
            
            console.log(`Response received in ${responseTime}ms, status:`, response.status, response.statusText);
            console.log("Response headers:", [...response.headers.entries()].reduce((obj, [key, val]) => ({...obj, [key]: val}), {}));
            
            if (!response.ok) {
                console.error("Response not OK:", {
                    status: response.status, 
                    statusText: response.statusText
                });
                
                let responseText;
                try {
                    responseText = await response.text();
                    console.error("Error response body:", responseText);
                } catch (e) {
                    console.error("Could not read error response body");
                }
                
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }
            
            // Try to parse the response
            let responseData;
            let responseText;
            try {
                responseText = await response.text();
                console.log("Response text (first 100 chars):", responseText.substring(0, 100));
                responseData = JSON.parse(responseText);
                console.log("Response parsed successfully, bot response length:", 
                    responseData.bot_response ? responseData.bot_response.length : 0);
            } catch (parseError) {
                console.error("Failed to parse response:", parseError);
                console.error("Response text was:", responseText);
                throw new Error("خطا در پارس پاسخ سرور");
            }
            
            // Update conversation ID if needed
            if (responseData.conversation_id) {
                window.chatState.currentConversationId = responseData.conversation_id;
                window.history.pushState({}, '', `/chat/${responseData.conversation_id}`);
                console.log("Conversation ID updated:", responseData.conversation_id);
            }
            
            // Update bot message with simple text first
            if (botMessage && botMessage.querySelector('.message-content')) {
                const contentDiv = botMessage.querySelector('.message-content');
                
                // بررسی پاسخ دریافتی از سرور
                if (responseData && (responseData.message || responseData.bot_response)) {
                    const botResponse = responseData.message || responseData.bot_response;
                    
                    // چک کنیم که پاسخ خالی نباشد
                    if (!botResponse) {
                        console.warn("Empty bot response received");
                        contentDiv.textContent = "پاسخی دریافت نشد";
                        return;
                    }
                    
                    console.log("Raw bot response type:", typeof botResponse);
                    console.log("Raw bot response length:", botResponse.length);
                    
                    // ابتدا متن خام را نمایش دهیم تا کاربر منتظر نماند
                    contentDiv.textContent = botResponse;
                    
                    // ذخیره محتوای اصلی برای بازیابی بعدی
                    contentDiv.setAttribute('data-message-content', botResponse);
                    
                    // تنظیم جهت متن و اضافه کردن حفظ خط جدید
                    if (/[\u0600-\u06FF]/.test(botResponse)) {
                        contentDiv.setAttribute('dir', 'rtl');
                    }
                    // اضافه کردن استایل white-space برای حفظ خطوط جدید
                    contentDiv.style.whiteSpace = 'pre-wrap';
                    
                    // فرمت‌بندی محتوا در یک بلوک try-catch مجزا
                    setTimeout(() => {
                        try {
                            if (!window.marked) {
                                console.error("Marked library not loaded!");
                                return;
                            }
                            
                            // چک مجدد محتوا
                            if (!botResponse || typeof botResponse !== 'string') {
                                console.warn("Invalid content type for marked:", typeof botResponse);
                                return;
                            }
                            
                            console.log("Formatting bot response with marked");
                            
                            // تنظیمات marked برای اطمینان از عملکرد درست
                            marked.setOptions({
                                breaks: true,
                                gfm: true,
                                headerIds: true,
                                pedantic: false,
                                mangle: false,
                                sanitize: false,
                                silent: true  // برای جلوگیری از error throwing
                            });
                            
                            // پردازش Markdown با بررسی خروجی
                            let formattedHtml = null;
                            try {
                                formattedHtml = marked.parse(botResponse);
                                
                                if (!formattedHtml) {
                                    console.warn("Marked returned empty result");
                                    return;
                                }
                                
                                // اعمال HTML فرمت شده
                                contentDiv.innerHTML = formattedHtml;
                                
                                // اطمینان از اینکه استایل white-space حفظ شود، حتی بعد از تغییر innerHTML
                                contentDiv.style.whiteSpace = 'pre-wrap';
                                
                                // Process code blocks
                                if (window.hljs) {
                                    console.log("Applying syntax highlighting");
                                    addCodeButtons(contentDiv);
                                }
                                
                                // Process math if available
                                if (window.katex) {
                                    console.log("Processing math expressions");
                                    processMathInElement(contentDiv);
                                }
                                
                                // Make links open in new tab
                                contentDiv.querySelectorAll('a').forEach(link => {
                                    link.setAttribute('target', '_blank');
                                    link.setAttribute('rel', 'noopener noreferrer');
                                });
                                
                                // اطمینان از استایل تمام پاراگراف‌ها
                                contentDiv.querySelectorAll('p').forEach(p => {
                                    p.style.whiteSpace = 'pre-wrap';
                                    p.style.margin = '0.5em 0';
                                });
                                
                                console.log("Message formatting completed successfully");
                            } catch (parseError) {
                                console.error("Error in marked.parse():", parseError);
                                // اگر فرمت‌بندی شکست خورد، متن خام را حفظ می‌کنیم
                            }
                        } catch (formatError) {
                            console.error("Error during formatting:", formatError);
                            // متن خام از قبل نمایش داده شده است
                        }
                    }, 50); // اندکی تأخیر برای اطمینان از اینکه UI ابتدا متن خام را نمایش داده
                } else {
                    // اگر پاسخی وجود نداشت
                    console.warn("No bot_response or message field in response");
                    contentDiv.textContent = "پاسخی از سرور دریافت نشد";
                }
            } else {
                console.error("Bot message element or content div not found");
            }
            
        } catch (error) {
            console.error("=== API COMMUNICATION ERROR ===", error);
            
            // Check for specific error types
            let errorMessage = "متأسفانه در ارتباط با سرور خطایی رخ داد. لطفاً دوباره تلاش کنید.";
            
            if (error.name === 'AbortError') {
                errorMessage = "درخواست به دلیل طولانی شدن زمان پاسخ لغو شد. لطفاً دوباره تلاش کنید.";
            }
            else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage = "خطای شبکه: لطفاً اتصال اینترنت خود را بررسی کنید و مطمئن شوید سرور در حال اجراست.";
            }
            
            // Log detailed error info
            console.error({
                errorType: error.name,
                errorMessage: error.message,
                stack: error.stack,
                modelBeingUsed: window.chatState.currentModel,
                conversationId: window.chatState.currentConversationId
            });
            
            // Update error message if we have a placeholder message
            if (botMessage && botMessage.querySelector('.message-content')) {
                const contentDiv = botMessage.querySelector('.message-content');
                contentDiv.textContent = errorMessage;
                contentDiv.style.color = '#ff5252';
            } else {
                createMessage(errorMessage, false);
            }
        }
        
    } catch (outerError) {
        console.error("Critical error in sendMessage:", outerError);
        createMessage("خطای بحرانی در سیستم چت. لطفاً صفحه را رفرش کنید و دوباره تلاش کنید.", false);
    } finally {
        // Reset processing state
        window.chatState.isProcessing = false;
        
        // Hide typing indicator
        typingIndicator.style.display = 'none';
        
        console.log("==== SEND MESSAGE FUNCTION COMPLETED ====");
    }
}

// Helper function to add copy and run buttons to code blocks
function addCodeButtons(element) {
    if (!window.hljs) return;
    
    element.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
        
        // Add copy button to code blocks
        const container = block.parentNode;
        
        // Check if buttons already exist
        if (container.querySelector('.copy-code-btn')) return;
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-code-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.title = 'کپی کد';
        copyBtn.onclick = function() {
            navigator.clipboard.writeText(block.textContent)
                .then(() => {
                    copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                    }, 2000);
                })
                .catch(err => {
                    console.error('خطا در کپی کردن:', err);
                });
        };
        
        // Add run HTML button for HTML code blocks
        if (block.classList.contains('language-html')) {
            const runBtn = document.createElement('button');
            runBtn.className = 'run-html-btn';
            runBtn.innerHTML = '<i class="fas fa-play"></i>';
            runBtn.title = 'اجرای HTML';
            runBtn.onclick = function() {
                const htmlCode = block.textContent;
                const previewWindow = window.open('', '_blank');
                previewWindow.document.write(htmlCode);
                previewWindow.document.close();
            };
            container.insertBefore(runBtn, container.firstChild);
        }
        
        container.insertBefore(copyBtn, container.firstChild);
    });
}

// اضافه کردن استایل‌های جدید برای پیام‌ها و فرمول‌ها
if (!document.getElementById('enhanced-chat-styles')) {
    const style = document.createElement('style');
    style.id = 'enhanced-chat-styles';
    style.textContent = `
        .message-content {
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-wrap: break-word;
            line-height: 1.6;
            display: block;
            width: 100%;
        }
        
        .message-content p {
            margin: 0.8em 0;
            line-height: 1.6;
            display: block;
            width: 100%;
        }
        
        .message-content pre {
            direction: ltr;
            text-align: left;
            margin: 1em 0;
            padding: 1em;
            border-radius: 8px;
            background: #1e1e1e;
            color: #d4d4d4;
            overflow-x: auto;
            display: block;
            width: 100%;
        }
        
        .message-content code {
            direction: ltr;
            unicode-bidi: bidi-override;
            display: inline-block;
            font-family: 'Fira Code', monospace;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            background: #1e1e1e;
            color: #d4d4d4;
        }
        
        .math-block {
            display: block;
            overflow-x: auto;
            margin: 1em 0;
            padding: 1em;
            background: rgba(0,10,20,0.02);
            border-radius: 8px;
            transition: all 0.3s ease;
            cursor: zoom-in;
            text-align: center;
            width: 100%;
            font-size: 1.1em;
        }
        
        .math-block.math-zoomed {
            transform: scale(1.1);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            background: rgba(0,10,20,0.03);
            cursor: zoom-out;
        }
        
        .math-inline {
            display: inline-block;
            vertical-align: middle;
            padding: 0 0.2em;
            font-size: 1.1em;
        }
        
        .math-error {
            color: #dc3545;
            border-left: 3px solid #dc3545;
            padding-left: 1em;
            background: rgba(220,53,69,0.1);
        }
        
        .message-content ul, .message-content ol {
            margin: 0.8em 0;
            padding-right: 1.5em;
            padding-left: 0;
            display: block;
            width: 100%;
        }
        
        .message-content li {
            margin: 0.4em 0;
            display: list-item;
        }
        
        .message-content blockquote {
            margin: 1em 0;
            padding: 0.5em 1em;
            border-right: 4px solid #4a6bdf;
            background: rgba(74,107,223,0.05);
            border-radius: 4px;
            display: block;
            width: 100%;
        }
        
        .message-content img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 1em 0;
            display: block;
        }
        
        .message-content table {
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
            direction: rtl;
            display: table;
        }
        
        .message-content th, .message-content td {
            padding: 0.5em;
            border: 1px solid #ddd;
            text-align: right;
        }
        
        .message-content th {
            background: #f8f9fa;
        }
        
        .message-content tr:nth-child(even) {
            background: #f8f9fa;
        }

        .message {
            display: block;
            width: 100%;
        }

        .message > div {
            display: block;
            width: 100%;
        }

        .katex-display {
            direction: ltr !important;
            text-align: center !important;
            width: 100% !important;
            overflow-x: auto;
            padding: 0.5em 0;
        }

        .katex {
            font-size: 1.1em;
            direction: ltr !important;
            text-align: center !important;
        }
    `;
    document.head.appendChild(style);
}

// نسخهٔ بهبود یافته از تابع processMathInElement
function processMathInElement(element) {
    if (!window.katex) {
        console.warn("KaTeX library not loaded, skipping math processing");
        return;
    }
    
    if (!element || !element.innerHTML) {
        console.warn("Invalid element or empty innerHTML in processMathInElement");
        return;
    }
    
    try {
        // Find all math expressions
        let html = element.innerHTML;
        const originalHtml = html;
        
        try {
            // 1. Process block math first ($$...$$)
            const blockRegex = /\$\$([\s\S]*?)\$\$/g;
            html = html.replace(blockRegex, (match, formula) => {
                try {
                    if (!formula.trim()) return match;
                    
                    const rendered = katex.renderToString(formula.trim(), {
                        displayMode: true,
                        throwOnError: false,
                        trust: true,
                        strict: false,
                        output: 'html',
                        macros: {
                            "\\pm": "\\pm",
                            "\\sqrt": "\\sqrt",
                            "\\pi": "\\pi"
                        }
                    });
                    
                    return `<div class="math-block" onclick="this.classList.toggle('math-zoomed')">${rendered}</div>`;
                } catch (err) {
                    console.warn(`KaTeX block rendering error: ${err.message}`);
                    return `<div class="math-block math-error" title="${err.message}">خطا در فرمول: ${formula}</div>`;
                }
            });
            
            // 2. Then process inline math ($...$)
            const inlineRegex = /\$([^$\n]+?)\$/g;
            html = html.replace(inlineRegex, (match, formula) => {
                try {
                    if (!formula.trim()) return match;
                    
                    const rendered = katex.renderToString(formula.trim(), {
                        displayMode: false,
                        throwOnError: false,
                        trust: true,
                        strict: false,
                        output: 'html',
                        macros: {
                            "\\pm": "\\pm",
                            "\\sqrt": "\\sqrt",
                            "\\pi": "\\pi"
                        }
                    });
                    
                    return `<span class="math-inline">${rendered}</span>`;
                } catch (err) {
                    console.warn(`KaTeX inline rendering error: ${err.message}`);
                    return `<span class="math-inline math-error" title="${err.message}">${formula}</span>`;
                }
            });
            
            // Apply the processed HTML
            element.innerHTML = html;
            
        } catch (err) {
            console.error("Critical error in math processing:", err);
            element.innerHTML = originalHtml;
        }
        
    } catch (err) {
        console.error("Error in processMathInElement:", err);
    }
}
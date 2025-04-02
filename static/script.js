document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const sidebar = document.getElementById('sidebar');
    const toggleSidebar = document.getElementById('toggle-sidebar');
    const newChatButton = document.getElementById('new-chat');
    const typingIndicator = document.getElementById('typing-indicator');
    const thinkerButton = document.getElementById('thinker-toggle');
    const formatToolbar = document.getElementById('formatting-toolbar');
    const formatButtons = document.querySelectorAll('.format-btn');
    const previewModal = document.getElementById('preview-modal');
    const previewBody = document.getElementById('preview-body');
    const closePreview = document.getElementById('close-preview');
    const sendPreview = document.getElementById('send-preview');
    
    // Store important elements and app state in global namespace as a single organized object
    window.chatApp = {
        elements: {
            chatMessages,
            userInput,
            sendButton,
            sidebar,
            toggleSidebar,
            typingIndicator,
            thinkerButton,
            previewModal,
            previewBody
        },
        state: {
            isProcessing: false,
            currentConversationId: null,
            currentModel: 'deepseek-chat-v3-0324:free', // Default model
            isThinkerMode: false // Thinker mode is off by default
        }
    };
    
    // Backward compatibility for older code
    window.isProcessing = false;
    window.currentConversationId = null;
    
    // Get current conversation ID from URL and set it in the global state
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length === 3 && pathParts[1] === 'chat') {
        window.chatApp.state.currentConversationId = pathParts[2];
        window.currentConversationId = pathParts[2]; // For backward compatibility
    }

    // Configure marked for markdown parsing
    marked.setOptions({
        breaks: true,
        gfm: true, // GitHub Flavored Markdown
        pedantic: false,
        sanitize: false,
        smartLists: true,
        smartypants: false,
        // غیرفعال کردن شناسایی خودکار کد برای جلوگیری از نمایش متن فارسی به عنوان کد
        highlight: function(code, lang) {
            // فقط اگر زبان مشخص شده باشد آن را کد در نظر بگیر
            if (lang && lang.trim() !== '') {
                return code;
            }
            // در غیر این صورت، این را کد در نظر نگیر و به صورت متن عادی برگردان
            return code;
        },
        renderer: createCustomRenderer(),
    });

    // ایجاد رندرر سفارشی برای مارک‌داون
    function createCustomRenderer() {
        const renderer = new marked.Renderer();
        
        // ذخیره متد اصلی code
        const originalCodeRenderer = renderer.code;
        
        // تعریف مجدد چگونگی رندر کردن بلوک‌های کد
        renderer.code = function(code, language) {
            // اگر محتوا فارسی است، آن را به صورت پاراگراف عادی نمایش بده
            if (/[\u0600-\u06FF]/.test(code) && (!language || language.trim() === '')) {
                return `<p>${code}</p>`;
            }
            
            // در غیر این صورت از رندرر اصلی استفاده کن
            return originalCodeRenderer.call(this, code, language);
        };
        
        return renderer;
    }

    // Process existing messages on page load
    processExistingMessages();

    // Helper function for delays
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Function to preprocess markdown text to prevent Persian text from being interpreted as code
    function preprocessMarkdown(text) {
        // Check if the text contains Persian characters but doesn't have explicit code markers
        if (/[\u0600-\u06FF]/.test(text)) {
            // Split by lines to process each line
            const lines = text.split('\n');
            
            // Process each line
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                
                // If line starts with 4 spaces or a tab, but contains Persian text, 
                // it might be mistakenly interpreted as code - so remove the spaces
                if ((line.startsWith('    ') || line.startsWith('\t')) && /[\u0600-\u06FF]/.test(line)) {
                    lines[i] = line.replace(/^( {4}|\t)/, '');
                }
            }
            
            // Join back lines
            return lines.join('\n');
        }
        
        return text;
    }

    // Function to safely parse markdown with custom preprocessing
    function safelyParseMarkdown(content) {
        // Preprocess content
        const preprocessed = preprocessMarkdown(content);
        
        // Parse with marked
        return marked.parse(preprocessed);
    }

    // Function to process all existing messages when page loads or refreshes
    function processExistingMessages() {
        // Get all message content divs
        const messageContents = document.querySelectorAll('.message-content');
        
        if (messageContents.length === 0) return;

        messageContents.forEach(content => {
            // Skip welcome message as it's already formatted properly
            if (content.closest('.welcome-message')) {
                return;
            }
            
            // Get the original HTML content
            const originalHTML = content.innerHTML;
            
            // Process the content with safe parsing to prevent Persian text from becoming code
            content.innerHTML = safelyParseMarkdown(originalHTML);
            
            // Process math formulas
            processMathFormulas(content);
        });
    }

    // Function to create and append a message element
    function createMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content markdown-body';
        
        // Check if the content is RTL (Persian/Arabic)
        if (/[\u0600-\u06FF]/.test(content)) {
            contentDiv.setAttribute('dir', 'rtl');
        } else {
            contentDiv.setAttribute('dir', 'ltr');
        }
        
        // Safely parse markdown to prevent Persian text from becoming code
        contentDiv.innerHTML = safelyParseMarkdown(content);
        
        // Process math formulas
        processMathFormulas(contentDiv);
        
        // Add the content div to the message
        messageDiv.appendChild(contentDiv);
        
        // Add the message to the chat
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }

    // Function to handle user input
    async function handleUserInput() {
        const message = userInput.value.trim();
        if (!message || window.chatApp.state.isProcessing) return;
        
        window.chatApp.state.isProcessing = true;
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Create and display user message
        createMessage(message, true);
        
        // Show typing indicator
        typingIndicator.style.display = 'flex';
        
        try {
            const response = await fetch('/api/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: window.chatApp.state.currentConversationId
                })
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            
            // Update current conversation ID
            if (!window.chatApp.state.currentConversationId) {
                window.chatApp.state.currentConversationId = data.conversation_id;
                // Update URL without reloading
                window.history.pushState({}, '', `/chat/${data.conversation_id}`);
            }
            
            // Hide typing indicator
            typingIndicator.style.display = 'none';
            
            // Create and display bot message
            createMessage(data.bot_response);
            
        } catch (error) {
            console.error('Error:', error);
            typingIndicator.style.display = 'none';
            createMessage('متأسفانه در پردازش پیام شما مشکلی پیش آمد. لطفاً دوباره تلاش کنید.');
        }
        
        window.chatApp.state.isProcessing = false;
    }

    // Event listeners
    sendButton.addEventListener('click', handleUserInput);
    
    userInput.addEventListener('keydown', async function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            await handleUserInput();
        }
    });
    
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Toggle sidebar with backdrop
    toggleSidebar.addEventListener('click', function() {
        sidebar.classList.toggle('active');
        
        // Add dark backdrop when menu is open
        if (sidebar.classList.contains('active')) {
            // Create overlay for black blur background
            if (!document.querySelector('.sidebar-overlay')) {
                const overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                overlay.style.position = 'fixed';
                overlay.style.top = '0';
                overlay.style.left = '0';
                overlay.style.right = '0';
                overlay.style.bottom = '0';
                overlay.style.background = 'rgba(0, 0, 0, 0.5)';
                overlay.style.backdropFilter = 'blur(3px)';
                overlay.style.WebkitBackdropFilter = 'blur(3px)'; // برای پشتیبانی از Safari
                overlay.style.zIndex = '999';
                
                // Close menu when clicking on backdrop
                overlay.addEventListener('click', function() {
                    sidebar.classList.remove('active');
                    document.body.removeChild(overlay);
                });
                
                document.body.appendChild(overlay);
            }
        } else {
            // Remove overlay when menu is closed
            const overlay = document.querySelector('.sidebar-overlay');
            if (overlay) {
                document.body.removeChild(overlay);
            }
        }
    });
    
    // New chat button
    newChatButton.addEventListener('click', async function() {
        try {
            const response = await fetch('/api/conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: 'گفتگوی جدید'
                })
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            window.location.href = `/chat/${data.id}`;
            
        } catch (error) {
            console.error('Error:', error);
            alert('خطا در ایجاد گفتگوی جدید');
        }
    });
    
    // Edit conversation title
    document.querySelectorAll('.edit-title').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const conversationId = this.dataset.id;
            const titleElement = this.closest('.conversation-item').querySelector('.conversation-title');
            const currentTitle = titleElement.textContent;
            
            const newTitle = prompt('عنوان جدید را وارد کنید:', currentTitle);
            if (!newTitle || newTitle === currentTitle) return;
            
            try {
                const response = await fetch(`/api/conversation/${conversationId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: newTitle
                    })
                });
                
                if (!response.ok) throw new Error('Network response was not ok');
                
                titleElement.textContent = newTitle;
                if (conversationId === window.chatApp.state.currentConversationId) {
                    document.querySelector('.chat-title').textContent = newTitle;
                }
                
            } catch (error) {
                console.error('Error:', error);
                alert('خطا در به‌روزرسانی عنوان');
            }
        });
    });
    
    // Delete conversation
    document.querySelectorAll('.delete-conversation').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const conversationId = this.dataset.id;
            
            if (!confirm('آیا از حذف این گفتگو اطمینان دارید؟')) return;
            
            try {
                const response = await fetch(`/api/conversation/${conversationId}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) throw new Error('Network response was not ok');
                
                if (conversationId === window.chatApp.state.currentConversationId) {
                    window.location.href = '/chat';
                } else {
                    this.closest('.conversation-item').remove();
                }
                
            } catch (error) {
                console.error('Error:', error);
                alert('خطا در حذف گفتگو');
            }
        });
    });
    
    // Focus input field
    userInput.focus();

    // Handle paste events for images
    userInput.addEventListener('paste', function(e) {
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        for (const item of items) {
            if (item.type.indexOf('image') === 0) {
                e.preventDefault();
                const file = item.getAsFile();
                handleFileUpload([file]);
            }
        }
    });

    // File upload handling
    fileUploadButton.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => handleFileUpload(e.target.files));

    // Web search button
    webSearchButton.addEventListener('click', function() {
        const query = userInput.value.trim();
        if (query) {
            performWebSearch(query);
        }
    });

    // Toggle formatting toolbar
    if (formatToggle) {
        formatToggle.addEventListener('click', function() {
            formatToolbar.classList.toggle('active');
        });
    }
    
    // Handle formatting buttons
    if (formatButtons.length > 0) {
        formatButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const format = this.getAttribute('data-format');
                applyFormatting(format);
            });
        });
    }
    
    // Function to apply formatting to the input text
    function applyFormatting(format) {
        const start = userInput.selectionStart;
        const end = userInput.selectionEnd;
        const text = userInput.value;
        const selectedText = text.substring(start, end);
        let replacement = '';
        
        switch(format) {
            case 'bold':
                replacement = `**${selectedText || 'متن پررنگ'}**`;
                break;
            case 'italic':
                replacement = `*${selectedText || 'متن مورب'}*`;
                break;
            case 'heading':
                replacement = `\n# ${selectedText || 'عنوان'}\n`;
                break;
            case 'list':
                if (selectedText) {
                    const lines = selectedText.split('\n');
                    replacement = lines.map(line => `- ${line}`).join('\n');
                } else {
                    replacement = '- آیتم اول\n- آیتم دوم\n- آیتم سوم';
                }
                break;
            case 'code':
                if (selectedText) {
                    // If there are newlines, use a code block, otherwise use inline code
                    if (selectedText.includes('\n')) {
                        replacement = '```\n' + selectedText + '\n```';
                    } else {
                        replacement = '`' + selectedText + '`';
                    }
                } else {
                    replacement = '```\nکد شما اینجا\n```';
                }
                break;
            case 'math':
                replacement = `$${selectedText || 'x^2 + y^2 = z^2'}$`;
                break;
            case 'hr':
                replacement = '\n---\n';
                break;
        }
        
        userInput.value = text.substring(0, start) + replacement + text.substring(end);
        
        // Set cursor position after the inserted text
        const newCursorPos = start + replacement.length;
        userInput.setSelectionRange(newCursorPos, newCursorPos);
        
        // Focus back on the input
        userInput.focus();
    }
    
    // Preview functionality
    if (userInput && previewModal && previewBody) {
        // Preview keyboard shortcut (Ctrl+P or Cmd+P)
        userInput.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
                e.preventDefault();
                showPreview();
            }
        });
        
        // Close preview with Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && previewModal.style.display === 'flex') {
                hidePreview();
            }
        });
        
        // Close preview button
        if (closePreview) {
            closePreview.addEventListener('click', hidePreview);
        }
        
        // Send from preview
        if (sendPreview) {
            sendPreview.addEventListener('click', function() {
                sendMessage();
                hidePreview();
            });
        }
    }
    
    function showPreview() {
        const previewModal = document.getElementById('preview-modal');
        const previewBody = document.getElementById('preview-body');
        const userInput = document.getElementById('user-input');
        
        if (!userInput || !previewModal || !previewBody) return;
        
        const text = userInput.value.trim();
        if (!text) return;
        
        // Clear previous content
        previewBody.innerHTML = '';
        
        // Render markdown preview - with safe parsing
        previewBody.innerHTML = safelyParseMarkdown(text);
        
        // Process math formulas
        processMathFormulas(previewBody);
        
        previewModal.style.display = 'flex';
    }
    
    function hidePreview() {
        const previewModal = document.getElementById('preview-modal');
        if (previewModal) {
            previewModal.style.display = 'none';
        }
    }
    
    // Generate stars for background
    generateStars();

    // Add animations after a short delay to ensure all elements are rendered
    setTimeout(() => {
        addAnimations();
    }, 500);

    // Set up thinker button functionality
    if (thinkerButton) {
        thinkerButton.addEventListener('click', toggleThinkerMode);
    }

    // On mobile, hide sidebar by default
    if (window.innerWidth <= 768) {
        sidebar.classList.remove('active');
    }
});

// File upload handling
async function handleFileUpload(files) {
    if (!files.length) return;

    // Reference the global app object
    const { elements, state } = window.chatApp;
    
    // Set processing state to prevent multiple uploads
    if (state.isProcessing) return;
    state.isProcessing = true;
    window.isProcessing = true; // For backward compatibility

    const formData = new FormData();
    for (const file of files) {
        formData.append('files[]', file);
    }

    // Show typing indicator
    elements.typingIndicator.style.display = 'flex';
    
    // Add file preview to the message area
    const uploadingMessage = document.createElement('div');
    uploadingMessage.className = 'message user-message';
    uploadingMessage.id = 'file-upload-preview';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content markdown-body';
    contentDiv.innerHTML = '<strong>در حال آپلود فایل‌ها...</strong><div class="upload-preview"></div>';
    
    uploadingMessage.appendChild(contentDiv);
    elements.chatMessages.appendChild(uploadingMessage);
    
    const previewContainer = contentDiv.querySelector('.upload-preview');
    
    // Add simple previews for each file
    for (const file of files) {
        const filePreview = document.createElement('div');
        filePreview.className = 'file-preview';
        
        if (file.type.startsWith('image/')) {
            // For images, show thumbnail preview
            const reader = new FileReader();
            reader.onload = function(e) {
                filePreview.innerHTML = `
                    <div class="file-preview-item">
                        <img src="${e.target.result}" alt="${file.name}" style="max-width: 200px; max-height: 150px; border-radius: 8px;">
                        <div class="file-name">${file.name} (${formatFileSize(file.size)})</div>
                        <div class="progress-bar"><div class="progress" style="width: 10%"></div></div>
                    </div>
                `;
            };
            reader.readAsDataURL(file);
        } else {
            // For other files, show icon based on file type
            let icon = 'fa-file';
            if (file.name.endsWith('.pdf')) icon = 'fa-file-pdf';
            else if (file.name.endsWith('.doc') || file.name.endsWith('.docx')) icon = 'fa-file-word';
            else if (file.name.endsWith('.txt')) icon = 'fa-file-alt';
            
            filePreview.innerHTML = `
                <div class="file-preview-item">
                    <i class="fas ${icon} file-icon"></i>
                    <div class="file-name">${file.name} (${formatFileSize(file.size)})</div>
                    <div class="progress-bar"><div class="progress" style="width: 10%"></div></div>
                </div>
            `;
        }
        
        previewContainer.appendChild(filePreview);
    }
    
    // Scroll to the newest message
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    try {
        // Simulate progress
        const progressBars = previewContainer.querySelectorAll('.progress');
        const progressInterval = setInterval(() => {
            progressBars.forEach(bar => {
                const currentWidth = parseInt(bar.style.width);
                if (currentWidth < 90) {
                    bar.style.width = (currentWidth + 10) + '%';
                }
            });
        }, 300);
        
        // Send the actual request
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);
        progressBars.forEach(bar => {
            bar.style.width = '100%';
        });
        
        await sleep(500); // Show completed progress briefly
        
        const data = await response.json();
        
        // Remove the temporary upload message
        const uploadPreview = document.getElementById('file-upload-preview');
        if (uploadPreview) {
            elements.chatMessages.removeChild(uploadPreview);
        }
        
        if (data.success) {
            // Store the uploaded files in our state
            state.uploadedFiles = state.uploadedFiles.concat(data.files);
            
            // Add final message with uploaded files
            let messageContent = '';
            
            if (files.length === 1) {
                messageContent = 'فایل آپلود شد:';
            } else {
                messageContent = `${files.length} فایل آپلود شد:`;
            }
            
            messageContent += '<div class="uploaded-files">';
            
            // Add each file to the message
            for (const file of data.files) {
                if (file.type.startsWith('image/')) {
                    messageContent += `
                        <div class="uploaded-file">
                            <img src="${file.url}" alt="${file.name}" style="max-width: 100%; border-radius: 8px;">
                            <div class="file-name">${file.name}</div>
                        </div>
                    `;
                } else {
                    let icon = 'fa-file';
                    if (file.name.endsWith('.pdf')) icon = 'fa-file-pdf';
                    else if (file.name.endsWith('.doc') || file.name.endsWith('.docx')) icon = 'fa-file-word';
                    else if (file.name.endsWith('.txt')) icon = 'fa-file-alt';
                    
                    messageContent += `
                        <div class="uploaded-file">
                            <a href="${file.url}" target="_blank" class="file-link">
                                <i class="fas ${icon} file-icon"></i>
                                <div class="file-name">${file.name}</div>
                            </a>
                        </div>
                    `;
                }
            }
            
            messageContent += '</div>';
            
            appendMessage(messageContent, 'user');
        } else {
            appendMessage('خطا در آپلود فایل. لطفاً دوباره تلاش کنید.', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        appendMessage('خطا در آپلود فایل. لطفاً دوباره تلاش کنید.', 'error');
        
        // Remove the temporary upload message on error
        const uploadPreview = document.getElementById('file-upload-preview');
        if (uploadPreview) {
            elements.chatMessages.removeChild(uploadPreview);
        }
    } finally {
        elements.typingIndicator.style.display = 'none';
        state.isProcessing = false;
        window.isProcessing = false;
        elements.fileInput.value = '';
    }
}

// Helper function to format file size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
}

// Web search function
async function performWebSearch(query) {
    // Reference the global app object
    const { elements, state } = window.chatApp;
    
    // Prevent multiple searches at once
    if (state.isProcessing) return;
    state.isProcessing = true;
    window.isProcessing = true; // For backward compatibility
    
    // Update loading state
    elements.typingIndicator.style.display = 'flex';
    
    // Add user query to chat
    appendMessage(`<strong>🔍 جستجو:</strong> ${query}`, 'user');

    try {
        // Show searching indicator
        const searchingMessage = document.createElement('div');
        searchingMessage.className = 'message bot-message';
        searchingMessage.id = 'web-search-indicator';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content markdown-body';
        contentDiv.innerHTML = '<div class="search-indicator"><i class="fas fa-search fa-spin"></i> در حال جستجو در وب...</div>';
        
        searchingMessage.appendChild(contentDiv);
        elements.chatMessages.appendChild(searchingMessage);
        
        // Scroll to the newest message
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        
        // Send the search request
        const response = await fetch('/api/web-search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }

        const data = await response.json();
        
        // Remove the temporary searching message
        const searchIndicator = document.getElementById('web-search-indicator');
        if (searchIndicator) {
            elements.chatMessages.removeChild(searchIndicator);
        }
        
        // Show the search results
        let resultsContent = `<strong>🔍 نتایج جستجو برای: "${query}"</strong>\n\n`;
        
        if (data.results && data.results.length > 0) {
            resultsContent += data.results;
        } else {
            resultsContent += "متأسفانه نتیجه‌ای برای جستجوی شما یافت نشد.";
        }
        
        // Add a beautiful separator
        resultsContent += "\n\n---\n\n<div class='search-footer'>جستجو توسط <strong>OpenRouter AI API</strong></div>";
        
        appendMessage(resultsContent, 'assistant');
    } catch (error) {
        console.error('Error:', error);
        
        // Remove the temporary searching message if exists
        const searchIndicator = document.getElementById('web-search-indicator');
        if (searchIndicator) {
            elements.chatMessages.removeChild(searchIndicator);
        }
        
        appendMessage('خطا در جستجوی وب. لطفاً دوباره تلاش کنید.', 'error');
    } finally {
        elements.typingIndicator.style.display = 'none';
        state.isProcessing = false;
        window.isProcessing = false;
    }
}

// Helper functions for typing indicator
function showTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.style.display = 'flex';
    }
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.style.display = 'none';
    }
}

function clearMessages() {
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h2>به دستیار هوشمند فارسی خوش آمدید! 👋</h2>
            <p>من آماده‌ام تا به سؤالات شما پاسخ دهم.</p>
            <p>می‌توانید از قابلیت‌های زیر استفاده کنید:</p>
            <ul>
                <li>جستجو در وب</li>
                <li>آپلود فایل و تصویر</li>
                <li>پردازش فرمول‌های ریاضی</li>
                <li>نمایش کد با syntax highlighting</li>
            </ul>
        </div>
    `;
}

// Process math formulas
function processMathFormulas(element) {
    if (!window.katex) return;
    
    try {
        // First, mark all existing KaTeX elements so we don't process them again
        const existingKatex = element.querySelectorAll('.katex, .katex-display');
        existingKatex.forEach(el => {
            el.setAttribute('data-processed', 'true');
        });
        
        // Replace HTML entities that break KaTeX
        let html = element.innerHTML;
        html = html.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
        element.innerHTML = html;
        
        // Handle special math delimiters: [\\boxed{...}] format (common in responses)
        const boxedMathRegex = /\[\s*\\boxed\{([\s\S]*?)\}\s*\]/g;
        let matches = element.innerHTML.match(boxedMathRegex);
        if (matches) {
            matches.forEach(match => {
                // Extract content inside \boxed{...}
                const boxedContent = match.match(/\\boxed\{([\s\S]*?)\}/);
                if (boxedContent && boxedContent[1]) {
                    const formula = boxedContent[1].trim();
                    try {
                        const rendered = katex.renderToString(formula, {
                            throwOnError: false,
                            displayMode: true
                        });
                        const safeMatch = match.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        const regex = new RegExp(safeMatch, 'g');
                        element.innerHTML = element.innerHTML.replace(
                            regex, 
                            `<div class="math-block boxed-math">${rendered}</div>`
                        );
                    } catch (e) {
                        console.error('KaTeX error (boxed math): ', e);
                    }
                }
            });
        }
        
        // Handle \[ ... \] format (block math)
        const blockLaTeXRegex = /\\\[([\s\S]*?)\\\]/g;
        matches = element.innerHTML.match(blockLaTeXRegex);
        if (matches) {
            matches.forEach(match => {
                const formula = match.slice(2, -2).trim();
                try {
                    const rendered = katex.renderToString(formula, {
                        throwOnError: false,
                        displayMode: true
                    });
                    const safeMatch = match.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    const regex = new RegExp(safeMatch, 'g');
                    element.innerHTML = element.innerHTML.replace(regex, `<div class="math-block">${rendered}</div>`);
                } catch (e) {
                    console.error('KaTeX error (block LaTeX): ', e);
                }
            });
        }
        
        // Handle $$...$$ format (block math)
        const blockMathRegex = /\$\$([\s\S]*?)\$\$/g;
        matches = element.innerHTML.match(blockMathRegex);
        if (matches) {
            matches.forEach(match => {
                const formula = match.slice(2, -2).trim();
                try {
                    const rendered = katex.renderToString(formula, {
                        throwOnError: false,
                        displayMode: true
                    });
                    const safeMatch = match.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    const regex = new RegExp(safeMatch, 'g');
                    element.innerHTML = element.innerHTML.replace(regex, `<div class="math-block">${rendered}</div>`);
                } catch (e) {
                    console.error('KaTeX error (block): ', e);
                }
            });
        }
    
        // Handle \( ... \) format (inline math)
        const inlineLaTeXRegex = /\\\(([\s\S]*?)\\\)/g;
        matches = element.innerHTML.match(inlineLaTeXRegex);
        if (matches) {
            matches.forEach(match => {
                const formula = match.slice(2, -2).trim();
                try {
                    const rendered = katex.renderToString(formula, {
                        throwOnError: false,
                        displayMode: false
                    });
                    const safeMatch = match.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    const regex = new RegExp(safeMatch, 'g');
                    element.innerHTML = element.innerHTML.replace(regex, rendered);
                } catch (e) {
                    console.error('KaTeX error (inline LaTeX): ', e);
                }
            });
        }
        
        // Handle $...$ format (inline math) - making sure it's not $$...$$
        // This regex uses negative lookbehind/lookahead to ensure it's not part of $$...$$
        const inlineMathRegex = /(?<!\$)\$(?!\$)((?:\\[\s\S]|[^\\$])*?)(?<!\$)\$(?!\$)/g;
        matches = element.innerHTML.match(inlineMathRegex);
        if (matches) {
            matches.forEach(match => {
                const formula = match.slice(1, -1).trim();
                try {
                    const rendered = katex.renderToString(formula, {
                        throwOnError: false,
                        displayMode: false
                    });
                    // Escape special regex characters in the match string
                    const escapedMatch = match.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    const regex = new RegExp(escapedMatch, 'g');
                    element.innerHTML = element.innerHTML.replace(regex, rendered);
                } catch (e) {
                    console.error('KaTeX error (inline): ', e, 'Formula:', formula);
                }
            });
        }
    } catch (e) {
        console.error('Math processing error:', e);
    }
    
    return element;
}

// Helper function to append messages
function appendMessage(content, role) {
    // Reference the global app object
    const { elements } = window.chatApp;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content markdown-body';
    
    // Check if the content is RTL (Persian/Arabic)
    if (/[\u0600-\u06FF]/.test(content)) {
        contentDiv.setAttribute('dir', 'rtl');
    } else {
        contentDiv.setAttribute('dir', 'ltr');
    }
    
    // Safely parse markdown to prevent Persian text from becoming code
    contentDiv.innerHTML = safelyParseMarkdown(content);
    
    // Process math formulas
    processMathFormulas(contentDiv);
    
    // Ensure any links open in a new tab
    contentDiv.querySelectorAll('a').forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });
    
    // Add the message div to the chat
    messageDiv.appendChild(contentDiv);
    elements.chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    return messageDiv;
}

// Update conversation title
async function updateConversationTitle(conversationId, newTitle) {
    try {
        const response = await fetch(`/api/conversation/${conversationId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: newTitle })
        });

        if (response.ok) {
            window.location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('خطا در بروزرسانی عنوان گفتگو');
    }
}

// Delete conversation
async function deleteConversation(conversationId) {
    try {
        const response = await fetch(`/api/conversation/${conversationId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            window.location.href = '/chat';
        }
    } catch (error) {
        console.error('Error:', error);
        alert('خطا در حذف گفتگو');
    }
}

// Handle message sending with previewing option
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey && window.chatApp.elements.userInput === document.activeElement) {
        // If Ctrl is pressed, show preview instead of sending
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            showPreview();
        } else {
            // Regular sending
            e.preventDefault();
            sendMessage();
        }
    }
});

// Generate stars background
function generateStars() {
    const stars = document.getElementById('stars');
    if (!stars) return;
    
    const count = 150;
    
    for (let i = 0; i < count; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        star.style.top = `${Math.random() * 100}%`;
        star.style.left = `${Math.random() * 100}%`;
        star.style.width = star.style.height = `${Math.random() * 2 + 1}px`;
        star.style.animationDuration = `${Math.random() * 5 + 5}s`;
        star.style.animationDelay = `${Math.random() * 5}s`;
        stars.appendChild(star);
    }
}

// Function to send messages to the server with streaming capability
async function sendMessage() {
    if (window.chatApp.state.isProcessing) return;
    
    const message = window.chatApp.elements.userInput.value.trim();
    if (!message) return;

    // Clear input
    window.chatApp.elements.userInput.value = '';
    
    // Create user message bubble
    createMessage(message, true);
    
    // Set processing state
    window.chatApp.state.isProcessing = true;
    window.isProcessing = true; // For backward compatibility
    
    // Show typing indicator
    window.chatApp.elements.typingIndicator.classList.add('active');
    
    try {
        // Create bot message container that will be filled with streaming content
        const botMessageDiv = document.createElement('div');
        botMessageDiv.className = 'message bot-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content markdown-body';
        contentDiv.innerHTML = '<div class="loading-dots"><div></div><div></div><div></div></div>';
        
        botMessageDiv.appendChild(contentDiv);
        chatMessages.appendChild(botMessageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        let accumulatedResponse = "";
        
        // Get current model from state
        const currentModel = window.chatApp.state.currentModel;
        
        // Create request data with model information
        const requestData = {
            message: message,
            conversation_id: window.chatApp.state.currentConversationId,
            model: currentModel
        };
        
        // Fetch from streaming endpoint
        const response = await fetch('/api/message/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response from server');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        // Process the streaming response
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            
            try {
                // Parse the chunk as JSON
                const jsonChunk = JSON.parse(chunk);
                
                // Process the bot's response
                if (jsonChunk.bot_response) {
                    accumulatedResponse += jsonChunk.bot_response;
                    
                    // Check if the content is RTL (Persian/Arabic)
                    if (/[\u0600-\u06FF]/.test(accumulatedResponse)) {
                        contentDiv.setAttribute('dir', 'rtl');
                    } else {
                        contentDiv.setAttribute('dir', 'ltr');
                    }
                    
                    // Update the message content with the accumulated response
                    contentDiv.innerHTML = safelyParseMarkdown(accumulatedResponse);
                    
                    // Process math formulas
                    processMathFormulas(contentDiv);
                    
                    // Make links open in new tab
                    contentDiv.querySelectorAll('a').forEach(link => {
                        link.setAttribute('target', '_blank');
                        link.setAttribute('rel', 'noopener noreferrer');
                    });
                    
                    // Scroll to bottom
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
                
                // If we get a conversation ID, update it
                if (jsonChunk.conversation_id && (!window.chatApp.state.currentConversationId || window.chatApp.state.currentConversationId === 'new')) {
                    window.chatApp.state.currentConversationId = jsonChunk.conversation_id;
                    window.currentConversationId = jsonChunk.conversation_id; // For backward compatibility
                    
                    // Update URL without reloading page
                    const newUrl = `/chat/${jsonChunk.conversation_id}`;
                    window.history.pushState({ path: newUrl }, '', newUrl);
                    
                    // Update sidebar to show new conversation
                    refreshSidebar();
                }
            } catch (error) {
                console.error('Error processing chunk:', error);
            }
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = 'Error: Failed to get response from server. Please try again.';
        chatMessages.appendChild(errorDiv);
        
    } finally {
        // Reset processing state
        window.chatApp.state.isProcessing = false;
        window.isProcessing = false; // For backward compatibility
        
        // Hide typing indicator
        window.chatApp.elements.typingIndicator.classList.remove('active');
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Add animations
        addAnimations();
    }
}

// Add animations to chat interface
function addAnimations() {
    // Add particle effects in the background (only if not already added)
    if (!document.querySelector('.particles')) {
        const particles = document.createElement('div');
        particles.className = 'particles';
        const chatArea = document.querySelector('.chat-area');
        if (chatArea) {
            chatArea.prepend(particles);
            
            // Create glowing particles that float around
            for (let i = 0; i < 20; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = `${Math.random() * 100}%`;
                particle.style.top = `${Math.random() * 100}%`;
                particle.style.width = particle.style.height = `${Math.random() * 15 + 5}px`;
                particle.style.opacity = (Math.random() * 0.2).toString();
                
                // Set random animation properties
                const duration = Math.random() * 30 + 10;
                const delay = Math.random() * 5;
                
                particle.style.animation = `float-particle ${duration}s linear infinite`;
                particle.style.animationDelay = `${delay}s`;
                
                particles.appendChild(particle);
            }
        }
    }
    
    // Add hover effects to buttons
    document.querySelectorAll('button:not([data-animation-added]), .button:not([data-animation-added])').forEach(button => {
        button.setAttribute('data-animation-added', 'true');
        button.addEventListener('mouseenter', function() {
            // Create ripple effect
            const ripple = document.createElement('div');
            ripple.className = 'ripple';
            this.appendChild(ripple);
            
            const rect = this.getBoundingClientRect();
            ripple.style.width = ripple.style.height = `${Math.max(rect.width, rect.height) * 2}px`;
            
            // Center the ripple
            ripple.style.left = `${-rect.width / 2}px`;
            ripple.style.top = `${-rect.height / 2}px`;
            
            // Remove the ripple after animation completes
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // اضافه کردن افکت‌های حرکتی بیشتر به حباب‌های پیام
    document.querySelectorAll('.message-bubble').forEach(bubble => {
        bubble.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.01)';
            this.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.2)';
        });
        
        bubble.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = 'none';
        });
    });
}

// Function to toggle between thinking and standard mode
function toggleThinkerMode() {
    const thinkerButton = window.chatApp.elements.thinkerButton;
    
    // Toggle thinker mode state
    window.chatApp.state.isThinkerMode = !window.chatApp.state.isThinkerMode;
    
    // Update button appearance
    if (window.chatApp.state.isThinkerMode) {
        thinkerButton.classList.add('active');
        window.chatApp.state.currentModel = 'claude-3-opus';
        
        // Show system message indicating thinker mode is activated
        const systemMessage = document.createElement('div');
        systemMessage.className = 'system-message';
        systemMessage.textContent = 'Thinker mode activated: Using Claude 3 Opus for deeper thinking';
        chatMessages.appendChild(systemMessage);
    } else {
        thinkerButton.classList.remove('active');
        window.chatApp.state.currentModel = 'deepseek-chat-v3-0324:free';
        
        // Show system message indicating thinker mode is deactivated
        const systemMessage = document.createElement('div');
        systemMessage.className = 'system-message';
        systemMessage.textContent = 'Thinker mode deactivated: Using standard DeepSeek model';
        chatMessages.appendChild(systemMessage);
    }
    
    // Scroll to see the new system message
    chatMessages.scrollTop = chatMessages.scrollHeight;
} 
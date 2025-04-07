document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded - initializing chat functionality");
    
    // DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const thinkerToggle = document.getElementById('thinker-toggle');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // Log detection of elements
    console.log("Critical DOM elements:", {
        chatMessages: !!chatMessages,
        userInput: !!userInput, 
        sendButton: !!sendButton,
        thinkerToggle: !!thinkerToggle,
        typingIndicator: !!typingIndicator
    });
    
    // Setup global state
    window.chatApp = {
        elements: {
            chatMessages,
            userInput,
            sendButton,
            thinkerToggle,
            typingIndicator
        },
        state: {
            isProcessing: false,
            currentConversationId: null,
            currentModel: 'gpt-4o',
            isThinkerMode: false
        }
    };
    
    // Get current conversation ID from URL
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length === 3 && pathParts[1] === 'chat') {
        window.chatApp.state.currentConversationId = pathParts[2];
    }
    
    // SETUP EVENT LISTENERS
    
    // Send button click
    if (sendButton) {
        console.log("Adding click event to send button");
        
        // Remove any existing event listeners
        const newSendButton = sendButton.cloneNode(true);
        sendButton.parentNode.replaceChild(newSendButton, sendButton);
        
        // Add click event listener
        newSendButton.addEventListener('click', function() {
            console.log("Send button clicked");
            sendMessage();
        });
    }
    
    // Thinker/model toggle button
    if (thinkerToggle) {
        console.log("Adding click event to thinker button");
        
        // Remove any existing event listeners
        const newThinkerToggle = thinkerToggle.cloneNode(true);
        thinkerToggle.parentNode.replaceChild(newThinkerToggle, thinkerToggle);
        
        // Add click event listener
        newThinkerToggle.addEventListener('click', function() {
            console.log("Thinker button clicked");
            
            // Toggle between models
            if (window.chatApp.state.currentModel === 'gpt-4o') {
                window.chatApp.state.currentModel = 'claude-3';
                alert('مدل زبانی به Claude 3 تغییر یافت');
            } else {
                window.chatApp.state.currentModel = 'gpt-4o';
                alert('مدل زبانی به GPT-4o تغییر یافت');
            }
            
            console.log("Current model:", window.chatApp.state.currentModel);
        });
    }
    
    // User input events (Enter key and text changes)
    if (userInput) {
        console.log("Adding events to user input");
        
        // Remove any existing event listeners
        const newUserInput = userInput.cloneNode(true);
        userInput.parentNode.replaceChild(newUserInput, userInput);
        
        // Update reference
        window.chatApp.elements.userInput = newUserInput;
        
        // Add keydown event listener
        newUserInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                if (e.shiftKey) {
                    // Allow new line with Shift+Enter
                    console.log("Shift+Enter pressed: new line");
                    return;
                } else {
                    // Send message with Enter
                    console.log("Enter pressed: sending message");
                    e.preventDefault();
                    sendMessage();
                }
            }
        });
        
        // Auto resize textarea
        newUserInput.addEventListener('input', function() {
            // Save to localStorage
            localStorage.setItem('current_message', this.value);
            
            // Auto-resize
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Restore message from localStorage
        const savedMessage = localStorage.getItem('current_message');
        if (savedMessage) {
            newUserInput.value = savedMessage;
            
            // Trigger resize
            newUserInput.style.height = 'auto';
            newUserInput.style.height = (newUserInput.scrollHeight) + 'px';
        }
    }
});

// MAIN FUNCTIONS

// Function to create and append a message
function createMessage(content, isUser = false) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) {
        console.error("Chat messages container not found");
        return;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    // Set direction for RTL text (Persian)
    if (/[\u0600-\u06FF]/.test(content)) {
        contentDiv.setAttribute('dir', 'rtl');
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to the latest message
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

// Function to send messages
async function sendMessage() {
    console.log("sendMessage called");
    
    // Get required elements
    const userInput = document.getElementById('user-input');
    const typingIndicator = document.getElementById('typing-indicator');
    
    if (!userInput || !typingIndicator) {
        console.error("Required elements not found:", {
            userInput: !!userInput,
            typingIndicator: !!typingIndicator
        });
        return;
    }
    
    // Prevent sending if already processing
    if (window.chatApp && window.chatApp.state && window.chatApp.state.isProcessing) {
        console.log("Already processing a message");
        return;
    }
    
    // Get message text
    const message = userInput.value.trim();
    if (!message) {
        console.log("Empty message, not sending");
        return;
    }
    
    // Clear input and localStorage
    userInput.value = '';
    userInput.style.height = 'auto';
    localStorage.removeItem('current_message');
    
    // Create user message
    createMessage(message, true);
    
    // Set processing state
    if (window.chatApp && window.chatApp.state) {
        window.chatApp.state.isProcessing = true;
    }
    
    // Show typing indicator
    typingIndicator.style.display = 'flex';
    
    try {
        // Create temporary bot response
        const botResponse = createMessage("در حال دریافت پاسخ...", false);
        
        // Prepare API request
        const currentModel = window.chatApp?.state?.currentModel || 'gpt-4o';
        const conversationId = window.chatApp?.state?.currentConversationId || null;
        
        const response = await fetch('/api/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId,
                model: currentModel
            })
        });
        
        // Handle response
        if (!response.ok) {
            throw new Error("Server error: " + response.status);
        }
        
        const data = await response.json();
        
        // Update conversation ID if new
        if (data.conversation_id && (!conversationId || conversationId !== data.conversation_id)) {
            if (window.chatApp && window.chatApp.state) {
                window.chatApp.state.currentConversationId = data.conversation_id;
            }
            
            // Update URL
            window.history.pushState({}, '', `/chat/${data.conversation_id}`);
        }
        
        // Update bot response
        if (botResponse && botResponse.querySelector('.message-content')) {
            botResponse.querySelector('.message-content').textContent = data.bot_response || "خطایی رخ داد";
        }
        
    } catch (error) {
        console.error("Error sending message:", error);
        
        // Show error message
        createMessage("متأسفانه خطایی در ارتباط با سرور رخ داد. لطفاً دوباره تلاش کنید.", false);
        
    } finally {
        // Reset processing state
        if (window.chatApp && window.chatApp.state) {
            window.chatApp.state.isProcessing = false;
        }
        
        // Hide typing indicator
        typingIndicator.style.display = 'none';
    }
} 
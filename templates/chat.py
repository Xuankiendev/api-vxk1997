<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Room - API Platform</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💬</text></svg>">
    <style>
        .chat-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            min-height: 100vh;
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 2rem;
        }

        .chat-main {
            display: flex;
            flex-direction: column;
            height: calc(100vh - 4rem);
        }

        .chat-header {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 20px 20px 0 0;
            padding: 1.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-messages {
            flex: 1;
            background: rgba(30, 41, 59, 0.4);
            backdrop-filter: blur(20px);
            border-left: 1px solid var(--border);
            border-right: 1px solid var(--border);
            padding: 1rem;
            overflow-y: auto;
            max-height: calc(100vh - 200px);
        }

        .chat-input-container {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 0 0 20px 20px;
            padding: 1.5rem 2rem;
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .chat-input {
            flex: 1;
            padding: 0.875rem 1.25rem;
            background: rgba(15, 23, 42, 0.8);
            border: 2px solid var(--border);
            border-radius: 12px;
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 500;
            resize: none;
            min-height: 44px;
            max-height: 120px;
        }

        .chat-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .send-button {
            padding: 0.875rem 1.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            border: none;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        }

        .send-button:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        }

        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .message {
            margin-bottom: 1rem;
            padding: 1rem;
            border-radius: 12px;
            animation: messageSlide 0.3s ease;
            position: relative;
        }

        .message.own {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            margin-left: 2rem;
            color: white;
        }

        .message.other {
            background: rgba(51, 65, 85, 0.6);
            margin-right: 2rem;
            border: 1px solid var(--border);
        }

        .message.system {
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.3);
            color: var(--accent);
            text-align: center;
            font-style: italic;
            margin: 0.5rem 1rem;
        }

        .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }

        .message-username {
            font-weight: 600;
            color: var(--secondary);
        }

        .message.own .message-username {
            color: rgba(255, 255, 255, 0.9);
        }

        .message-time {
            opacity: 0.7;
            font-size: 0.8rem;
        }

        .message-content {
            word-wrap: break-word;
            line-height: 1.5;
        }

        @keyframes messageSlide {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .online-users {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1.5rem;
        }

        .online-users h3 {
            margin-bottom: 1rem;
            color: var(--success);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .user-list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .user-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 8px;
            border: 1px solid var(--border);
        }

        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.875rem;
            font-weight: 600;
            color: white;
        }

        .user-status {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            margin-left: auto;
        }

        .connection-status {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1.5rem;
            text-align: center;
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.5rem;
        }

        .status-connected {
            background: var(--success);
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        }

        .status-disconnected {
            background: var(--error);
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
        }

        .status-connecting {
            background: var(--warning);
            box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .back-button {
            background: rgba(100, 255, 218, 0.2);
            border: 1px solid rgba(100, 255, 218, 0.5);
            color: var(--secondary);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .back-button:hover {
            background: rgba(100, 255, 218, 0.3);
            transform: scale(1.05);
        }

        @media (max-width: 768px) {
            .chat-container {
                grid-template-columns: 1fr;
                padding: 1rem;
            }
            
            .sidebar {
                order: -1;
            }
            
            .online-users {
                padding: 1rem;
            }
            
            .chat-main {
                height: calc(100vh - 300px);
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-main">
            <div class="chat-header">
                <div>
                    <h2 style="margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                        💬 Chat Room
                    </h2>
                    <p style="margin: 0; color: var(--text-secondary); font-size: 0.875rem;">
                        Connect with other API Platform users
                    </p>
                </div>
                <a href="/dashboard" class="back-button">← Dashboard</a>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="message system">
                    <div class="message-content">Welcome to the chat room! 🎉</div>
                </div>
            </div>
            
            <div class="chat-input-container">
                <textarea 
                    id="messageInput" 
                    class="chat-input" 
                    placeholder="Type your message..." 
                    rows="1"
                    maxlength="1000"
                ></textarea>
                <button id="sendButton" class="send-button">Send</button>
            </div>
        </div>
        
        <div class="sidebar">
            <div class="connection-status">
                <h3 style="margin-bottom: 1rem; color: var(--text-primary);">Connection</h3>
                <div id="connectionStatus">
                    <span class="status-indicator status-connecting"></span>
                    <span>Connecting...</span>
                </div>
            </div>
            
            <div class="online-users">
                <h3>🟢 Online Users (<span id="onlineCount">0</span>)</h3>
                <div class="user-list" id="userList">
                    <div class="user-item">
                        <div class="user-avatar">?</div>
                        <span>Loading...</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let websocket = null;
        let currentUser = null;
        let apiKey = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        document.addEventListener('DOMContentLoaded', function() {
            apiKey = localStorage.getItem('apiKey');
            const userEmail = localStorage.getItem('userEmail');
            
            if (!apiKey || !userEmail) {
                window.location.href = '/login';
                return;
            }
            
            currentUser = userEmail.split('@')[0];
            setupEventListeners();
            loadChatHistory();
            connectWebSocket();
            updateOnlineUsers();
        });

        function setupEventListeners() {
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            
            messageInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            });
            
            sendButton.addEventListener('click', sendMessage);
        }

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chat/${apiKey}`;
            
            websocket = new WebSocket(wsUrl);
            
            websocket.onopen = function(event) {
                console.log('WebSocket connected');
                updateConnectionStatus('connected');
                reconnectAttempts = 0;
            };
            
            websocket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            websocket.onclose = function(event) {
                console.log('WebSocket disconnected');
                updateConnectionStatus('disconnected');
                
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    updateConnectionStatus('connecting');
                    setTimeout(() => {
                        connectWebSocket();
                    }, 2000 * reconnectAttempts);
                }
            };
            
            websocket.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateConnectionStatus('disconnected');
            };
        }

        function handleWebSocketMessage(data) {
            switch(data.type) {
                case 'new_message':
                    addMessageToChat(data.data);
                    break;
                case 'user_joined':
                case 'user_left':
                    addSystemMessage(data.data.message);
                    updateOnlineUsers();
                    break;
                case 'pong':
                    // Keep alive response
                    break;
            }
        }

        function updateConnectionStatus(status) {
            const statusElement = document.getElementById('connectionStatus');
            const indicator = statusElement.querySelector('.status-indicator');
            const text = statusElement.querySelector('span');
            
            indicator.className = `status-indicator status-${status}`;
            
            switch(status) {
                case 'connected':
                    text.textContent = 'Connected';
                    break;
                case 'disconnected':
                    text.textContent = 'Disconnected';
                    break;
                case 'connecting':
                    text.textContent = 'Connecting...';
                    break;
            }
        }

        async function loadChatHistory() {
            try {
                const response = await fetch(`/api/chat/messages?apikey=${apiKey}&limit=50`);
                const data = await response.json();
                
                if (data.success) {
                    const chatMessages = document.getElementById('chatMessages');
                    // Clear loading message
                    chatMessages.innerHTML = '';
                    
                    data.messages.forEach(message => {
                        addMessageToChat(message, false);
                    });
                    
                    scrollToBottom();
                }
            } catch (error) {
                console.error('Error loading chat history:', error);
            }
        }

        async function sendMessage() {
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            const message = messageInput.value.trim();
            
            if (!message || !websocket || websocket.readyState !== WebSocket.OPEN) {
                return;
            }
            
            sendButton.disabled = true;
            sendButton.textContent = 'Sending...';
            
            try {
                const response = await fetch('/api/chat/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        apikey: apiKey,
                        message: message
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    messageInput.value = '';
                    messageInput.style.height = 'auto';
                } else {
                    alert('Error sending message: ' + data.error);
                }
            } catch (error) {
                console.error('Error sending message:', error);
                alert('Error sending message. Please try again.');
            } finally {
                sendButton.disabled = false;
                sendButton.textContent = 'Send';
                messageInput.focus();
            }
        }

        function addMessageToChat(message, animate = true) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            
            const isOwnMessage = message.username === currentUser;
            messageDiv.className = `message ${isOwnMessage ? 'own' : 'other'}`;
            
            const timestamp = new Date(message.timestamp).toLocaleString('vi-VN', {
                timeZone: 'Asia/Ho_Chi_Minh',
                hour: '2-digit',
                minute: '2-digit',
                day: '2-digit',
                month: '2-digit'
            });
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <span class="message-username">${escapeHtml(message.username)}</span>
                    <span class="message-time">${timestamp}</span>
                </div>
                <div class="message-content">${escapeHtml(message.message)}</div>
            `;
            
            chatMessages.appendChild(messageDiv);
            
            if (animate) {
                scrollToBottom();
            }
        }

        function addSystemMessage(message) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message system';
            messageDiv.innerHTML = `<div class="message-content">${escapeHtml(message)}</div>`;
            chatMessages.appendChild(messageDiv);
            scrollToBottom();
        }

        async function updateOnlineUsers() {
            try {
                const response = await fetch(`/api/chat/online-users?apikey=${apiKey}`);
                const data = await response.json();
                
                if (data.success) {
                    const onlineCount = document.getElementById('onlineCount');
                    const userList = document.getElementById('userList');
                    
                    onlineCount.textContent = data.count;
                    userList.innerHTML = '';
                    
                    data.online_users.forEach(email => {
                        const username = email.split('@')[0];
                        const userDiv = document.createElement('div');
                        userDiv.className = 'user-item';
                        userDiv.innerHTML = `
                            <div class="user-avatar">${username.charAt(0).toUpperCase()}</div>
                            <span>${escapeHtml(username)}</span>
                            <div class="user-status"></div>
                        `;
                        userList.appendChild(userDiv);
                    });
                }
            } catch (error) {
                console.error('Error updating online users:', error);
            }
        }

        function scrollToBottom() {
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Keep WebSocket alive
        setInterval(() => {
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({type: 'ping'}));
            }
        }, 30000);

        // Update online users periodically
        setInterval(updateOnlineUsers, 10000);

        // Cleanup when page unloads
        window.addEventListener('beforeunload', function() {
            if (websocket) {
                websocket.close();
            }
        });
    </script>
</body>
</html>

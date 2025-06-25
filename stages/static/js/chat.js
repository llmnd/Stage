// static/js/chat.js
document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-messages');
    const conversationId = window.location.pathname.split('/')[2];
    
    if (chatContainer && conversationId) {
        // Faire défiler vers le bas au chargement
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Rafraîchissement automatique des messages
        setInterval(fetchMessages, 3000);
        
        function fetchMessages() {
            fetch(`/chat/api/messages/${conversationId}/`)
                .then(response => response.json())
                .then(messages => {
                    chatContainer.innerHTML = '';
                    messages.forEach(message => {
                        const messageDiv = document.createElement('div');
                        messageDiv.className = `message ${message.is_me ? 'sent' : 'received'}`;
                        
                        const contentDiv = document.createElement('div');
                        contentDiv.className = 'message-content';
                        contentDiv.textContent = message.content;
                        
                        const timeDiv = document.createElement('div');
                        timeDiv.className = 'message-time';
                        timeDiv.textContent = message.timestamp;
                        
                        messageDiv.appendChild(contentDiv);
                        messageDiv.appendChild(timeDiv);
                        chatContainer.appendChild(messageDiv);
                    });
                    
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
        }
    }
});
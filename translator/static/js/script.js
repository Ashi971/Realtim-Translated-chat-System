// Role selection page
if (document.getElementById('roleForm')) {
    const roleSelect = document.getElementById('role');
    const serverOptions = document.getElementById('serverOptions');
    const clientOptions = document.getElementById('clientOptions');
    const continueBtn = document.getElementById('continueBtn');
    
    roleSelect.addEventListener('change', function() {
        serverOptions.style.display = this.value === 'server' ? 'block' : 'none';
        clientOptions.style.display = this.value === 'client' ? 'block' : 'none';
    });
    
    continueBtn.addEventListener('click', function() {
        const role = roleSelect.value;
        if (!role) return alert('Please select a role');
        
        if (role === 'server') {
            const serverLang = document.getElementById('server_lang').value;
            const clientLang = document.getElementById('client_lang').value;
            if (!serverLang || !clientLang) return alert('Please select both languages');
            const roomId = Math.random().toString(36).substring(2, 8);
            window.location.href = `/server?server_lang=${serverLang}&client_lang=${clientLang}&room_id=${roomId}`;
        } else {
            const roomId = document.getElementById('room_id').value.trim();
            if (!roomId) return alert('Please enter room ID');
            window.location.href = `/client?room_id=${roomId}`;
        }
    });
}

// Chat page functionality
if (document.getElementById('chatBox')) {
    const socket = io();
    const chatBox = document.getElementById('chatBox');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendMessage');
    const status = document.getElementById('connectionStatus');
    
    // Join room
    socket.emit('join_room', { room_id: roomId, role: role });
    
    // Connection events
    socket.on('server_ready', () => {
        if (role === 'server') status.textContent = 'Waiting for client...';
    });
    
    socket.on('client_ready', () => {
        if (role === 'client') status.textContent = 'Connected to server!';
    });
    
    socket.on('connection_established', () => {
        status.textContent = 'Connected! Start chatting';
        status.style.color = 'green';
    });
    
    // Message handling
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    socket.on('receive_message', (data) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${data.sender === role ? 'sent' : 'received'}`;
        msgDiv.innerHTML = `
            <div class="message-info">${new Date().toLocaleTimeString()}</div>
            ${data.original ? `<div class="original">${data.original}</div>` : ''}
            <div class="text">${data.text}</div>
        `;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    });
    
    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;
        
        socket.emit('send_message', {
            room_id: roomId,
            text: text,
            sender: role
        });
        
        messageInput.value = '';
    }
}
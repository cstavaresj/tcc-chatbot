document.addEventListener('DOMContentLoaded', () => {

    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) { return; }

    const BACKEND_URL = 'https://SEU-DOMINIO-DO-NGROK.app/chat';
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const settingsBtn = document.getElementById('settings-btn');
    const settingsMenu = document.getElementById('settings-menu');
    const lightModeBtn = document.getElementById('light-mode-btn');
    const darkModeBtn = document.getElementById('dark-mode-btn');

    let chatHistory = [];
    let sessionId = null;

    function formatTextToHTML(text) {
        if (typeof text !== 'string') return '';
        return text
            .replace(/\*(.*?)\*/g, '<strong>$1</strong>')
            .replace(/\_(.*?)\_/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
    
    function addMessage(text, type, buttons = [], isReloading = false) {
        if (typeof text !== 'string' || text.trim() === '') return;

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', type);

        const contentP = document.createElement('p');
        contentP.innerHTML = formatTextToHTML(text);
        messageDiv.appendChild(contentP);

        // Lógica para renderizar botões
        if (buttons && buttons.length > 0) {
            const buttonsContainer = document.createElement('div');
            buttonsContainer.classList.add('message-buttons');
            buttons.forEach(buttonInfo => {
                const buttonElement = document.createElement('button');
                buttonElement.textContent = buttonInfo.label;
                buttonElement.addEventListener('click', () => {
                    handleSendMessage(buttonInfo.value);
                    buttonsContainer.querySelectorAll('button').forEach(btn => { btn.disabled = true; });
                });
                buttonsContainer.appendChild(buttonElement);
            });
            messageDiv.appendChild(buttonsContainer);
        }

        const metaDiv = document.createElement('div');
        metaDiv.classList.add('message-meta');
        const timeSpan = document.createElement('span');
        timeSpan.textContent = `${new Date().getHours().toString().padStart(2, '0')}:${new Date().getMinutes().toString().padStart(2, '0')}`;
        metaDiv.appendChild(timeSpan);

        if (type === 'sent') {
            const ticksSpan = document.createElement('span');
            ticksSpan.classList.add('ticks');
            ticksSpan.innerHTML = '<span class="tick1">✓</span><span class="tick2">✓</span>';
            setTimeout(() => ticksSpan.classList.add('delivered'), 1000);
            setTimeout(() => ticksSpan.classList.add('read'), 2000);
            metaDiv.appendChild(ticksSpan);
        }
        messageDiv.appendChild(metaDiv);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        if (!isReloading) {
            chatHistory.push({ text, type, buttons });
            localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        }
    }

    async function handleSendMessage(messageTextFromButton = null) {
        const messageText = messageTextFromButton || messageInput.value;
        if (messageText.trim() === '') return;

        if (!messageTextFromButton) {
            messageInput.value = '';
        }
        addMessage(messageText, 'sent');

        try {
            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText, sessionId: sessionId })
            });
            if (!response.ok) throw new Error(`Erro de rede: ${response.status}`);
            
            const data = await response.json();
            if (data && data.reply) {
                setTimeout(() => {                    
                    addMessage(data.reply, 'received', data.buttons || []);
                }, 1500);
            }
        } catch (error) {
            console.error('Falha ao comunicar com o servidor:', error);
            addMessage('Desculpe, não consegui conectar ao servidor.', 'received');
        }
    }

    function initializeChat() {
        sessionId = localStorage.getItem('chatSessionId');
        if (!sessionId) {
            sessionId = Math.random().toString(36).substring(2, 9);
            localStorage.setItem('chatSessionId', sessionId);
        }

        const savedHistory = localStorage.getItem('chatHistory');
        if (savedHistory) {
            try {
                chatHistory = JSON.parse(savedHistory);
            } catch (e) {
                chatHistory = [];
                localStorage.removeItem('chatHistory');
            }
        }

        if (chatHistory.length === 0) {
            const initialMessages = [
                { text: `Olá! Bem-vindo(a) ao chat da <b>Pamonha Express</b>! 🌽<br><br>Este é um projeto de TCC de Carlos Soares, aluno da Universidade de Uberaba, <i>com fins exclusivamente acadêmicos</i>. 🎓<br><br>⚠️<b>Atenção⚠️</b> O delivery é fictício. Nenhuma cobrança será feita e nenhum produto será entregue.<br><br>Sua participação é fundamental para este teste com usuários reais. Você pode encerrar a interação a qualquer momento digitando "sair".`, type: 'received' },
                { text: `Ao final da interação, faremos algumas perguntas rápidas para avaliar sua experiência. 📝<br><br>Agradecemos sua colaboração!👍`, type: 'received' },
                { text: `Para começar, envie uma mensagem.`, type: 'received' }
            ];
            chatHistory.push(...initialMessages);
            localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        }

        chatMessages.innerHTML = '';
        chatHistory.forEach(msg => {
            addMessage(msg.text, msg.type, msg.buttons || [], true);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    sendButton.addEventListener('click', () => handleSendMessage());
    messageInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSendMessage(); });
    settingsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        settingsMenu.classList.toggle('hidden');
    });

    lightModeBtn.addEventListener('click', () => {
        document.body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        settingsMenu.classList.add('hidden');
    });

    darkModeBtn.addEventListener('click', () => {
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        settingsMenu.classList.add('hidden');
    });
    
    window.addEventListener('click', () => {
        if (!settingsMenu.classList.contains('hidden')) {
            settingsMenu.classList.add('hidden');
        }
    });

    window.addEventListener('storage', (event) => { if (event.key === 'chatHistory') { location.reload(); } });
    
    initializeChat();
});
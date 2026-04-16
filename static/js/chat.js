document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.querySelector('.chat-messages');
    const chatInput = document.querySelector('.chat-input input');
    const sendButton = document.querySelector('.chat-input button');
    const summaryButton = document.getElementById('summary-button');

    // Fonction pour ajouter un message au chat
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Fonction pour envoyer un message
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Afficher le message de l'utilisateur
        addMessage(message, true);
        chatInput.value = '';

        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            // Afficher la réponse du bot
            addMessage(data.response);

            // Si des symptômes sont détectés, les afficher
            if (data.symptoms && data.symptoms.length > 0) {
                const symptomsDiv = document.createElement('div');
                symptomsDiv.className = 'message bot-message symptoms';
                symptomsDiv.innerHTML = `
                    <strong>Symptômes détectés :</strong><br>
                    ${data.symptoms.join(', ')}
                `;
                chatMessages.appendChild(symptomsDiv);
            }

            // Si une spécialité est suggérée, l'afficher
            if (data.specialty) {
                const specialtyDiv = document.createElement('div');
                specialtyDiv.className = 'message bot-message specialty';
                specialtyDiv.innerHTML = `
                    <strong>Spécialité suggérée :</strong><br>
                    ${data.specialty}
                `;
                chatMessages.appendChild(specialtyDiv);
            }

        } catch (error) {
            console.error('Erreur:', error);
            addMessage('Désolé, une erreur s\'est produite. Veuillez réessayer.');
        }
    }

    // Fonction pour obtenir le résumé de la conversation
    async function getConversationSummary() {
        try {
            const response = await fetch('/get_conversation_summary');
            const data = await response.json();
            
            const summaryDiv = document.createElement('div');
            summaryDiv.className = 'message bot-message summary';
            summaryDiv.innerHTML = `
                <strong>Résumé de la conversation :</strong><br>
                ${data.summary}
            `;
            chatMessages.appendChild(summaryDiv);
        } catch (error) {
            console.error('Erreur:', error);
            addMessage('Erreur lors de la récupération du résumé.');
        }
    }

    // Événements
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    if (summaryButton) {
        summaryButton.addEventListener('click', getConversationSummary);
    }

    // Style CSS pour les nouveaux éléments
    const style = document.createElement('style');
    style.textContent = `
        .symptoms, .specialty, .summary {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            margin: 10px 0;
            padding: 10px 15px;
        }
        
        .symptoms strong, .specialty strong, .summary strong {
            color: #1976d2;
        }
    `;
    document.head.appendChild(style);
}); 
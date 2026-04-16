document.addEventListener('DOMContentLoaded', function() {
    // Gestion du chat
    const chatForm = document.getElementById('chat-form');
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');

    if (chatForm) {
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const message = messageInput.value.trim();
            if (!message) return;

            // Ajouter le message de l'utilisateur
            addMessage(message, 'user');
            messageInput.value = '';

            try {
                const response = await fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                
                if (data.error) {
                    addMessage('Désolé, une erreur est survenue. Veuillez réessayer.', 'bot');
                    console.error('Erreur:', data.error);
                    return;
                }

                // Ajouter la réponse du bot
                addMessage(data.response, 'bot');
                
                // Afficher les symptômes et la spécialité si présents
                if (data.symptoms && data.symptoms.length > 0) {
                    const symptomsText = `Symptômes détectés : ${data.symptoms.join(', ')}`;
                    addInfoMessage(symptomsText);
                }
                if (data.specialty) {
                    const specialtyText = `Spécialité suggérée : ${data.specialty}`;
                    addInfoMessage(specialtyText);
                }
            } catch (error) {
                console.error('Erreur:', error);
                addMessage('Désolé, une erreur est survenue. Veuillez réessayer.', 'bot');
            }
        });
    }

    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Faire défiler vers le bas
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addInfoMessage(content) {
        const infoDiv = document.createElement('div');
        infoDiv.className = 'info-message';
        infoDiv.textContent = content;
        
        chatMessages.appendChild(infoDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Gestion du tableau de bord
    const dashboardStats = document.getElementById('dashboard-stats');
    if (dashboardStats) {
        updateDashboardStats();
    }

    async function updateDashboardStats() {
        try {
            const response = await fetch('/get_conversation_summary');
            const data = await response.json();
            
            if (data.summary) {
                const summaryDiv = document.getElementById('conversation-summary');
                if (summaryDiv) {
                    summaryDiv.textContent = data.summary;
                }
            }
        } catch (error) {
            console.error('Erreur lors de la mise à jour des statistiques:', error);
        }
    }

    // Gestion des formulaires de connexion et d'inscription
    const loginForm = document.querySelector('form[action="/login"]');
    const signupForm = document.querySelector('form[action="/signup"]');

    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const username = loginForm.querySelector('input[name="username"]').value;
            const password = loginForm.querySelector('input[name="password"]').value;

            if (!username || !password) {
                e.preventDefault();
                alert('Veuillez remplir tous les champs');
            }
        });
    }

    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            const username = signupForm.querySelector('input[name="username"]').value;
            const email = signupForm.querySelector('input[name="email"]').value;
            const password = signupForm.querySelector('input[name="password"]').value;
            const confirmPassword = signupForm.querySelector('input[name="confirm_password"]').value;

            if (!username || !email || !password || !confirmPassword) {
                e.preventDefault();
                alert('Veuillez remplir tous les champs');
                return;
            }

            if (password !== confirmPassword) {
                e.preventDefault();
                alert('Les mots de passe ne correspondent pas');
                return;
            }

            // Ne pas empêcher la soumission si tout est valide
            const submitButton = signupForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.classList.add('loading');
            }
        });
    }

    // Gestion du tableau de bord médecin
    loadStats();
    loadRecentConsultations();
});

// Fonction pour charger les statistiques
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // Mettre à jour les statistiques dans l'interface
        updateStats(data);
    } catch (error) {
        console.error('Erreur lors du chargement des statistiques:', error);
    }
}

// Fonction pour mettre à jour les statistiques
function updateStats(data) {
    const stats = {
        patients: document.querySelector('.stat-card:nth-child(1) .stat-number'),
        consultations: document.querySelector('.stat-card:nth-child(2) .stat-number'),
        timeAverage: document.querySelector('.stat-card:nth-child(3) .stat-number'),
        satisfaction: document.querySelector('.stat-card:nth-child(4) .stat-number')
    };

    if (stats.patients) stats.patients.textContent = data.patients || '0';
    if (stats.consultations) stats.consultations.textContent = data.consultations || '0';
    if (stats.timeAverage) stats.timeAverage.textContent = `${data.timeAverage || '0'} min`;
    if (stats.satisfaction) stats.satisfaction.textContent = `${data.satisfaction || '0'}%`;
}

// Fonction pour charger les consultations récentes
async function loadRecentConsultations() {
    try {
        const response = await fetch('/api/recent-consultations');
        const data = await response.json();
        
        // Mettre à jour la liste des consultations
        updateConsultationsList(data);
    } catch (error) {
        console.error('Erreur lors du chargement des consultations:', error);
    }
}

// Fonction pour mettre à jour la liste des consultations
function updateConsultationsList(consultations) {
    const consultationsList = document.querySelector('.consultations-list');
    if (!consultationsList) return;

    consultationsList.innerHTML = ''; // Vider la liste

    consultations.forEach(consultation => {
        const consultationCard = document.createElement('div');
        consultationCard.className = 'consultation-card';
        consultationCard.innerHTML = `
            <div class="consultation-header">
                <span class="patient-name">${consultation.patientName}</span>
                <span class="consultation-time">${consultation.time}</span>
            </div>
            <div class="consultation-content">
                <p class="symptoms">Symptômes: ${consultation.symptoms}</p>
                <p class="specialty">Spécialité suggérée: ${consultation.specialty}</p>
            </div>
        `;
        consultationsList.appendChild(consultationCard);
    });
}

// Gestion des outils médicaux
function showPatientHistory() {
    // À implémenter : afficher l'historique des patients
    alert('Fonctionnalité en cours de développement');
}

function showMedicalGuidelines() {
    // À implémenter : afficher les guides médicaux
    alert('Fonctionnalité en cours de développement');
}

function showDrugInteractions() {
    // À implémenter : afficher les interactions médicamenteuses
    alert('Fonctionnalité en cours de développement');
}

function showEmergencyProtocols() {
    // À implémenter : afficher les protocoles d'urgence
    alert('Fonctionnalité en cours de développement');
} 
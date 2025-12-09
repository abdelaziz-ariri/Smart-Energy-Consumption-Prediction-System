class EnergyDashboard {
    constructor() {
        this.charts = {};
        this.init();
    }

    init() {
        this.loadCurrentConsumption();
        this.loadHistoricalData('7d');
        this.setupEventListeners();
        this.checkNotifications();
        
        // Vérifier les notifications toutes les 30 secondes
        setInterval(() => this.checkNotifications(), 30000);
    }

    setupEventListeners() {
        // Boutons de période historique
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const period = e.target.dataset.period;
                this.loadHistoricalData(period);
                
                // Mettre à jour le bouton actif
                document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        // Bouton de prédiction
        const predictBtn = document.getElementById('predict-btn');
        if (predictBtn) {
            predictBtn.addEventListener('click', () => this.predictConsumption());
        }

        // Sélecteur de jours de prédiction
        const daysSelect = document.getElementById('predict-days');
        if (daysSelect) {
            daysSelect.addEventListener('change', () => this.predictConsumption());
        }

        // Bouton pour générer des données de démo
        const demoBtn = document.getElementById('demo-data-btn');
        if (demoBtn) {
            demoBtn.addEventListener('click', () => this.generateDemoData());
        }

        // Bouton pour marquer les notifications comme lues
        const markReadBtn = document.getElementById('mark-read-btn');
        if (markReadBtn) {
            markReadBtn.addEventListener('click', () => this.markNotificationsRead());
        }
    }

    async loadCurrentConsumption() {
        try {
            const response = await fetch('/api/consumption/current');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateStats(data);
        } catch (error) {
            console.error('Erreur lors du chargement des données:', error);
            this.showError('Impossible de charger les données actuelles');
        }
    }

    async loadHistoricalData(period) {
        try {
            const container = document.getElementById('historical-chart');
            if (container) {
                container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            }
            
            const response = await fetch(`/api/consumption/historical?period=${period}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.renderHistoricalChart(data.graph);
        } catch (error) {
            console.error('Erreur lors du chargement des données historiques:', error);
            this.showError('Impossible de charger les données historiques');
        }
    }

    async predictConsumption() {
        try {
            const days = document.getElementById('predict-days').value;
            const container = document.getElementById('prediction-chart');
            
            if (container) {
                container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
            }
            
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ days: parseInt(days) })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.renderPredictionChart(data.graph);
            this.handleTrendWarnings(data.trend_warnings);
            
        } catch (error) {
            console.error('Erreur lors de la prédiction:', error);
            this.showError('Impossible de générer la prédiction');
        }
    }

    async checkNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateNotificationBadge(data.unread_count);
            
            // Si nous sommes sur la page des notifications, les afficher
            if (window.location.pathname.includes('notifications')) {
                this.displayNotifications(data.notifications);
            }
            
        } catch (error) {
            console.error('Erreur lors de la vérification des notifications:', error);
        }
    }

    async markNotificationsRead() {
        try {
            const response = await fetch('/api/notifications/mark-read', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateNotificationBadge(0);
                this.checkNotifications();
            }
        } catch (error) {
            console.error('Erreur:', error);
        }
    }

    async generateDemoData() {
        if (!confirm('Générer des données de démonstration ? Cela écrasera les données existantes.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/generate-demo-data', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Données de démonstration générées avec succès !');
                this.loadCurrentConsumption();
                this.loadHistoricalData('7d');
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la génération des données');
        }
    }

    updateStats(data) {
        const totalElement = document.getElementById('total-consumption');
        const avgElement = document.getElementById('avg-consumption');
        const peakElement = document.getElementById('peak-hour');
        const dataPointsElement = document.getElementById('data-points');
        
        if (totalElement) totalElement.textContent = `${data.total_consumption} kWh`;
        if (avgElement) avgElement.textContent = `${data.avg_consumption} kWh/h`;
        if (peakElement) peakElement.textContent = data.peak_hour !== null ? `${data.peak_hour}h` : 'N/A';
        if (dataPointsElement) dataPointsElement.textContent = data.data_points;
    }

    renderHistoricalChart(graphJson) {
        const container = document.getElementById('historical-chart');
        if (!container) return;
        
        try {
            const graph = JSON.parse(graphJson);
            Plotly.newPlot(container, graph.data, graph.layout, {
                responsive: true,
                displayModeBar: true
            });
        } catch (error) {
            console.error('Erreur lors du rendu du graphique:', error);
            container.innerHTML = '<p class="error">Erreur lors de l\'affichage du graphique</p>';
        }
    }

    renderPredictionChart(graphJson) {
        const container = document.getElementById('prediction-chart');
        if (!container) return;
        
        try {
            const graph = JSON.parse(graphJson);
            Plotly.newPlot(container, graph.data, graph.layout, {
                responsive: true,
                displayModeBar: true
            });
        } catch (error) {
            console.error('Erreur lors du rendu du graphique:', error);
            container.innerHTML = '<p class="error">Erreur lors de l\'affichage de la prédiction</p>';
        }
    }

    updateNotificationBadge(count) {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-flex' : 'none';
        }
    }

    displayNotifications(notifications) {
        const container = document.getElementById('notifications-container');
        if (!container) return;
        
        if (notifications.length === 0) {
            container.innerHTML = '<p class="empty">Aucune notification</p>';
            return;
        }
        
        const notificationsHtml = notifications.map(notification => `
            <div class="notification-item">
                <div class="notification-icon ${notification.level}">
                    <i class="fas fa-${this.getNotificationIcon(notification.level)}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${this.formatTime(notification.created_at)}</div>
                </div>
                ${!notification.read ? '<span class="unread-dot"></span>' : ''}
            </div>
        `).join('');
        
        container.innerHTML = notificationsHtml;
    }

    handleTrendWarnings(warnings) {
        if (!warnings || warnings.length === 0) return;
        
        // Afficher la première alerte critique
        const criticalWarning = warnings.find(w => w.level === 'critical');
        if (criticalWarning) {
            this.showAlert(criticalWarning.title, criticalWarning.message, 'danger');
        }
    }

    getNotificationIcon(level) {
        switch(level) {
            case 'critical': return 'exclamation-triangle';
            case 'warning': return 'exclamation-circle';
            default: return 'info-circle';
        }
    }

    formatTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('fr-FR');
    }

    showAlert(title, message, type = 'info') {
        // Créer une alerte temporaire
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            <strong>${title}</strong>
            <p>${message}</p>
        `;
        
        document.body.appendChild(alert);
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    showError(message) {
        this.showAlert('Erreur', message, 'danger');
    }
}

// Initialiser le tableau de bord lorsque la page est chargée
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new EnergyDashboard();
});
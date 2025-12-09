import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
import json
from dotenv import load_dotenv
import plotly
import plotly.express as px
from model import EnergyPredictor
from utils.database import MongoDBHandler
from utils.notifications import NotificationManager

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configuration MongoDB
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/energy_dashboard')

# Initialiser les handlers
db_handler = MongoDBHandler(app.config['MONGO_URI'])
print("*************")
print(app.config['MONGO_URI'])
print("*************")
notification_manager = NotificationManager(db_handler)

# Configuration Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modèle utilisateur
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.role = user_data.get('role', 'user')
        self.created_at = user_data.get('created_at', datetime.utcnow())

from bson import ObjectId

@login_manager.user_loader
def load_user(user_id):
    try:
        # Convertit le user_id string en ObjectId pour MongoDB
        user_data = db_handler.get_user_by_id(ObjectId(user_id))
        if user_data:
            return User(user_data)
    except Exception as e:
        print("Erreur load_user:", e)
    return None

# Routes d'authentification
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = db_handler.get_user_by_username(username)
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Identifiants incorrects')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if db_handler.get_user_by_username(username):
            return render_template('register.html', error='Nom d\'utilisateur déjà existant')
        
        hashed_password = generate_password_hash(password)
        user_data = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'role': 'admin',
            'created_at': datetime.utcnow()
        }
        
        db_handler.create_user(user_data)
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Routes principales
@app.route('/')
@login_required
def dashboard():
    return render_template('index.html', user=current_user)

@app.route('/api/consumption/current')
@login_required
def get_current_consumption():
    """Récupérer la consommation actuelle"""
    try:
        # Récupérer les données des dernières 24 heures
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        
        consumption_data = db_handler.get_consumption_data(start_date, end_date)
        
        # Calculer la consommation totale
        total_consumption = sum(item['value'] for item in consumption_data)
        
        # Calculer la consommation moyenne par heure
        hourly_data = {}
        for item in consumption_data:
            hour = item['timestamp'].hour
            hourly_data[hour] = hourly_data.get(hour, 0) + item['value']
        
        avg_consumption = total_consumption / 24 if len(hourly_data) > 0 else 0
        
        return jsonify({
            'total_consumption': round(total_consumption, 2),
            'avg_consumption': round(avg_consumption, 2),
            'peak_hour': max(hourly_data, key=hourly_data.get) if hourly_data else None,
            'data_points': len(consumption_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/consumption/historical')
@login_required
def get_historical_data():
    """Récupérer les données historiques"""
    try:
        period = request.args.get('period', '7d')  # 7d, 30d, 90d
        
        if period == '7d':
            days = 7
        elif period == '30d':
            days = 30
        else:
            days = 90
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        consumption_data = db_handler.get_consumption_data(start_date, end_date)
        
        # Organiser les données par jour
        daily_data = {}
        for item in consumption_data:
            date_str = item['timestamp'].strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = 0
            daily_data[date_str] += item['value']
        
        # Créer le graphique
        dates = list(daily_data.keys())
        values = list(daily_data.values())
        
        fig = px.line(
            x=dates, 
            y=values,
            title=f'Consommation énergétique - {days} derniers jours',
            labels={'x': 'Date', 'y': 'Consommation (kWh)'}
        )
        
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return jsonify({'graph': graph_json, 'data': daily_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
@login_required
def predict_consumption():
    """Prédire la consommation future"""
    try:
        data = request.json
        days_to_predict = int(data.get('days', 7))
        
        # Récupérer les données historiques pour l'entraînement
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)  # 90 jours d'historique
        
        historical_data = db_handler.get_consumption_data(start_date, end_date)
        
        if len(historical_data) < 10:
            return jsonify({'error': 'Données insuffisantes pour la prédiction'}), 400
        
        # Préparer les données pour le modèle
        df = pd.DataFrame([{
            'timestamp': item['timestamp'],
            'value': item['value']
        } for item in historical_data])
        
        df.set_index('timestamp', inplace=True)
        
        # Utiliser le modèle pour prédire
        predictor = EnergyPredictor()
        predictions = predictor.predict(df, days_to_predict)
        
        # Créer les dates de prédiction
        prediction_dates = [end_date + timedelta(days=i+1) for i in range(days_to_predict)]
        
        # Créer le graphique
        fig = px.line(
            x=prediction_dates,
            y=predictions,
            title=f'Prédiction de consommation - {days_to_predict} prochains jours',
            labels={'x': 'Date', 'y': 'Consommation prédite (kWh)'}
        )
        
        # Ajouter une ligne pour l'historique récent
        recent_dates = [item['timestamp'] for item in historical_data[-7:]]
        recent_values = [item['value'] for item in historical_data[-7:]]
        
        fig.add_scatter(
            x=recent_dates,
            y=recent_values,
            mode='lines',
            name='Historique récent',
            line=dict(color='gray', dash='dash')
        )
        
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Vérifier les tendances pour les notifications
        trend_notifications = notification_manager.check_trends(predictions)
        
        return jsonify({
            'predictions': predictions.tolist(),
            'dates': [d.strftime('%Y-%m-%d') for d in prediction_dates],
            'graph': graph_json,
            'trend_warnings': trend_notifications
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications')
@login_required
def get_notifications():
    """Récupérer les notifications"""
    try:
        notifications = db_handler.get_notifications(current_user.id)
        unread_count = sum(1 for n in notifications if not n.get('read', False))
        
        return jsonify({
            'notifications': notifications,
            'unread_count': unread_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    """Marquer les notifications comme lues"""
    try:
        db_handler.mark_all_notifications_read(current_user.id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/historique')
@login_required
def historique():
    return render_template('historique.html', user=current_user)

@app.route('/predictions')
@login_required
def predictions():
    return render_template('predictions.html', user=current_user)

@app.route('/notifications')
@login_required
def notifications_page():
    return render_template('notifications.html', user=current_user)

# Route pour générer des données de démonstration
@app.route('/api/generate-demo-data', methods=['POST'])
@login_required
def generate_demo_data():
    """Générer des données de démonstration"""
    try:
        if current_user.role != 'admin':
            return jsonify({'error': 'Non autorisé'}), 403
        
        db_handler.generate_demo_data()
        return jsonify({'success': True, 'message': 'Données de démonstration générées'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
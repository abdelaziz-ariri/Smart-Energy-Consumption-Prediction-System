from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDBHandler:
    def __init__(self, mongo_uri=None):
        if mongo_uri is None:
            mongo_uri = os.getenv('MONGO_URI')
        
        if not mongo_uri:
            raise ValueError("MONGO_URI n'est pas défini dans les variables d'environnement")
        
        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Tester la connexion
            self.client.admin.command('ping')
            self.db = self.client.energy_dashboard
            print("✅ Connecté à MongoDB Atlas avec succès!")
        except ConnectionFailure as e:
            print(f"❌ Échec de connexion à MongoDB: {e}")
            raise
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            raise
    
    def test_connection(self):
        """Tester la connexion à MongoDB"""
        try:
            self.client.admin.command('ping')
            return True, "Connexion réussie à MongoDB Atlas"
        except ConnectionFailure as e:
            return False, f"Échec de connexion: {e}"
    
    def get_consumption_data(self, start_date, end_date, source=None):
        """Récupérer les données de consommation dans une période"""
        collection = self.db.consumption
        
        query = {
            'timestamp': {'$gte': start_date, '$lte': end_date}
        }
        
        if source:
            query['source'] = source
        
        try:
            return list(collection.find(query).sort('timestamp', ASCENDING))
        except Exception as e:
            print(f"Erreur lors de la récupération des données: {e}")
            return []
    
    def get_user_by_id(self, user_id):
        """Récupérer un utilisateur par son ID"""
        collection = self.db.users
        return collection.find_one({'_id': user_id})
    
    def get_user_by_username(self, username):
        """Récupérer un utilisateur par son nom d'utilisateur"""
        collection = self.db.users
        return collection.find_one({'username': username})
    
    def get_user_by_email(self, email):
        """Récupérer un utilisateur par son email"""
        collection = self.db.users
        return collection.find_one({'email': email})
    
    def create_user(self, user_data):
        """Créer un nouvel utilisateur"""
        collection = self.db.users
        
        # Vérifier si l'utilisateur existe déjà
        if collection.find_one({'username': user_data['username']}):
            return None, "Nom d'utilisateur déjà utilisé"
        
        if collection.find_one({'email': user_data['email']}):
            return None, "Email déjà utilisé"
        
        try:
            result = collection.insert_one(user_data)
            return result.inserted_id, "Utilisateur créé avec succès"
        except Exception as e:
            return None, f"Erreur lors de la création: {e}"
    
    def get_notifications(self, user_id, limit=50, unread_only=False):
        """Récupérer les notifications d'un utilisateur"""
        collection = self.db.notifications
        
        query = {'user_id': user_id}
        if unread_only:
            query['read'] = False
        
        try:
            return list(collection.find(query)
                       .sort('created_at', DESCENDING)
                       .limit(limit))
        except Exception as e:
            print(f"Erreur lors de la récupération des notifications: {e}")
            return []
    
    def create_notification(self, user_id, title, message, level='info', metadata=None):
        """Créer une nouvelle notification"""
        collection = self.db.notifications
        
        notification = {
            'user_id': user_id,
            'title': title,
            'message': message,
            'level': level,  # info, warning, critical
            'read': False,
            'created_at': datetime.utcnow(),
            'metadata': metadata or {}
        }
        
        try:
            result = collection.insert_one(notification)
            return result.inserted_id
        except Exception as e:
            print(f"Erreur lors de la création de la notification: {e}")
            return None
    
    def mark_notification_read(self, notification_id, user_id):
        """Marquer une notification comme lue"""
        collection = self.db.notifications
        return collection.update_one(
            {'_id': notification_id, 'user_id': user_id},
            {'$set': {'read': True, 'read_at': datetime.utcnow()}}
        )
    
    def mark_all_notifications_read(self, user_id):
        """Marquer toutes les notifications comme lues"""
        collection = self.db.notifications
        return collection.update_many(
            {'user_id': user_id, 'read': False},
            {'$set': {'read': True, 'read_at': datetime.utcnow()}}
        )
    
    def save_prediction(self, user_id, predictions_data, model_version="1.0"):
        """Sauvegarder une prédiction dans la base de données"""
        collection = self.db.predictions
        
        prediction_doc = {
            'user_id': user_id,
            'predictions': predictions_data.get('predictions', []),
            'dates': predictions_data.get('dates', []),
            'model_version': model_version,
            'created_at': datetime.utcnow(),
            'metadata': predictions_data.get('metadata', {})
        }
        
        try:
            result = collection.insert_one(prediction_doc)
            return result.inserted_id
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la prédiction: {e}")
            return None
    
    def get_user_predictions(self, user_id, limit=20):
        """Récupérer les prédictions d'un utilisateur"""
        collection = self.db.predictions
        return list(collection.find({'user_id': user_id})
                   .sort('created_at', DESCENDING)
                   .limit(limit))
    
    def generate_demo_data(self, days=90, user_id=None):
        """Générer des données de démonstration réalistes"""
        collection = self.db.consumption
        
        # Supprimer les anciennes données de démo
        collection.delete_many({'source': 'demo'})
        
        # Générer les dates
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        data_points = []
        current_date = start_date
        
        # Coefficients saisonniers (simulation)
        seasonal_coeff = {
            0: 1.0,  # Janvier
            1: 1.0,  # Février
            2: 0.9,  # Mars
            3: 0.8,  # Avril
            4: 0.7,  # Mai
            5: 0.7,  # Juin
            6: 0.8,  # Juillet
            7: 0.9,  # Août
            8: 1.0,  # Septembre
            9: 1.1,  # Octobre
            10: 1.2, # Novembre
            11: 1.3  # Décembre
        }
        
        while current_date <= end_date:
            # Coefficient basé sur le mois
            month = current_date.month - 1
            seasonal = seasonal_coeff.get(month, 1.0)
            
            # Variation jour/semaine
            day_of_week = current_date.weekday()
            is_weekend = day_of_week >= 5
            day_factor = 1.2 if is_weekend else 1.0
            
            # Valeur de base
            base_value = 100 * seasonal * day_factor
            
            # Ajouter des variations aléatoires
            for hour in range(24):
                hour_date = current_date + timedelta(hours=hour)
                
                # Variation horaire (pic en soirée)
                if 18 <= hour < 22:
                    hour_factor = 1.5  # Pic du soir
                elif 8 <= hour < 12:
                    hour_factor = 1.2  # Matinée
                elif 0 <= hour < 6:
                    hour_factor = 0.6  # Nuit
                else:
                    hour_factor = 1.0
                
                # Variation aléatoire
                random_variation = random.uniform(-15, 20)
                
                # Valeur finale
                value = max(10, base_value * hour_factor + random_variation)
                
                data_point = {
                    'timestamp': hour_date,
                    'value': round(value, 2),
                    'unit': 'kWh',
                    'source': 'demo',
                    'created_at': datetime.utcnow(),
                    'user_id': user_id
                }
                
                data_points.append(data_point)
            
            # Passer au jour suivant
            current_date += timedelta(days=1)
            
            # Insérer par lots pour éviter les problèmes de mémoire
            if len(data_points) >= 1000:
                collection.insert_many(data_points)
                data_points = []
        
        # Insérer les données restantes
        if data_points:
            collection.insert_many(data_points)
        
        # Créer des statistiques résumées
        self.create_demo_stats()
        
        return len(data_points)
    
    def create_demo_stats(self):
        """Créer des statistiques de démonstration"""
        collection = self.db.stats
        
        stats = {
            'total_data_points': 2160,  # 90 jours * 24 heures
            'average_consumption': 85.5,
            'peak_consumption': 187.3,
            'lowest_consumption': 23.1,
            'updated_at': datetime.utcnow(),
            'source': 'demo'
        }
        
        collection.update_one(
            {'source': 'demo'},
            {'$set': stats},
            upsert=True
        )
    
    def get_database_stats(self):
        """Obtenir des statistiques sur la base de données"""
        stats = {
            'consumption_count': self.db.consumption.count_documents({}),
            'users_count': self.db.users.count_documents({}),
            'notifications_count': self.db.notifications.count_documents({}),
            'predictions_count': self.db.predictions.count_documents({}),
            'last_update': datetime.utcnow()
        }
        return stats
    
    def create_indexes(self):
        """Créer les index pour optimiser les requêtes"""
        try:
            # Index pour les données de consommation
            self.db.consumption.create_index([('timestamp', ASCENDING)])
            self.db.consumption.create_index([('user_id', ASCENDING)])
            
            # Index pour les utilisateurs
            self.db.users.create_index([('username', ASCENDING)], unique=True)
            self.db.users.create_index([('email', ASCENDING)], unique=True)
            
            # Index pour les notifications
            self.db.notifications.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])
            self.db.notifications.create_index([('read', ASCENDING)])
            
            # Index pour les prédictions
            self.db.predictions.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])
            
            print("✅ Index créés avec succès!")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la création des index: {e}")
            return False
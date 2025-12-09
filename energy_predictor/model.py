import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

class EnergyPredictor:
    def __init__(self, model_path=None):
        """Initialiser le prédicteur d'énergie"""
        if model_path and os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
        else:
            # Modèle par défaut (simplifié)
            self.model = self.create_default_model()
    
    def create_default_model(self):
        """Créer un modèle par défaut si aucun modèle n'est fourni"""
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        return model
    
    def predict(self, historical_data, days_to_predict):
        """
        Prédire la consommation future
        
        Args:
            historical_data: DataFrame avec index de timestamp et colonne 'value'
            days_to_predict: Nombre de jours à prédire
        
        Returns:
            Array des prédictions
        """
        try:
            # Si un vrai modèle est chargé
            if hasattr(self.model, 'predict'):
                # Préparer les features pour la prédiction
                X_future = self.prepare_future_features(days_to_predict)
                predictions = self.model.predict(X_future)
                return predictions
            else:
                # Simulation de prédiction pour la démo
                return self.simulate_predictions(historical_data, days_to_predict)
        except Exception as e:
            print(f"Erreur lors de la prédiction: {e}")
            return self.simulate_predictions(historical_data, days_to_predict)
    
    def simulate_predictions(self, historical_data, days_to_predict):
        """Simuler des prédictions pour la démonstration"""
        # Moyenne mobile sur les 7 derniers jours
        if len(historical_data) > 7:
            last_values = historical_data['value'].tail(7).values
            avg_value = np.mean(last_values)
            std_value = np.std(last_values)
        else:
            avg_value = 100
            std_value = 20
        
        # Générer des prédictions avec une tendance saisonnière
        predictions = []
        for i in range(days_to_predict):
            # Ajouter une composante saisonnière hebdomadaire
            day_of_week = (datetime.now() + timedelta(days=i)).weekday()
            
            # Facteur saisonnier (weekend vs semaine)
            seasonal_factor = 1.2 if day_of_week >= 5 else 1.0  # Weekend > semaine
            
            # Ajouter un peu de bruit
            noise = np.random.normal(0, std_value * 0.1)
            
            # Valeur prédite
            pred_value = avg_value * seasonal_factor + noise
            predictions.append(max(0, pred_value))  # Pas de valeurs négatives
        
        return np.array(predictions)
    
    def prepare_future_features(self, days_to_predict):
        """Préparer les features pour les prédictions futures"""
        # À implémenter selon les besoins de votre modèle
        pass
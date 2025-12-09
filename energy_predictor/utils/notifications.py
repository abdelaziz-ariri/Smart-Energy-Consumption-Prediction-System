from datetime import datetime

class NotificationManager:
    def __init__(self, db_handler):
        self.db_handler = db_handler
    
    def check_trends(self, predictions):
        """Vérifier les tendances dans les prédictions"""
        notifications = []
        
        # Vérifier la tendance à la hausse
        if len(predictions) >= 3:
            # Calculer la pente
            from scipy import stats
            x = list(range(len(predictions[:3])))
            slope, _, _, _, _ = stats.linregress(x, predictions[:3])
            
            if slope > 5:  # Hausse significative
                notifications.append({
                    'level': 'warning',
                    'title': 'Tendance à la hausse détectée',
                    'message': f'Augmentation prévue de {slope:.1f} kWh/jour'
                })
            elif slope < -3:  # Baisse significative
                notifications.append({
                    'level': 'info',
                    'title': 'Tendance à la baisse détectée',
                    'message': f'Baisse prévue de {abs(slope):.1f} kWh/jour'
                })
        
        # Vérifier les pics
        avg_prediction = sum(predictions) / len(predictions)
        for i, pred in enumerate(predictions):
            if pred > avg_prediction * 1.5:  # Pic de plus de 50%
                notifications.append({
                    'level': 'critical',
                    'title': 'Pic de consommation prévu',
                    'message': f'Pic de {pred:.1f} kWh prévu le jour {i+1}'
                })
                break
        
        return notifications
    
    def check_historical_trends(self, historical_data):
        """Vérifier les tendances dans les données historiques"""
        notifications = []
        
        if len(historical_data) >= 7:
            # Calculer la moyenne sur 7 jours
            last_7_days = historical_data[-7:]
            avg_last_7 = sum(d['value'] for d in last_7_days) / 7
            
            # Comparer avec la semaine précédente
            if len(historical_data) >= 14:
                previous_7_days = historical_data[-14:-7]
                avg_previous_7 = sum(d['value'] for d in previous_7_days) / 7
                
                if avg_last_7 > avg_previous_7 * 1.2:
                    increase = ((avg_last_7 - avg_previous_7) / avg_previous_7) * 100
                    notifications.append({
                        'level': 'warning',
                        'title': 'Augmentation de consommation',
                        'message': f'Augmentation de {increase:.1f}% cette semaine'
                    })
        
        return notifications
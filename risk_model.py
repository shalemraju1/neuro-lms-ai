import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import logging
from typing import Dict, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskAssessmentModel:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.model_path = 'models/risk_model.pkl'
        self.scaler_path = 'models/risk_scaler.pkl'

        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)

        # Try to load existing model
        self._load_model()

    def _load_model(self):
        """Load pre-trained model if available"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                logger.info("Loaded pre-trained risk assessment model")
            else:
                logger.info("No pre-trained model found, using rule-based fallback")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

    def _generate_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data for risk assessment"""
        np.random.seed(42)

        # Generate sample data: [score, attempts, time_taken]
        n_samples = 1000
        X = np.random.rand(n_samples, 3)
        X[:, 0] = X[:, 0] * 100  # score 0-100
        X[:, 1] = np.random.poisson(2, n_samples) + 1  # attempts (1-5+)
        X[:, 2] = X[:, 2] * 600 + 60  # time_taken 60-660 seconds

        # Generate risk labels based on rules
        y = []
        for sample in X:
            score, attempts, time_taken = sample
            risk = 0

            if score < 50:
                risk += 40
            elif score < 70:
                risk += 20

            if attempts > 3:
                risk += 30
            elif attempts > 1:
                risk += 15

            if time_taken > 300:
                risk += 30
            elif time_taken > 180:
                risk += 15

            # Add some noise and cap at 100
            risk = min(risk + np.random.normal(0, 5), 100)
            risk = max(risk, 0)

            # Convert to risk categories
            if risk < 25:
                y.append(0)  # Low risk
            elif risk < 50:
                y.append(1)  # Medium risk
            elif risk < 75:
                y.append(2)  # High risk
            else:
                y.append(3)  # Critical risk

        return X, np.array(y)

    def train_model(self):
        """Train the risk assessment model"""
        try:
            logger.info("Training risk assessment model...")

            X, y = self._generate_training_data()

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)

            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)

            logger.info(f"Model trained - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")

            # Save model
            self._save_model()
            self.is_trained = True

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            self.is_trained = False

    def _save_model(self):
        """Save trained model to disk"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info("Model saved successfully")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    def predict_risk(self, score: float, attempts: int, time_taken: float) -> Dict[str, any]:
        """
        Predict risk level using ML model or fallback to rule-based
        """
        features = np.array([[score, attempts, time_taken]])

        if self.is_trained and self.model and self.scaler:
            try:
                # Scale features
                features_scaled = self.scaler.transform(features)

                # Get prediction and probability
                risk_category = self.model.predict(features_scaled)[0]
                probabilities = self.model.predict_proba(features_scaled)[0]

                # Convert category to risk score and level
                risk_levels = ['Low', 'Medium', 'High', 'Critical']
                risk_score = (risk_category / 3) * 100  # Convert to 0-100 scale

                return {
                    'risk_score': round(risk_score, 2),
                    'risk_level': risk_levels[risk_category],
                    'confidence': round(max(probabilities) * 100, 2),
                    'probabilities': {
                        'low': round(probabilities[0] * 100, 2),
                        'medium': round(probabilities[1] * 100, 2),
                        'high': round(probabilities[2] * 100, 2),
                        'critical': round(probabilities[3] * 100, 2)
                    },
                    'method': 'machine_learning'
                }

            except Exception as e:
                logger.error(f"ML prediction failed: {e}")
                return self._rule_based_risk(score, attempts, time_taken)

        else:
            return self._rule_based_risk(score, attempts, time_taken)

    def _rule_based_risk(self, score: float, attempts: int, time_taken: float) -> Dict[str, any]:
        """Fallback rule-based risk calculation"""
        risk = 0

        # Score-based risk
        if score < 50:
            risk += 40
        elif score < 70:
            risk += 20

        # Attempts-based risk
        if attempts > 3:
            risk += 30
        elif attempts > 1:
            risk += 15

        # Time-based risk
        if time_taken > 300:
            risk += 30
        elif time_taken > 180:
            risk += 15

        risk = min(max(risk, 0), 100)

        # Determine risk level
        if risk < 25:
            level = 'Low'
        elif risk < 50:
            level = 'Medium'
        elif risk < 75:
            level = 'High'
        else:
            level = 'Critical'

        return {
            'risk_score': round(risk, 2),
            'risk_level': level,
            'confidence': 85.0,  # Rule-based confidence
            'method': 'rule_based'
        }

    def get_model_info(self) -> Dict[str, any]:
        """Get information about the current model"""
        return {
            'is_trained': self.is_trained,
            'model_type': type(self.model).__name__ if self.model else None,
            'has_scaler': self.scaler is not None,
            'model_path': self.model_path,
            'scaler_path': self.scaler_path
        }

# Global risk model instance
risk_model = RiskAssessmentModel()

# Backward compatibility function
def calculate_risk(score, attempts, time_taken):
    """Legacy function for backward compatibility"""
    result = risk_model.predict_risk(score, attempts, time_taken)
    return result['risk_score']

# Initialize model on import
if not risk_model.is_trained:
    logger.info("Initializing risk assessment model...")
    risk_model.train_model()
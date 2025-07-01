"""
Phase 1 XGBoost Baseline Model for Magic8 Accuracy Predictor

Simple and effective XGBoost classifier using readily available features.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight
import json
import joblib
import os
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import shutil

# Import the model wrapper
from model_wrappers import XGBoostModelWrapper

class XGBoostBaseline:
    def __init__(self, config_path=None):
        self.logger = self._setup_logger()
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.feature_importance = None
        
        # Default configuration
        self.config = {
            'n_estimators': 1000,
            'max_depth': 6,
            'learning_rate': 0.01,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 1,
            'gamma': 0,
            'reg_alpha': 0.1,
            'reg_lambda': 1,
            'early_stopping_rounds': 50,
            'random_state': 42
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config.update(json.load(f))
    
    def _setup_logger(self):
        """Setup logging configuration"""
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/xgboost_baseline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def load_data(self, data_dir='data/phase1_processed'):
        """Load preprocessed Phase 1 data"""
        self.logger.info(f"Loading data from {data_dir}")
        
        # Load train, validation, and test data
        self.train_df = pd.read_csv(os.path.join(data_dir, 'train_data.csv'))
        self.val_df = pd.read_csv(os.path.join(data_dir, 'val_data.csv'))
        self.test_df = pd.read_csv(os.path.join(data_dir, 'test_data.csv'))
        
        # Load feature info
        with open(os.path.join(data_dir, 'feature_info.json'), 'r') as f:
            self.feature_info = json.load(f)
        
        self.feature_names = self.feature_info['feature_names']
        
        # Automatically detect and remove ALL object/string columns
        # Check dtypes of features in the training data
        object_columns = []
        for feature in self.feature_names:
            if feature in self.train_df.columns:
                if self.train_df[feature].dtype == 'object':
                    object_columns.append(feature)
        
        if object_columns:
            self.logger.warning(f"Removing {len(object_columns)} object/string columns: {object_columns}")
            self.feature_names = [f for f in self.feature_names if f not in object_columns]
        
        # Also check for any columns that might cause issues (additional safety check)
        numeric_feature_names = []
        for feature in self.feature_names:
            if feature in self.train_df.columns:
                # Try to verify the column is numeric
                try:
                    # Check if we can convert to numeric without errors
                    pd.to_numeric(self.train_df[feature], errors='raise')
                    numeric_feature_names.append(feature)
                except:
                    self.logger.warning(f"Removing non-numeric feature: {feature}")
        
        self.feature_names = numeric_feature_names
        
        # Prepare features and targets
        self.X_train = self.train_df[self.feature_names]
        self.y_train = self.train_df['target']
        
        self.X_val = self.val_df[self.feature_names]
        self.y_val = self.val_df['target']
        
        self.X_test = self.test_df[self.feature_names]
        self.y_test = self.test_df['target']
        
        self.logger.info(f"Loaded {len(self.X_train)} training samples with {len(self.feature_names)} features")
        self.logger.info(f"Class distribution - Train: {self.y_train.value_counts().to_dict()}")
        self.logger.info(f"Class distribution - Val: {self.y_val.value_counts().to_dict()}")
        self.logger.info(f"Class distribution - Test: {self.y_test.value_counts().to_dict()}")
        
        return self
    
    def preprocess_features(self):
        """Scale features and handle missing values"""
        self.logger.info("Preprocessing features...")
        
        # Fill any remaining NaN values
        self.X_train = self.X_train.fillna(0)
        self.X_val = self.X_val.fillna(0)
        self.X_test = self.X_test.fillna(0)
        
        # Convert DataFrames to float to avoid dtype warnings
        self.X_train = self.X_train.astype(float)
        self.X_val = self.X_val.astype(float)
        self.X_test = self.X_test.astype(float)
        
        # Scale numerical features (skip one-hot encoded features)
        non_binary_features = []
        for feature in self.feature_names:
            # Skip binary/one-hot encoded features
            if not any(feature.startswith(prefix) for prefix in ['strategy_', 'vix_regime_', 'is_']):
                non_binary_features.append(feature)
        
        self.logger.info(f"Scaling {len(non_binary_features)} numeric features")
        
        # Fit scaler on training data
        if non_binary_features:
            self.scaler.fit(self.X_train[non_binary_features])
            
            # Transform all sets
            self.X_train[non_binary_features] = self.scaler.transform(self.X_train[non_binary_features])
            self.X_val[non_binary_features] = self.scaler.transform(self.X_val[non_binary_features])
            self.X_test[non_binary_features] = self.scaler.transform(self.X_test[non_binary_features])
        
        return self
    
    def train(self):
        """Train XGBoost model with early stopping"""
        self.logger.info("Training XGBoost model...")
        
        # Calculate class weights for imbalanced data
        classes = np.unique(self.y_train)
        class_weights = compute_class_weight('balanced', classes=classes, y=self.y_train)
        weight_dict = dict(zip(classes, class_weights))
        
        # Create sample weights
        sample_weights = self.y_train.map(weight_dict)
        
        # Create DMatrix for XGBoost
        dtrain = xgb.DMatrix(self.X_train, label=self.y_train, weight=sample_weights)
        dval = xgb.DMatrix(self.X_val, label=self.y_val)
        
        # Set parameters
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': self.config['max_depth'],
            'learning_rate': self.config['learning_rate'],
            'subsample': self.config['subsample'],
            'colsample_bytree': self.config['colsample_bytree'],
            'min_child_weight': self.config['min_child_weight'],
            'gamma': self.config['gamma'],
            'reg_alpha': self.config['reg_alpha'],
            'reg_lambda': self.config['reg_lambda'],
            'random_state': self.config['random_state']
        }
        
        # Train model
        evals = [(dtrain, 'train'), (dval, 'eval')]
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=self.config['n_estimators'],
            evals=evals,
            early_stopping_rounds=self.config['early_stopping_rounds'],
            verbose_eval=50
        )
        
        # Get feature importance
        self.feature_importance = self.model.get_score(importance_type='gain')
        
        self.logger.info(f"Training completed. Best iteration: {self.model.best_iteration}")
        
        return self
    
    def evaluate(self, X, y, dataset_name='Test'):
        """Evaluate model performance"""
        self.logger.info(f"Evaluating on {dataset_name} set...")
        
        # Make predictions
        dtest = xgb.DMatrix(X)
        y_pred_proba = self.model.predict(dtest)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Calculate metrics (handle edge cases)
        metrics = {}
        
        try:
            metrics['accuracy'] = accuracy_score(y, y_pred)
        except:
            metrics['accuracy'] = np.nan
            
        try:
            metrics['precision'] = precision_score(y, y_pred, zero_division=0)
        except:
            metrics['precision'] = np.nan
            
        try:
            metrics['recall'] = recall_score(y, y_pred, zero_division=0)
        except:
            metrics['recall'] = np.nan
            
        try:
            metrics['f1'] = f1_score(y, y_pred, zero_division=0)
        except:
            metrics['f1'] = np.nan
            
        try:
            metrics['auc_roc'] = roc_auc_score(y, y_pred_proba)
        except:
            metrics['auc_roc'] = np.nan
        
        # Log metrics
        self.logger.info(f"{dataset_name} Performance:")
        for metric, value in metrics.items():
            if not np.isnan(value):
                self.logger.info(f"  {metric}: {value:.4f}")
            else:
                self.logger.info(f"  {metric}: N/A")
        
        # Confusion matrix
        cm = confusion_matrix(y, y_pred)
        self.logger.info(f"Confusion Matrix:\n{cm}")
        
        # Classification report
        report = classification_report(y, y_pred, zero_division=0)
        self.logger.info(f"Classification Report:\n{report}")
        
        return metrics, y_pred_proba
    
    def evaluate_by_strategy(self):
        """Evaluate performance by trading strategy"""
        self.logger.info("Evaluating performance by strategy...")
        
        results = {}
        
        # Get strategy columns
        strategy_cols = [col for col in self.test_df.columns if col.startswith('strategy_')]
        
        for strategy_col in strategy_cols:
            strategy_name = strategy_col.replace('strategy_', '')
            
            # Filter test data for this strategy
            strategy_mask = self.test_df[strategy_col] == 1
            if strategy_mask.sum() > 0:
                X_strategy = self.X_test[strategy_mask]
                y_strategy = self.y_test[strategy_mask]
                
                metrics, _ = self.evaluate(X_strategy, y_strategy, f"Strategy: {strategy_name}")
                results[strategy_name] = metrics
                results[strategy_name]['n_samples'] = int(strategy_mask.sum())  # Convert to int
        
        return results
    
    def plot_feature_importance(self, top_n=20):
        """Plot top N most important features"""
        self.logger.info("Plotting feature importance...")
        
        # Sort features by importance
        importance_df = pd.DataFrame([
            {'feature': k, 'importance': v} 
            for k, v in self.feature_importance.items()
        ]).sort_values('importance', ascending=False)
        
        # Plot top N
        plt.figure(figsize=(10, 8))
        top_features = importance_df.head(top_n)
        
        plt.barh(top_features['feature'], top_features['importance'])
        plt.xlabel('Feature Importance (Gain)')
        plt.title(f'Top {top_n} Most Important Features')
        plt.tight_layout()
        
        # Save plot
        os.makedirs('plots', exist_ok=True)
        plt.savefig('plots/feature_importance_phase1.png', dpi=300)
        plt.close()
        
        # Log top features
        self.logger.info(f"Top {top_n} features:")
        for idx, row in top_features.iterrows():
            self.logger.info(f"  {row['feature']}: {row['importance']:.2f}")
        
        return importance_df
    
    def save_model(self, model_dir='models/phase1'):
        """Save trained model and preprocessing objects"""
        os.makedirs(model_dir, exist_ok=True)
        
        # Save XGBoost model in native format
        self.model.save_model(os.path.join(model_dir, 'xgboost_baseline.json'))
        
        # Save scaler
        joblib.dump(self.scaler, os.path.join(model_dir, 'scaler.pkl'))
        
        # Save feature names and config
        metadata = {
            'feature_names': self.feature_names,
            'config': self.config,
            'feature_importance': self.feature_importance,
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(os.path.join(model_dir, 'model_metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save wrapped model for real-time predictor
        self.logger.info("Creating wrapped model for real-time predictor...")
        wrapped_model = XGBoostModelWrapper(self.model, self.feature_names, self.scaler)
        
        # Save wrapped model
        wrapped_path = os.path.join(model_dir, 'xgboost_model.pkl')
        joblib.dump(wrapped_model, wrapped_path)
        
        # Also copy to root models directory for backward compatibility
        root_model_path = os.path.join('models', 'xgboost_phase1_model.pkl')
        os.makedirs('models', exist_ok=True)
        shutil.copy2(wrapped_path, root_model_path)
        
        self.logger.info(f"Model saved to {model_dir}")
        self.logger.info(f"Wrapped model saved to {wrapped_path} and {root_model_path}")
    
    def load_model(self, model_dir='models/phase1'):
        """Load saved model"""
        # Load XGBoost model
        self.model = xgb.Booster()
        self.model.load_model(os.path.join(model_dir, 'xgboost_baseline.json'))
        
        # Load scaler
        self.scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
        
        # Load metadata
        with open(os.path.join(model_dir, 'model_metadata.json'), 'r') as f:
            metadata = json.load(f)
        
        self.feature_names = metadata['feature_names']
        self.config = metadata['config']
        self.feature_importance = metadata['feature_importance']
        
        self.logger.info(f"Model loaded from {model_dir}")
        
        return self
    
    def run_full_pipeline(self):
        """Run complete training and evaluation pipeline"""
        # Load and preprocess data
        self.load_data()
        self.preprocess_features()
        
        # Train model
        self.train()
        
        # Evaluate on all sets
        self.logger.info("=" * 50)
        train_metrics, _ = self.evaluate(self.X_train, self.y_train, 'Training')
        val_metrics, _ = self.evaluate(self.X_val, self.y_val, 'Validation')
        test_metrics, test_proba = self.evaluate(self.X_test, self.y_test, 'Test')
        
        # Evaluate by strategy
        strategy_results = self.evaluate_by_strategy()
        
        # Plot feature importance
        self.plot_feature_importance()
        
        # Save model (includes wrapped model)
        self.save_model()
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_to_native(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(v) for v in obj]
            else:
                return obj
        
        # Save results
        results = {
            'train_metrics': convert_to_native(train_metrics),
            'val_metrics': convert_to_native(val_metrics),
            'test_metrics': convert_to_native(test_metrics),
            'strategy_results': convert_to_native(strategy_results)
        }
        
        with open('models/phase1/results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)  # Use default=str as fallback
        
        self.logger.info("Phase 1 pipeline completed successfully!")
        self.logger.info("✅ Wrapped model ready for real-time predictions!")
        
        return results


def main():
    """Run Phase 1 XGBoost baseline"""
    model = XGBoostBaseline()
    results = model.run_full_pipeline()
    
    print("\n" + "="*50)
    print("PHASE 1 RESULTS SUMMARY")
    print("="*50)
    
    # Handle NaN values in output
    test_metrics = results['test_metrics']
    for metric in ['accuracy', 'auc_roc', 'f1']:
        value = test_metrics.get(metric, 'N/A')
        if isinstance(value, (int, float)) and not np.isnan(value):
            print(f"Test {metric.replace('_', ' ').title()}: {value:.4f}")
        else:
            print(f"Test {metric.replace('_', ' ').title()}: N/A")
    
    print("\nPerformance by Strategy:")
    for strategy, metrics in results['strategy_results'].items():
        acc = metrics.get('accuracy', 'N/A')
        n_samples = metrics.get('n_samples', 0)
        if isinstance(acc, (int, float)) and not np.isnan(acc):
            print(f"  {strategy}: Accuracy={acc:.4f}, n={n_samples}")
        else:
            print(f"  {strategy}: Accuracy=N/A, n={n_samples}")
    
    print("\n✅ Model ready for real-time predictions!")
    print("   Run 'python quick_start.py' to test predictions")


if __name__ == "__main__":
    main()

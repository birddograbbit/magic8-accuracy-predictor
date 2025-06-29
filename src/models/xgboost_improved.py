"""
Improved XGBoost baseline model for Phase 1 - addresses overfitting and class imbalance
"""

import os
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
from sklearn.model_selection import StratifiedKFold
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import json
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedXGBoostTrainer:
    def __init__(self, data_dir='data/phase1_processed', model_dir='models/phase1_improved'):
        self.data_dir = data_dir
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Improved XGBoost parameters to prevent overfitting
        self.model_params = {
            'n_estimators': 300,
            'max_depth': 3,  # Reduced from 6
            'min_child_weight': 10,  # Increased from 1
            'learning_rate': 0.05,  # Reduced from 0.1
            'subsample': 0.7,  # Reduced from 0.8
            'colsample_bytree': 0.7,  # Reduced from 0.8
            'reg_alpha': 1.0,  # Increased from 0
            'reg_lambda': 2.0,  # Increased from 1
            'gamma': 0.1,  # Added minimum split loss
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',  # Changed from default
            'use_label_encoder': False,
            'random_state': 42,
            'n_jobs': -1
        }
        
    def load_data(self):
        """Load the preprocessed data"""
        logger.info(f"Loading data from {self.data_dir}")
        
        self.train_df = pd.read_csv(os.path.join(self.data_dir, 'train_data.csv'))
        self.val_df = pd.read_csv(os.path.join(self.data_dir, 'val_data.csv'))
        self.test_df = pd.read_csv(os.path.join(self.data_dir, 'test_data.csv'))
        
        # Load feature info
        with open(os.path.join(self.data_dir, 'feature_info.json'), 'r') as f:
            self.feature_info = json.load(f)
        
        self.feature_cols = self.feature_info['features']
        
        # Remove constant and low-variance features
        self.remove_problematic_features()
        
        logger.info(f"Loaded {len(self.train_df)} training samples with {len(self.feature_cols)} features")
        
        # Log class distribution
        for name, df in [('Train', self.train_df), ('Val', self.val_df), ('Test', self.test_df)]:
            class_dist = df['target'].value_counts().to_dict()
            logger.info(f"Class distribution - {name}: {class_dist}")
    
    def remove_problematic_features(self):
        """Remove constant and low-variance features"""
        features_to_remove = []
        
        for col in self.feature_cols:
            if col in self.train_df.columns:
                # Check for constant features
                if self.train_df[col].nunique() == 1:
                    features_to_remove.append(col)
                    logger.info(f"Removing constant feature: {col}")
                # Check for very low variance
                elif self.train_df[col].var() < 0.001:
                    features_to_remove.append(col)
                    logger.info(f"Removing low-variance feature: {col} (var={self.train_df[col].var():.6f})")
        
        # Remove features
        self.feature_cols = [f for f in self.feature_cols if f not in features_to_remove]
        logger.info(f"Removed {len(features_to_remove)} problematic features")
    
    def calculate_scale_pos_weight(self):
        """Calculate proper scale_pos_weight for class imbalance"""
        neg_count = (self.train_df['target'] == 0).sum()
        pos_count = (self.train_df['target'] == 1).sum()
        scale_pos_weight = neg_count / pos_count
        logger.info(f"Calculated scale_pos_weight: {scale_pos_weight:.2f}")
        return scale_pos_weight
    
    def find_optimal_threshold(self, y_true, y_proba):
        """Find optimal probability threshold using F1 score"""
        thresholds = np.arange(0.1, 0.9, 0.01)
        f1_scores = []
        
        for threshold in thresholds:
            y_pred = (y_proba >= threshold).astype(int)
            f1 = f1_score(y_true, y_pred)
            f1_scores.append(f1)
        
        optimal_idx = np.argmax(f1_scores)
        optimal_threshold = thresholds[optimal_idx]
        optimal_f1 = f1_scores[optimal_idx]
        
        logger.info(f"Optimal threshold: {optimal_threshold:.3f} (F1: {optimal_f1:.3f})")
        return optimal_threshold
    
    def train(self):
        """Train the improved XGBoost model"""
        logger.info("Preprocessing features...")
        
        # Prepare data
        X_train = self.train_df[self.feature_cols]
        y_train = self.train_df['target']
        X_val = self.val_df[self.feature_cols]
        y_val = self.val_df['target']
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Calculate scale_pos_weight
        scale_pos_weight = self.calculate_scale_pos_weight()
        self.model_params['scale_pos_weight'] = scale_pos_weight
        
        # Train model with better early stopping
        logger.info("Training improved XGBoost model...")
        self.model = XGBClassifier(**self.model_params)
        
        # Use eval_set for early stopping
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_train_scaled, y_train), (X_val_scaled, y_val)],
            early_stopping_rounds=30,  # Increased from 10
            verbose=50
        )
        
        logger.info(f"Training completed. Best iteration: {self.model.best_iteration}")
        
        # Find optimal threshold on validation set
        y_val_proba = self.model.predict_proba(X_val_scaled)[:, 1]
        self.optimal_threshold = self.find_optimal_threshold(y_val, y_val_proba)
        
        # Save model and preprocessor
        self.save_model()
    
    def evaluate(self, X, y, dataset_name="", return_proba=False):
        """Evaluate model performance with optimal threshold"""
        X_scaled = self.scaler.transform(X)
        
        # Get probabilities
        y_proba = self.model.predict_proba(X_scaled)[:, 1]
        
        # Use optimal threshold
        y_pred = (y_proba >= self.optimal_threshold).astype(int)
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1': f1_score(y, y_pred, zero_division=0),
            'auc_roc': roc_auc_score(y, y_proba) if len(np.unique(y)) > 1 else 'N/A'
        }
        
        logger.info(f"{dataset_name} Performance:")
        for metric, value in metrics.items():
            if value != 'N/A':
                logger.info(f"  {metric}: {value:.4f}")
        
        # Confusion matrix
        cm = confusion_matrix(y, y_pred)
        logger.info(f"Confusion Matrix:\n{cm}")
        
        # Classification report
        report = classification_report(y, y_pred)
        logger.info(f"Classification Report:\n{report}")
        
        if return_proba:
            return metrics, y_proba
        return metrics
    
    def plot_results(self):
        """Create comprehensive visualization of results"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # Get test predictions
        X_test = self.test_df[self.feature_cols]
        y_test = self.test_df['target']
        X_test_scaled = self.scaler.transform(X_test)
        y_test_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # 1. Feature importance
        ax1 = axes[0, 0]
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:20]
        
        ax1.barh(range(20), importances[indices])
        ax1.set_yticks(range(20))
        ax1.set_yticklabels([self.feature_cols[i] for i in indices])
        ax1.set_xlabel('Importance')
        ax1.set_title('Top 20 Feature Importances')
        
        # 2. Probability distribution
        ax2 = axes[0, 1]
        ax2.hist(y_test_proba[y_test == 0], bins=50, alpha=0.5, label='Loss', density=True)
        ax2.hist(y_test_proba[y_test == 1], bins=50, alpha=0.5, label='Win', density=True)
        ax2.axvline(self.optimal_threshold, color='red', linestyle='--', 
                   label=f'Threshold: {self.optimal_threshold:.3f}')
        ax2.set_xlabel('Predicted Probability')
        ax2.set_ylabel('Density')
        ax2.set_title('Probability Distribution by Class')
        ax2.legend()
        
        # 3. Learning curves
        ax3 = axes[0, 2]
        results = self.model.evals_result()
        epochs = len(results['validation_0']['logloss'])
        x_axis = range(0, epochs)
        
        ax3.plot(x_axis, results['validation_0']['logloss'], label='Train')
        ax3.plot(x_axis, results['validation_1']['logloss'], label='Val')
        ax3.set_xlabel('Boosting Round')
        ax3.set_ylabel('Log Loss')
        ax3.set_title('Training History')
        ax3.legend()
        
        # 4. Performance by hour (if available)
        ax4 = axes[1, 0]
        if 'hour' in self.test_df.columns:
            hourly_perf = []
            for hour in sorted(self.test_df['hour'].unique()):
                mask = self.test_df['hour'] == hour
                if mask.sum() > 10:
                    X_hour = self.test_df[mask][self.feature_cols]
                    y_hour = self.test_df[mask]['target']
                    metrics, _ = self.evaluate(X_hour, y_hour, return_proba=True)
                    hourly_perf.append({'hour': hour, 'f1': metrics['f1']})
            
            if hourly_perf:
                perf_df = pd.DataFrame(hourly_perf)
                ax4.bar(perf_df['hour'], perf_df['f1'])
                ax4.set_xlabel('Hour')
                ax4.set_ylabel('F1 Score')
                ax4.set_title('Performance by Hour')
        
        # 5. Precision-Recall curve
        from sklearn.metrics import precision_recall_curve
        ax5 = axes[1, 1]
        precision, recall, thresholds = precision_recall_curve(y_test, y_test_proba)
        ax5.plot(recall, precision)
        ax5.set_xlabel('Recall')
        ax5.set_ylabel('Precision')
        ax5.set_title('Precision-Recall Curve')
        ax5.axhline(y_test.mean(), color='red', linestyle='--', 
                   label=f'Baseline: {y_test.mean():.3f}')
        ax5.legend()
        
        # 6. Threshold analysis
        ax6 = axes[1, 2]
        thresholds = np.arange(0.1, 0.9, 0.05)
        f1_scores = []
        precisions = []
        recalls = []
        
        for thresh in thresholds:
            y_pred_thresh = (y_test_proba >= thresh).astype(int)
            f1_scores.append(f1_score(y_test, y_pred_thresh))
            precisions.append(precision_score(y_test, y_pred_thresh, zero_division=0))
            recalls.append(recall_score(y_test, y_pred_thresh, zero_division=0))
        
        ax6.plot(thresholds, f1_scores, 'b-', label='F1')
        ax6.plot(thresholds, precisions, 'g-', label='Precision')
        ax6.plot(thresholds, recalls, 'r-', label='Recall')
        ax6.axvline(self.optimal_threshold, color='black', linestyle='--', 
                   label=f'Optimal: {self.optimal_threshold:.3f}')
        ax6.set_xlabel('Threshold')
        ax6.set_ylabel('Score')
        ax6.set_title('Metrics vs Threshold')
        ax6.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.model_dir, 'improved_model_analysis.png'), 
                   dpi=300, bbox_inches='tight')
        logger.info("Saved analysis plots")
    
    def save_model(self):
        """Save model and preprocessing artifacts"""
        joblib.dump(self.model, os.path.join(self.model_dir, 'xgboost_improved.pkl'))
        joblib.dump(self.scaler, os.path.join(self.model_dir, 'scaler.pkl'))
        
        # Save model info
        model_info = {
            'model_params': self.model_params,
            'feature_cols': self.feature_cols,
            'n_features': len(self.feature_cols),
            'optimal_threshold': self.optimal_threshold,
            'best_iteration': self.model.best_iteration,
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(os.path.join(self.model_dir, 'model_info.json'), 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info(f"Model saved to {self.model_dir}")
    
    def run_full_pipeline(self):
        """Execute the complete training pipeline"""
        logger.info("="*50)
        logger.info("Starting Improved XGBoost Pipeline")
        logger.info("="*50)
        
        # Load data
        self.load_data()
        
        # Train model
        self.train()
        
        # Evaluate on all datasets
        logger.info("\n" + "="*50)
        train_metrics = self.evaluate(
            self.train_df[self.feature_cols], 
            self.train_df['target'], 
            "Training"
        )
        
        val_metrics = self.evaluate(
            self.val_df[self.feature_cols], 
            self.val_df['target'], 
            "Validation"
        )
        
        test_metrics = self.evaluate(
            self.test_df[self.feature_cols], 
            self.test_df['target'], 
            "Test"
        )
        
        # Create visualizations
        self.plot_results()
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("IMPROVED MODEL SUMMARY")
        logger.info("="*50)
        logger.info(f"Optimal Threshold: {self.optimal_threshold:.3f}")
        logger.info(f"Test F1 Score: {test_metrics['f1']:.4f}")
        logger.info(f"Test Precision: {test_metrics['precision']:.4f}")
        logger.info(f"Test Recall: {test_metrics['recall']:.4f}")
        logger.info(f"Test AUC-ROC: {test_metrics['auc_roc']:.4f}")
        
        return test_metrics

if __name__ == "__main__":
    trainer = ImprovedXGBoostTrainer()
    test_metrics = trainer.run_full_pipeline()

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from typing import Dict, Tuple, Optional
import logging
from tqdm import tqdm


class Magic8Trainer:
    """Trainer for Magic8 accuracy prediction model."""
    
    def __init__(
        self,
        model: nn.Module,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        learning_rate: float = 1e-4,
        weight_decay: float = 1e-5
    ):
        self.model = model.to(device)
        self.device = device
        self.optimizer = optim.Adam(
            model.parameters(), 
            lr=learning_rate, 
            weight_decay=weight_decay
        )
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, 
            mode='min', 
            patience=5, 
            factor=0.5
        )
        
    def train_epoch(
        self, 
        train_loader: DataLoader, 
        criterion: nn.Module
    ) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        
        for batch in tqdm(train_loader, desc='Training'):
            # Move data to device
            symbol_ids = batch['symbol_ids'].to(self.device)
            temporal_features = batch['temporal_features'].to(self.device)
            market_features = batch['market_features'].to(self.device)
            magic8_features = batch['magic8_features'].to(self.device)
            labels = batch['labels'].to(self.device).float()
            
            # Forward pass
            self.optimizer.zero_grad()
            logits = self.model(
                symbol_ids,
                temporal_features,
                market_features,
                magic8_features
            )
            
            # Calculate loss
            loss = criterion(logits.squeeze(), labels)
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            
            total_loss += loss.item()
            
        return total_loss / len(train_loader)
    
    def evaluate(
        self, 
        val_loader: DataLoader, 
        criterion: nn.Module
    ) -> Tuple[float, Dict[str, float]]:
        """Evaluate model on validation set."""
        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_labels = []
        all_probs = []
        
        with torch.no_grad():
            for batch in tqdm(val_loader, desc='Evaluating'):
                # Move data to device
                symbol_ids = batch['symbol_ids'].to(self.device)
                temporal_features = batch['temporal_features'].to(self.device)
                market_features = batch['market_features'].to(self.device)
                magic8_features = batch['magic8_features'].to(self.device)
                labels = batch['labels'].to(self.device).float()
                
                # Forward pass
                logits = self.model(
                    symbol_ids,
                    temporal_features,
                    market_features,
                    magic8_features
                )
                
                # Calculate loss
                loss = criterion(logits.squeeze(), labels)
                total_loss += loss.item()
                
                # Get predictions
                probs = torch.sigmoid(logits.squeeze())
                preds = (probs > 0.5).float()
                
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                all_probs.extend(probs.cpu().numpy())
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(all_labels, all_preds),
            'precision': precision_score(all_labels, all_preds, zero_division=0),
            'recall': recall_score(all_labels, all_preds, zero_division=0),
            'f1': f1_score(all_labels, all_preds, zero_division=0),
            'auc': roc_auc_score(all_labels, all_probs) if len(np.unique(all_labels)) > 1 else 0.0
        }
        
        avg_loss = total_loss / len(val_loader)
        return avg_loss, metrics
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int = 50,
        early_stopping_patience: int = 10,
        checkpoint_path: str = 'checkpoints/best_model.pth'
    ):
        """Full training loop with early stopping."""
        # Calculate positive weight for class imbalance
        # This should be calculated from your actual data
        pos_weight = torch.tensor([1.0]).to(self.device)  # Adjust based on class distribution
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(num_epochs):
            logging.info(f'\nEpoch {epoch + 1}/{num_epochs}')
            
            # Train
            train_loss = self.train_epoch(train_loader, criterion)
            
            # Evaluate
            val_loss, metrics = self.evaluate(val_loader, criterion)
            
            # Log results
            logging.info(f'Train Loss: {train_loss:.4f}')
            logging.info(f'Val Loss: {val_loss:.4f}')
            logging.info(f'Metrics: {metrics}')
            
            # Learning rate scheduling
            self.scheduler.step(val_loss)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                
                # Save best model
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'val_loss': val_loss,
                    'metrics': metrics
                }, checkpoint_path)
                logging.info('Saved best model checkpoint')
            else:
                patience_counter += 1
                
            if patience_counter >= early_stopping_patience:
                logging.info(f'Early stopping triggered after {epoch + 1} epochs')
                break
                
        logging.info('Training completed!')

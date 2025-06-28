import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Tuple, Optional


class Magic8AccuracyTransformer(nn.Module):
    """Transformer model for binary classification of Magic8 trading accuracy."""
    
    def __init__(
        self,
        num_symbols: int = 100,
        symbol_embed_dim: int = 32,
        temporal_features: int = 8,
        market_features: int = 5,
        magic8_features: int = 10,
        seq_length: int = 30,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 3,
        dim_feedforward: int = 512,
        dropout: float = 0.1
    ):
        super().__init__()
        
        # Configuration
        self.seq_length = seq_length
        self.d_model = d_model
        
        # Symbol embeddings
        self.symbol_embedding = nn.Embedding(num_symbols, symbol_embed_dim)
        
        # Input projection
        input_dim = symbol_embed_dim + temporal_features + market_features + magic8_features
        self.input_fc = nn.Linear(input_dim, d_model)
        
        # Positional encoding
        self.pos_embedding = nn.Parameter(torch.zeros(1, seq_length, d_model))
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="relu",
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer, 
            num_layers=num_layers
        )
        
        # Classification head
        self.fc_out = nn.Linear(d_model, 1)
        self.dropout = nn.Dropout(dropout)
        
    def forward(
        self, 
        symbol_ids: torch.Tensor,
        temporal_features: torch.Tensor,
        market_features: torch.Tensor,
        magic8_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            symbol_ids: [batch_size, seq_length] - Symbol indices
            temporal_features: [batch_size, seq_length, temporal_features]
            market_features: [batch_size, seq_length, market_features]
            magic8_features: [batch_size, seq_length, magic8_features]
            attention_mask: Optional attention mask
            
        Returns:
            logits: [batch_size, 1] - Binary classification logits
        """
        batch_size, seq_len = symbol_ids.shape
        
        # Get symbol embeddings
        symbol_embeds = self.symbol_embedding(symbol_ids)  # [B, S, symbol_embed_dim]
        
        # Concatenate all features
        combined_features = torch.cat([
            symbol_embeds,
            temporal_features,
            market_features,
            magic8_features
        ], dim=-1)  # [B, S, total_features]
        
        # Project to model dimension
        src = self.input_fc(combined_features)  # [B, S, d_model]
        
        # Add positional embedding
        src = src + self.pos_embedding[:, :seq_len, :]
        
        # Apply transformer
        encoded = self.transformer_encoder(
            src, 
            src_key_padding_mask=attention_mask
        )  # [B, S, d_model]
        
        # Use the last timestep for classification
        last_hidden = encoded[:, -1, :]  # [B, d_model]
        
        # Apply dropout and classification head
        last_hidden = self.dropout(last_hidden)
        logits = self.fc_out(last_hidden)  # [B, 1]
        
        return logits


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding."""
    
    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * 
            (-np.log(10000.0) / d_model)
        )
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        self.register_buffer('pe', pe.unsqueeze(0))
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, :x.size(1)]

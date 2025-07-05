# Magic8 Accuracy Predictor - Comprehensive Revamp Plan (v2)

**Updated**: January 2025  
**Purpose**: Complete blueprint for improving Magic8 accuracy predictor with per-symbol-per-strategy models, corrected data processing, and risk/reward calculations  
**Overall Completion Status**: ~60% (Phase 5-7 Added)

## 🚨 Critical Issues & New Requirements

### SPX Profit Scale Misclassification
- **Issue**: SPX incorrectly grouped as "Small Scale" with $9.67 avg profit
- **Reality**: SPX Butterfly trades range from $2800 to -$1000
- **Impact**: 76x scale difference suggests data processing error or need for strategy-specific grouping

### Missing Delta Data Integration
- **Issue**: Delta sheets not properly marked in source_file column
- **Reality**: ShortTerm/LongTerm data exists but not utilized in models
- **Impact**: Missing critical Magic8 prediction signals

### Risk/Reward Calculation Gap
- **Issue**: DiscordTrading doesn't extract risk/reward from instructions
- **Reality**: These can be calculated from option spreads
- **Impact**: ML models missing key profitability features

## 📊 Phase 0-4: COMPLETED ✅ (See Previous Sections)

## 🎯 Phase 5: Per-Symbol-Per-Strategy Model Architecture - NEW

### 5.1 Profit Scale Analysis & Regrouping
**Goal**: Correctly classify symbols based on actual profit ranges per strategy

#### Implementation Steps:
```python
# 1. Create profit_scale_analyzer.py
class ProfitScaleAnalyzer:
    def analyze_by_strategy(self, df: pd.DataFrame) -> Dict:
        """Analyze profit scales per symbol-strategy combination."""
        results = {}
        
        for symbol in df['symbol'].unique():
            for strategy in df['strategy'].unique():
                mask = (df['symbol'] == symbol) & (df['strategy'] == strategy)
                strategy_df = df[mask]
                
                if len(strategy_df) > 0:
                    key = f"{symbol}_{strategy}"
                    results[key] = {
                        'count': len(strategy_df),
                        'avg_profit': strategy_df['profit'].mean(),
                        'min_profit': strategy_df['profit'].min(),
                        'max_profit': strategy_df['profit'].max(),
                        'std_profit': strategy_df['profit'].std(),
                        'profit_range': strategy_df['profit'].max() - strategy_df['profit'].min()
                    }
        
        return results
    
    def recommend_groupings(self, analysis: Dict) -> Dict:
        """Recommend model groupings based on profit scales."""
        # Group by profit range magnitude
        groupings = {
            'large_scale': [],  # > $1000 range
            'medium_scale': [], # $100-1000 range  
            'small_scale': []   # < $100 range
        }
        
        for key, stats in analysis.items():
            if stats['profit_range'] > 1000:
                groupings['large_scale'].append(key)
            elif stats['profit_range'] > 100:
                groupings['medium_scale'].append(key)
            else:
                groupings['small_scale'].append(key)
        
        return groupings
```

#### Expected Regrouping:
- **Large Scale**: SPX_Butterfly, SPX_IronCondor, NDX_all, RUT_all
- **Medium Scale**: SPY_all, SPX_Vertical, SPX_Sonar
- **Small Scale**: XSP_all, QQQ_all, AAPL_all, TSLA_all

### 5.2 Symbol-Strategy Model Training Pipeline
**Goal**: Train individual models for each symbol-strategy combination

```python
# train_symbol_strategy_models.py
class SymbolStrategyModelTrainer:
    def __init__(self, min_samples=100):
        self.min_samples = min_samples
        self.models = {}
        
    def train_all_models(self, df: pd.DataFrame, feature_cols: List[str]):
        """Train a model for each symbol-strategy combination."""
        
        for symbol in df['symbol'].unique():
            for strategy in df['strategy'].unique():
                mask = (df['symbol'] == symbol) & (df['strategy'] == strategy)
                strategy_df = df[mask]
                
                if len(strategy_df) >= self.min_samples:
                    model_key = f"{symbol}_{strategy}"
                    logger.info(f"Training model for {model_key}: {len(strategy_df)} samples")
                    
                    # Split data
                    X = strategy_df[feature_cols]
                    y = strategy_df['win']
                    
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42, stratify=y
                    )
                    
                    # Train XGBoost
                    model = XGBClassifier(
                        n_estimators=200,
                        max_depth=4,
                        learning_rate=0.1,
                        random_state=42
                    )
                    
                    model.fit(X_train, y_train)
                    
                    # Evaluate
                    y_pred = model.predict(X_test)
                    accuracy = accuracy_score(y_test, y_pred)
                    
                    self.models[model_key] = {
                        'model': model,
                        'accuracy': accuracy,
                        'samples': len(strategy_df),
                        'features': feature_cols
                    }
                    
                    logger.info(f"  Accuracy: {accuracy:.4f}")
                else:
                    logger.warning(f"Insufficient data for {symbol}_{strategy}: {len(strategy_df)} samples")
        
        return self.models
```

### 5.3 Hierarchical Model Strategy
**Goal**: Use symbol-strategy models with intelligent fallback

```python
# hierarchical_predictor.py
class HierarchicalPredictor:
    def __init__(self):
        self.symbol_strategy_models = {}  # e.g., "SPX_Butterfly"
        self.symbol_models = {}           # e.g., "SPX" 
        self.strategy_models = {}         # e.g., "Butterfly"
        self.default_model = None
        
    def predict(self, symbol: str, strategy: str, features: np.ndarray) -> float:
        """Predict with fallback hierarchy."""
        
        # 1. Try symbol-strategy specific model
        key = f"{symbol}_{strategy}"
        if key in self.symbol_strategy_models:
            return self.symbol_strategy_models[key].predict_proba(features)[0][1]
        
        # 2. Try symbol-specific model
        if symbol in self.symbol_models:
            return self.symbol_models[symbol].predict_proba(features)[0][1]
        
        # 3. Try strategy-specific model
        if strategy in self.strategy_models:
            return self.strategy_models[strategy].predict_proba(features)[0][1]
        
        # 4. Use default model
        if self.default_model:
            return self.default_model.predict_proba(features)[0][1]
        
        # 5. Return neutral probability
        return 0.5
```

## 🔧 Phase 6: Enhanced Data Processing for Delta Integration

### 6.1 Fix Delta Sheet Processing
**Goal**: Properly track and utilize ShortTerm/LongTerm data

```python
# Update process_magic8_data_optimized_v3.py
def process_folder(self, folder: Path):
    """Process all files in a single date folder with proper delta tracking."""
    
    # ... existing code ...
    
    # 3. Add delta sheet data with tracking
    if files['delta']:
        delta_data = self.process_delta_file(files['delta'], folder_date)
        delta_matches = 0
        
        for key, trade in trades_data.items():
            time_key = f"{trade.get('date')} {trade.get('time')}"
            if time_key in delta_data:
                # Update trade with delta data
                trade.update(delta_data[time_key])
                
                # Mark that delta data was included
                if trade.get('source_file'):
                    trade['source_file'] += ',delta'
                else:
                    trade['source_file'] = 'delta'
                    
                delta_matches += 1
        
        logger.info(f"Matched {delta_matches}/{len(delta_data)} delta records")
```

### 6.2 Delta-Aware Feature Engineering
**Goal**: Create features from ShortTerm/LongTerm predictions

```python
# delta_features.py
class DeltaFeatureGenerator:
    def generate_delta_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate features from delta sheet data."""
        
        # Basic delta features
        df['has_delta_data'] = (~df['short_term'].isna()).astype(int)
        
        # Short/Long term bias
        df['short_long_spread'] = df['short_term'] - df['long_term']
        df['short_long_ratio'] = df['short_term'] / df['long_term'].replace(0, 1)
        
        # Price vs predictions
        df['price_vs_short'] = (df['price'] - df['short_term']) / df['price'] * 100
        df['price_vs_long'] = (df['price'] - df['long_term']) / df['price'] * 100
        
        # Prediction alignment
        df['predicted_vs_short'] = df['predicted'] - df['short_term']
        df['predicted_vs_long'] = df['predicted'] - df['long_term']
        
        # Delta convergence
        df['delta_convergence'] = abs(df['short_term'] - df['long_term'])
        
        # Directional agreement
        df['predictions_aligned'] = (
            (df['short_term'] > df['price']) == (df['long_term'] > df['price'])
        ).astype(int)
        
        return df
```

### 6.3 Delta Data Quality Validation
**Goal**: Ensure delta data is properly captured

```python
# validate_delta_integration.py
def validate_delta_coverage(df: pd.DataFrame):
    """Validate delta data integration."""
    
    # Check source_file tracking
    has_delta = df['source_file'].str.contains('delta', na=False)
    delta_coverage = has_delta.sum() / len(df) * 100
    
    logger.info(f"Delta data coverage: {delta_coverage:.1f}%")
    
    # Check by date range
    df['date_parsed'] = pd.to_datetime(df['date'])
    monthly_coverage = df.groupby(df['date_parsed'].dt.to_period('M')).agg({
        'short_term': lambda x: x.notna().sum() / len(x) * 100,
        'long_term': lambda x: x.notna().sum() / len(x) * 100
    })
    
    logger.info("Monthly delta coverage:")
    logger.info(monthly_coverage)
    
    # Identify missing delta periods
    missing_delta = df[df['short_term'].isna() & df['long_term'].isna()]
    logger.info(f"Trades missing delta data: {len(missing_delta)}")
    
    return {
        'overall_coverage': delta_coverage,
        'monthly_coverage': monthly_coverage,
        'missing_count': len(missing_delta)
    }
```

## 📈 Phase 7: Risk/Reward Calculation from Discord Instructions

### 7.1 Option Spread Calculator
**Goal**: Calculate theoretical max profit/loss from trade instructions

```python
# risk_reward_calculator.py
class RiskRewardCalculator:
    def __init__(self, multiplier=100):
        self.multiplier = multiplier  # SPX multiplier
    
    def calculate_butterfly(self, strikes: List[float], premium: float, 
                          action: str, quantity: int = 1) -> Dict:
        """Calculate risk/reward for butterfly spread."""
        # strikes = [lower, middle, upper]
        spread_width = strikes[1] - strikes[0]
        
        if action == 'BUY':
            # Debit spread
            max_loss = premium * self.multiplier * quantity
            max_profit = (spread_width - premium) * self.multiplier * quantity
            breakeven_lower = strikes[0] + premium
            breakeven_upper = strikes[2] - premium
        else:
            # Credit spread (rare for butterfly)
            max_profit = premium * self.multiplier * quantity
            max_loss = (spread_width - premium) * self.multiplier * quantity
            breakeven_lower = strikes[0] + premium
            breakeven_upper = strikes[2] - premium
        
        return {
            'max_profit': max_profit,
            'max_loss': -abs(max_loss),
            'risk_reward_ratio': abs(max_profit / max_loss) if max_loss != 0 else 0,
            'breakeven_lower': breakeven_lower,
            'breakeven_upper': breakeven_upper
        }
    
    def calculate_iron_condor(self, strikes: List[float], premium: float,
                            action: str, quantity: int = 1) -> Dict:
        """Calculate risk/reward for iron condor."""
        # strikes = [put_long, put_short, call_short, call_long]
        put_spread_width = strikes[1] - strikes[0]
        call_spread_width = strikes[3] - strikes[2]
        max_spread_width = max(put_spread_width, call_spread_width)
        
        if action == 'SELL':
            # Credit spread (typical)
            max_profit = premium * self.multiplier * quantity
            max_loss = (max_spread_width - premium) * self.multiplier * quantity
            breakeven_lower = strikes[1] - premium
            breakeven_upper = strikes[2] + premium
        else:
            # Debit spread (rare)
            max_loss = premium * self.multiplier * quantity
            max_profit = (max_spread_width - premium) * self.multiplier * quantity
            breakeven_lower = strikes[1] - premium
            breakeven_upper = strikes[2] + premium
        
        return {
            'max_profit': max_profit,
            'max_loss': -abs(max_loss),
            'risk_reward_ratio': abs(max_profit / max_loss) if max_loss != 0 else 0,
            'breakeven_lower': breakeven_lower,
            'breakeven_upper': breakeven_upper
        }
    
    def calculate_vertical(self, strikes: List[float], premium: float,
                         action: str, option_type: str, quantity: int = 1) -> Dict:
        """Calculate risk/reward for vertical spread."""
        # strikes = [short_strike, long_strike]
        spread_width = abs(strikes[1] - strikes[0])
        
        if action == 'SELL':
            # Credit spread
            max_profit = premium * self.multiplier * quantity
            max_loss = (spread_width - premium) * self.multiplier * quantity
            
            if option_type == 'PUT':
                breakeven = strikes[0] - premium
            else:  # CALL
                breakeven = strikes[0] + premium
        else:
            # Debit spread
            max_loss = premium * self.multiplier * quantity
            max_profit = (spread_width - premium) * self.multiplier * quantity
            
            if option_type == 'PUT':
                breakeven = strikes[0] - premium
            else:  # CALL
                breakeven = strikes[0] + premium
        
        return {
            'max_profit': max_profit,
            'max_loss': -abs(max_loss),
            'risk_reward_ratio': abs(max_profit / max_loss) if max_loss != 0 else 0,
            'breakeven': breakeven
        }
```

### 7.2 Discord Message Parser Enhancement
**Goal**: Extract all required data from Discord messages

```python
# enhanced_discord_parser.py
class EnhancedDiscordParser:
    def parse_magic8_message(self, message: str) -> Dict:
        """Parse complete Magic8 Discord message."""
        
        result = {
            'metadata': {},
            'predictions': {},
            'trades': []
        }
        
        lines = message.split('\n')
        
        for line in lines:
            # Parse prediction data
            if 'Price:' in line:
                result['predictions']['current_price'] = self._extract_number(line)
            elif 'Predicted Close:' in line:
                result['predictions']['predicted_close'] = self._extract_number(line)
            elif 'Short term:' in line and 'bias' not in line:
                result['predictions']['short_term'] = self._extract_number(line)
            elif 'Long term:' in line and 'bias' not in line:
                result['predictions']['long_term'] = self._extract_number(line)
            elif 'Target 1:' in line:
                result['predictions']['target1'] = self._extract_number(line)
            elif 'Target 2:' in line:
                result['predictions']['target2'] = self._extract_number(line)
            
            # Parse trade instructions
            elif any(strategy in line for strategy in ['Butterfly', 'Iron Condor', 'Sonar', 'Vertical']):
                trade = self._parse_trade_instruction(line)
                if trade:
                    # Calculate risk/reward
                    calculator = RiskRewardCalculator()
                    
                    if trade['strategy'] == 'Butterfly':
                        rr = calculator.calculate_butterfly(
                            trade['strikes'], trade['premium'], 
                            trade['action'], trade['quantity']
                        )
                    elif trade['strategy'] in ['Iron Condor', 'Sonar']:
                        rr = calculator.calculate_iron_condor(
                            trade['strikes'], trade['premium'],
                            trade['action'], trade['quantity']
                        )
                    elif trade['strategy'] == 'Vertical':
                        rr = calculator.calculate_vertical(
                            trade['strikes'], trade['premium'],
                            trade['action'], trade['option_type'], 
                            trade['quantity']
                        )
                    
                    trade.update(rr)
                    result['trades'].append(trade)
        
        return result
    
    def _extract_number(self, line: str) -> float:
        """Extract number from line."""
        # Use regex to find number
        match = re.search(r'[-+]?\d*\.?\d+', line.split(':')[-1])
        return float(match.group()) if match else None
```

### 7.3 API Enhancement for Real-time Risk/Reward
**Goal**: Calculate risk/reward on-demand for DiscordTrading

```python
# Update prediction_api_realtime.py
@app.post("/calculate_risk_reward")
async def calculate_risk_reward(request: TradeInstruction):
    """Calculate risk/reward from trade instruction."""
    
    calculator = RiskRewardCalculator()
    
    # Parse trade details
    strategy = request.strategy
    strikes = request.strikes
    premium = request.premium
    action = request.action
    quantity = request.quantity
    option_type = request.option_type
    
    # Calculate based on strategy
    if strategy == 'Butterfly':
        result = calculator.calculate_butterfly(strikes, premium, action, quantity)
    elif strategy in ['IronCondor', 'Sonar']:
        result = calculator.calculate_iron_condor(strikes, premium, action, quantity)
    elif strategy == 'Vertical':
        result = calculator.calculate_vertical(strikes, premium, action, option_type, quantity)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")
    
    return {
        'symbol': request.symbol,
        'strategy': strategy,
        'risk': result['max_loss'],
        'reward': result['max_profit'],
        'risk_reward_ratio': result['risk_reward_ratio'],
        'breakevens': {
            k: v for k, v in result.items() 
            if 'breakeven' in k
        }
    }

# Add to prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(req: TradeRequest):
    # ... existing code ...
    
    # Auto-calculate risk/reward if not provided
    if req.risk is None or req.reward is None:
        if hasattr(req, 'strikes') and req.strikes:
            calc = RiskRewardCalculator()
            # ... calculate based on strategy ...
            req.risk = result['max_loss']
            req.reward = result['max_profit']
```

## 📊 Updated Implementation Timeline

### Week 4: Per-Symbol-Strategy Models
**Days 1-2: Profit Scale Analysis**
- [ ] Run comprehensive profit analysis by symbol-strategy
- [ ] Identify correct groupings (fix SPX classification)
- [ ] Document profit ranges for each combination

**Days 3-5: Model Training**
- [ ] Implement symbol-strategy model trainer
- [ ] Train models for high-volume combinations
- [ ] Implement hierarchical predictor with fallback

### Week 5: Delta Integration
**Days 1-2: Fix Data Processing**
- [ ] Update data processor to track delta source
- [ ] Validate delta data coverage
- [ ] Re-process all data with proper delta tracking

**Days 3-4: Feature Engineering**
- [ ] Implement delta-aware features
- [ ] Add ShortTerm/LongTerm to feature set
- [ ] Retrain models with delta features

### Week 6: Risk/Reward Integration  
**Days 1-2: Calculator Implementation**
- [ ] Implement option spread calculators
- [ ] Test with all strategy types
- [ ] Validate against manual calculations

**Days 3-4: API Enhancement**
- [ ] Add risk/reward endpoint
- [ ] Update prediction API to auto-calculate
- [ ] Create DiscordTrading integration guide

### Week 7: Integration & Deployment
**Days 1-2: DiscordTrading Updates**
- [ ] Update parser to extract predicted_price
- [ ] Add risk/reward calculation client
- [ ] Test end-to-end with live Discord messages

**Days 3-5: Production Deployment**
- [ ] Deploy enhanced API
- [ ] Monitor model performance by symbol-strategy
- [ ] A/B test hierarchical vs simple models

## 🎯 Success Metrics (Updated)

### Model Architecture
- [ ] 30+ symbol-strategy specific models trained
- [ ] Hierarchical predictor with 4-level fallback
- [ ] SPX correctly classified based on actual profit ranges

### Data Quality
- [ ] 95%+ delta data coverage (ShortTerm/LongTerm captured)
- [ ] source_file properly tracks all data sources
- [ ] Risk/reward calculated for 100% of trades

### Performance Targets
- [ ] Symbol-strategy models: 85-95% accuracy
- [ ] Risk/reward correlation with profit: >0.7
- [ ] API latency with calculations: <150ms

### Integration Success
- [ ] DiscordTrading extracts all required fields
- [ ] Real-time risk/reward calculation working
- [ ] ML predictions use complete feature set

## 🔑 Critical Dependencies

1. **Data Reprocessing**: Must fix delta tracking before retraining
2. **SPX Reclassification**: Impacts model grouping strategy
3. **Discord Message Format**: Need predicted_price in messages
4. **API Compatibility**: Maintain backward compatibility

## 🚀 Expected Outcomes

### Improved Predictions
- Per-strategy models capture strategy-specific patterns
- Delta features improve prediction timing
- Risk/reward features enhance profitability assessment

### Better Integration
- DiscordTrading has all data needed for ML
- Real-time calculations reduce data gaps
- Complete feature utilization

### Production Ready
- Scalable architecture with intelligent fallback
- Comprehensive monitoring by symbol-strategy
- Clear performance metrics for each model

---

**Status**: Phases 0-4 Complete ✅ | Phases 5-7 In Planning 📋
**Next Step**: Run profit scale analysis to fix SPX grouping
**Priority**: Fix delta data integration for immediate model improvement
# Magic8 Accuracy Predictor - Comprehensive Revamp Plan (v2)

**Updated**: January 1, 2025  
**Purpose**: Complete blueprint for improving Magic8 accuracy predictor with corrected data processing  
**Overall Completion Status**: ~80%

## 🚨 Critical Data Processing Issues Discovered

### New Findings:
1. **Data Processing is Incomplete**: Only capturing "profit" sheet data, missing crucial "trades" and "delta" sheets
2. **Format Year Bug**: Incorrect year assignment (2023 for 2024 trades)
3. **Missing Key Features**:
   - Strike-by-strike breakdown (Strike1-4, Direction1-4, Type1-4)
   - Magic8's prediction indicators (Predicted, ShortTerm, LongTerm, Target1, Target2)
   - Delta values (CallDelta, PutDelta)
4. **Symbol-Specific Profit Scales**: NDX butterfly ~$3,800 vs XSP/QQQ ~$50-100 (76x difference!)

### Impact:
- Current model is missing critical predictive features
- Cannot properly model per-symbol profit patterns
- Evaluation metrics are based on incomplete data

## 📊 Phase 0: Complete Data Processing Rebuild [3-4 days] - 100% COMPLETE ✅

### 0.1 Fix process_magic8_data_optimized_v2.py ✓ COMPLETE

**Key Changes Required**: ✓ ALL IMPLEMENTED

```python
class Magic8DataProcessorOptimized:
    def __init__(self, source_path: str, output_path: str, batch_size: int = 1000):
        # ... existing code ...
        
        # EXPANDED column order to include all sheets ✓
        self.column_order = [
            # Time/Identity columns
            'date', 'time', 'timestamp', 'symbol', 'strategy',
            
            # From profit sheet
            'price', 'premium', 'predicted', 'closed', 'expired', 
            'risk', 'reward', 'ratio', 'profit', 'win',
            
            # From trades sheet (NEW) ✓
            'source', 'expected_move', 'low', 'high', 
            'target1', 'target2', 'predicted_trades', 'closing',
            'strike1', 'direction1', 'type1', 'bid1', 'ask1', 'mid1',
            'strike2', 'direction2', 'type2', 'bid2', 'ask2', 'mid2',
            'strike3', 'direction3', 'type3', 'bid3', 'ask3', 'mid3',
            'strike4', 'direction4', 'type4', 'bid4', 'ask4', 'mid4',
            
            # From delta sheet (NEW) ✓
            'call_delta', 'put_delta', 'predicted_delta', 
            'short_term', 'long_term', 'closing_delta',
            
            # Metadata
            'trade_description', 'source_file', 'format_year'
        ]
        
    def process_folder(self, folder: Path): ✓
        """Process all files in a single date folder"""
        # Extract date from folder name
        folder_date = self.extract_date_from_folder(folder.name)
        if not folder_date:
            return
        
        # Get all CSV files ✓
        files = {
            'profit': None,
            'delta': None,
            'trades': None
        }
        
        for file_path in folder.glob('*.csv'):
            if 'profit' in file_path.name:
                files['profit'] = file_path
            elif 'delta' in file_path.name:
                files['delta'] = file_path
            elif 'trades' in file_path.name:
                files['trades'] = file_path
        
        # Process all three files and merge data ✓
        trades_data = {}
        
        # 1. Process profit file (base data) ✓
        if files['profit']:
            profit_trades = self.process_profit_file(files['profit'], folder_date)
            for trade in profit_trades:
                key = self._create_trade_key(trade)
                trades_data[key] = trade
        
        # 2. Enhance with trades file data ✓
        if files['trades']:
            trades_info = self.process_trades_file_enhanced(files['trades'], folder_date)
            for trade in trades_info:
                key = self._create_trade_key(trade)
                if key in trades_data:
                    # Merge trades data into existing record
                    trades_data[key].update(trade)
                else:
                    # New trade not in profit file
                    trades_data[key] = trade
        
        # 3. Add delta sheet data (applies to all trades for that time) ✓
        if files['delta']:
            delta_data = self.process_delta_file(files['delta'], folder_date)
            # Apply delta data to all trades at matching times
            for key, trade in trades_data.items():
                time_key = f"{trade['date']} {trade['time']}"
                if time_key in delta_data:
                    trade.update(delta_data[time_key])
        
        # Add all merged trades to batch ✓
        for trade in trades_data.values():
            self.validate_and_add_trade(trade, str(folder))
    
    def _create_trade_key(self, trade: Dict) -> str: ✓
        """Create unique key for trade matching"""
        return f"{trade.get('date')}_{trade.get('time')}_{trade.get('symbol')}_{trade.get('strategy')}"
    
    def process_trades_file_enhanced(self, file_path: Path, folder_date: datetime): ✓
        """Process trades file with full strike breakdown"""
        trades = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 2):
                # Extract all strike information ✓
                trade = {
                    'date': folder_date.strftime('%Y-%m-%d'),
                    'time': self.clean_string(row.get('Time', '')),
                    'source': self.clean_string(row.get('Source', '')),
                    'symbol': self.clean_string(row.get('Symbol', '')),
                    'strategy': self.clean_string(row.get('Name', '')),
                    'premium': self.safe_float(row.get('Premium')),
                    'risk': self.safe_float(row.get('Risk')),
                    'expected_move': self.safe_float(row.get('ExpectedMove')),
                    'low': self.safe_float(row.get('Low')),
                    'high': self.safe_float(row.get('High')),
                    'target1': self.safe_float(row.get('Target1')),
                    'target2': self.safe_float(row.get('Target2')),
                    'predicted_trades': self.safe_float(row.get('Predicted')),
                    'closing': self.safe_float(row.get('Closing')),
                    
                    # Strike details (up to 4 legs) ✓
                    'strike1': self.safe_float(row.get('Strike1')),
                    'direction1': self.clean_string(row.get('Direction1', '')),
                    'type1': self.clean_string(row.get('Type1', '')),
                    'bid1': self.safe_float(row.get('Bid1')),
                    'ask1': self.safe_float(row.get('Ask1')),
                    'mid1': self.safe_float(row.get('Mid1')),
                    
                    'strike2': self.safe_float(row.get('Strike2')),
                    'direction2': self.clean_string(row.get('Direction2', '')),
                    'type2': self.clean_string(row.get('Type2', '')),
                    'bid2': self.safe_float(row.get('Bid2')),
                    'ask2': self.safe_float(row.get('Ask2')),
                    'mid2': self.safe_float(row.get('Mid2')),
                    
                    'strike3': self.safe_float(row.get('Strike3')),
                    'direction3': self.clean_string(row.get('Direction3', '')),
                    'type3': self.clean_string(row.get('Type3', '')),
                    'bid3': self.safe_float(row.get('Bid3')),
                    'ask3': self.safe_float(row.get('Ask3')),
                    'mid3': self.safe_float(row.get('Mid3')),
                    
                    'strike4': self.safe_float(row.get('Strike4')),
                    'direction4': self.clean_string(row.get('Direction4', '')),
                    'type4': self.clean_string(row.get('Type4', '')),
                    'bid4': self.safe_float(row.get('Bid4')),
                    'ask4': self.safe_float(row.get('Ask4')),
                    'mid4': self.safe_float(row.get('Mid4')),
                    
                    'trade_description': self.clean_string(row.get('Trade', '')),
                    'source_file': 'trades',
                    'format_year': folder_date.year  # FIX: Use actual folder date year ✓
                }
                
                trades.append(trade)
        
        return trades
    
    def process_delta_file(self, file_path: Path, folder_date: datetime): ✓
        """Process delta file for prediction indicators"""
        delta_data = {}
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Parse time from "When" column (format: "7/3/25 14:30")
                when = self.clean_string(row.get('When', ''))
                if when:
                    # Extract time portion
                    time_part = when.split()[-1] if ' ' in when else ''
                    
                    time_key = f"{folder_date.strftime('%Y-%m-%d')} {time_part}"
                    
                    delta_data[time_key] = {
                        'call_delta': self.safe_float(row.get('CallDelta')),
                        'put_delta': self.safe_float(row.get('PutDelta')),
                        'predicted_delta': self.safe_float(row.get('Predicted')),
                        'short_term': self.safe_float(row.get('ShortTerm')),
                        'long_term': self.safe_float(row.get('LongTerm')),
                        'closing_delta': self.safe_float(row.get('Closing'))
                    }
        
        return delta_data
```

**Additional Implemented Features**:
- ✓ Duplicate detection using `seen_trade_keys`
- ✓ Timestamp validation with statistics tracking
- ✓ Quality issue tracking (duplicates, bad timestamps, etc.)
- ✓ Format year bug fixed (uses actual folder date)

### 0.2 Create Symbol-Specific Data Splits ✓ COMPLETE

```python
def split_data_by_symbol(input_file: str, output_dir: str): ✓
    """Split aggregated data into symbol-specific files"""
    
    df = pd.read_csv(input_file)
    symbols = df['symbol'].unique()
    
    os.makedirs(output_dir, exist_ok=True)
    
    symbol_stats = {}
    
    for symbol in symbols:
        symbol_df = df[df['symbol'] == symbol]
        
        # Save symbol-specific file ✓
        output_file = os.path.join(output_dir, f'{symbol}_trades.csv')
        symbol_df.to_csv(output_file, index=False)
        
        # Calculate symbol-specific statistics ✓
        symbol_stats[symbol] = {
            'total_trades': len(symbol_df),
            'strategies': symbol_df['strategy'].value_counts().to_dict(),
            'avg_profit': symbol_df['profit'].mean(),
            'profit_by_strategy': {}
        }
        
        # Profit statistics by strategy ✓
        for strategy in ['Butterfly', 'Iron Condor', 'Sonar', 'Vertical']:
            strategy_data = symbol_df[symbol_df['strategy'] == strategy]
            if len(strategy_data) > 0:
                symbol_stats[symbol]['profit_by_strategy'][strategy] = {
                    'count': len(strategy_data),
                    'avg_profit': strategy_data['profit'].mean(),
                    'win_rate': (strategy_data['profit'] > 0).mean(),
                    'avg_win': strategy_data[strategy_data['profit'] > 0]['profit'].mean() if any(strategy_data['profit'] > 0) else 0,
                    'avg_loss': strategy_data[strategy_data['profit'] <= 0]['profit'].mean() if any(strategy_data['profit'] <= 0) else 0
                }
    
    # Save statistics ✓
    with open(os.path.join(output_dir, 'symbol_statistics.json'), 'w') as f:
        json.dump(symbol_stats, f, indent=2)
    
    return symbol_stats
```

### 0.3 Analyze Symbol-Specific Patterns ✓ COMPLETE

```python
class SymbolSpecificAnalyzer: ✓ IMPLEMENTED IN src/symbol_analyzer.py
    """Analyze profit patterns by symbol"""
    
    def analyze_profit_scales(self, symbol_stats: Dict): ✓ COMPLETE
        """Identify symbols with similar profit scales"""
        
        # Group symbols by profit scale
        profit_groups = {
            'large_scale': [],   # >$1000 avg butterfly profit
            'medium_scale': [],  # $100-1000
            'small_scale': []    # <$100
        }
        
        for symbol, stats in symbol_stats.items():
            butterfly_profit = stats['profit_by_strategy'].get('Butterfly', {}).get('avg_profit', 0)
            
            if abs(butterfly_profit) > 1000:
                profit_groups['large_scale'].append(symbol)
            elif abs(butterfly_profit) > 100:
                profit_groups['medium_scale'].append(symbol)
            else:
                profit_groups['small_scale'].append(symbol)
        
        return profit_groups
    
    def recommend_model_grouping(self, profit_groups: Dict): ✓ IMPLEMENTED
        """Recommend how to group symbols for model training"""
        
        recommendations = {
            'separate_models': [],  # Train individual models
            'grouped_models': {},   # Train grouped models
            'unified_model': []     # Can use unified model
        }
        
        # Large scale symbols need separate models
        recommendations['separate_models'] = profit_groups['large_scale']
        
        # Medium scale can be grouped if similar
        if len(profit_groups['medium_scale']) > 3:
            recommendations['grouped_models']['medium_scale'] = profit_groups['medium_scale']
        else:
            recommendations['separate_models'].extend(profit_groups['medium_scale'])
        
        # Small scale can use unified model
        recommendations['unified_model'] = profit_groups['small_scale']
        
        return recommendations
```

**Completed Items**:
- ✓ `recommend_model_grouping` method implemented in `src/symbol_analyzer.py`
- ✓ Formal data schema documentation created in `docs/DATA_SCHEMA_COMPLETE.md`

## 📈 Phase 1: Feature Engineering with Complete Data [2-3 days] - 90% COMPLETE

### 1.1 Create Magic8-Specific Features ✓ COMPLETE

```python
class Magic8FeatureEngineer: ✓ ENHANCED
    """Extract features from Magic8's prediction logic"""
    
    def create_prediction_features(self, df): ✓ IMPLEMENTED
        """Features based on Magic8's prediction indicators"""
        
        # Price target features
        if {'target1', 'price'}.issubset(df.columns):
            df['distance_to_target1'] = (df['target1'] - df['price']) / df['price']
        if {'target2', 'price'}.issubset(df.columns):
            df['distance_to_target2'] = (df['target2'] - df['price']) / df['price']
        if {'target1', 'target2', 'price'}.issubset(df.columns):
            df['targets_spread'] = abs(df['target1'] - df['target2']) / df['price']
        
        # Prediction alignment
        if {'predicted_trades', 'price'}.issubset(df.columns):
            df['predicted_vs_price'] = (df['predicted_trades'] - df['price']) / df['price']
        if {'predicted_trades', 'closing'}.issubset(df.columns):
            df['predicted_vs_closing'] = (df['predicted_trades'] - df['closing']) / df['predicted_trades'].replace(0, 1e-9)
        
        # Delta features
        if {'call_delta', 'put_delta'}.issubset(df.columns):
            df['call_put_delta_spread'] = df['call_delta'] - df['put_delta']
            if 'price' in df.columns:
                df['delta_skew'] = df['call_put_delta_spread'] / df['price']
        
        # Short/Long term bias
        if {'short_term', 'price'}.issubset(df.columns):
            df['short_term_bias'] = (df['short_term'] - df['price']) / df['price']
        if {'long_term', 'price'}.issubset(df.columns):
            df['long_term_bias'] = (df['long_term'] - df['price']) / df['price']
        if {'short_term', 'long_term'}.issubset(df.columns):
            df['term_structure'] = df['short_term'] - df['long_term']
        
        # Expected move utilization
        if {'high', 'low', 'expected_move'}.issubset(df.columns):
            df['strike_width_ratio'] = (df['high'] - df['low']) / df['expected_move'].replace(0, 1e-9)
        
        return df
    
    def add_strike_features(self, df): ✓ ENHANCED
        """Features from strike structure"""
        # Enhanced implementation with:
        # - strike_distance_pct: relative width of strikes
        # - avg_strike: average strike price
        # - strike_width: absolute width
        
    def add_delta_features(self, df): ✓ ENHANCED
        """Features from delta sheet indicators"""
        # Enhanced implementation with:
        # - delta_diff: call_delta - put_delta
        # - delta_error: predicted_delta vs actual
        # - term_structure: short_term - long_term
        
    def add_microstructure_features(self, df): ✓ IMPLEMENTED
        """Features from bid-ask spreads"""
        # Implemented with:
        # - spread1, spread2: bid-ask spreads per leg
```

**Current State**:
- ✓ `Magic8FeatureEngineer` class enhanced
- ✓ `create_prediction_features` method implemented
- ✓ `add_strike_features` improved with comprehensive features
- ✓ `add_delta_features` now uses delta sheet indicators
- ✓ `add_microstructure_features` implemented
- ✓ All features integrated into Phase 1 pipeline

### 1.2 Create Symbol-Normalized Features ✓ COMPLETE

```python
class SymbolNormalizer: ✓ IMPLEMENTED
    """Normalize features by symbol to handle scale differences"""
    
    def __init__(self, symbol_stats: pd.DataFrame):
        self.stats = symbol_stats.set_index('symbol')

    def transform(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        df = df.copy()
        for symbol, group in df.groupby('symbol'):
            if symbol in self.stats.index:
                mean = self.stats.loc[symbol, 'mean']
                std = self.stats.loc[symbol, 'std']
                df.loc[group.index, columns] = (group[columns] - mean) / (std + 1e-9)
        return df
```

**Current State**:
- ✓ Symbol normalization implemented and integrated into Phase 1 pipeline
- ✓ Applied to profit columns per symbol using statistics

## 🧠 Phase 2: Symbol-Specific Model Architecture [3-4 days] - 65% COMPLETE

### 2.1 Model Strategy Decision Tree ✓ ENHANCED

```python
class SymbolModelStrategy: ✓ ENHANCED
    """Define mapping from symbols to model paths with default support"""
    
    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping
        self.default = mapping.get('default')

    def get_model_path(self, symbol: str) -> str:
        return self.mapping.get(symbol)
```

**Current State**:
- ✓ Enhanced with default model support for unseen symbols
- ✓ Configured in config.yaml with model paths

### 2.2 Multi-Model Architecture ✓ FUNCTIONAL IMPLEMENTATION

```python
class MultiModelPredictor: ✓ ENHANCED
    """Load and route predictions to symbol specific models"""
    
    def __init__(self, strategy: SymbolModelStrategy):
        self.strategy = strategy
        self.models: Dict[str, object] = {}

    def load_models(self): ✓ IMPLEMENTED
        """Load all configured models including default"""
        for sym, path in self.strategy.mapping.items():
            if sym == 'default':
                continue
            if path and Path(path).exists():
                self.models[sym] = joblib.load(path)
        if self.strategy.default and Path(self.strategy.default).exists():
            self.default_model = joblib.load(self.strategy.default)
        else:
            self.default_model = None

    def predict_proba(self, symbol: str, features): ✓ IMPLEMENTED
        """Route to appropriate model with default fallback"""
        model = self.models.get(symbol)
        if model is None:
            if self.default_model is None:
                raise ValueError(f"No model for symbol {symbol}")
            model = self.default_model
        return model.predict_proba(features)
```

**Current State**:
- ✓ Model loading and routing implemented
- ✓ Default model fallback support added
- ✓ Configuration integrated with config.yaml
- ✓ Demo models configured (NDX, XSP)
- ✗ No grouped models created yet
- ✗ No threshold optimization

### 2.3 Symbol-Specific XGBoost Model ✓ IMPLEMENTED

```python
def train_symbol_model(csv_path: Path, model_dir: Path, features: list, target: str = "target"): ✓
    """Train XGBoost model for a specific symbol with missing feature handling"""
    
    df = pd.read_csv(csv_path)
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' missing in {csv_path}")
    
    # Select only features that exist in the data
    selected = [f for f in features if f in df.columns]
    if not selected:
        raise ValueError("No matching features found in data")
    if len(selected) != len(features):
        missing = set(features) - set(selected)
        print(f"Warning: missing features {missing} in {csv_path}")
    
    X = df[selected]
    y = df[target]
    dtrain = xgb.DMatrix(X, label=y)
    
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 4,
        'eta': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
    }
    
    model = xgb.train(params, dtrain, num_boost_round=200)
    
    # Save model and feature list as pickle files
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / f"{csv_path.stem}_model.pkl")
    joblib.dump(selected, model_dir / f"{csv_path.stem}_features.pkl")
    
    return model
```

**Current State**:
- ✓ Implementation complete with missing feature handling
- ✓ Model persistence via pickle files
- ✓ Demo models trained for NDX (large scale) and XSP (small scale)
- ✗ Not all symbols have models trained yet

### 2.4 Configuration ✓ UPDATED

```yaml
# config/config.yaml
models:
  NDX: models/demo_models/NDX_trades_model.pkl
  XSP: models/demo_models/XSP_trades_model.pkl
  default: models/xgboost_phase1_model.pkl

prediction:
  feature_config:
    temporal:
      enabled: true
```

## 🔧 Phase 3: Model Evaluation Fixes [1-2 days] - 50% COMPLETE

### 3.1 Fix Baseline with Complete Data ✓ ENHANCED

```python
def evaluate_profit_impact_corrected(model, test_data, symbol_stats): ✓ IMPLEMENTED
    """Evaluate with correct baseline using all available features"""
    
    if 'profit' not in self.test_df.columns:
        raise ValueError("Profit column missing from test data")

    baseline_profit = self.test_df['profit'].sum()

    dtest = xgb.DMatrix(self.X_test)
    preds = (self.model.predict(dtest) > 0.5).astype(int)
    model_profit = 0.0

    for pred, profit in zip(preds, self.test_df['profit']):
        if pred == 1:
            model_profit += profit

    return {
        'baseline_profit': float(baseline_profit),
        'model_profit': float(model_profit),
        'profit_improvement': float(model_profit - baseline_profit),
        'profit_improvement_pct': ((model_profit - baseline_profit) / abs(baseline_profit) * 100) if baseline_profit != 0 else 0,
    }

def evaluate_profit_by_symbol(self): ✓ NEW METHOD
    """Compute baseline and model profit per symbol."""
    if 'profit' not in self.test_df.columns or 'symbol' not in self.test_df.columns:
        raise ValueError("Required columns missing from test data")

    dtest = xgb.DMatrix(self.X_test)
    preds = (self.model.predict(dtest) > 0.5).astype(int)
    self.test_df['pred'] = preds
    results = {}
    for sym, group in self.test_df.groupby('symbol'):
        baseline = group['profit'].sum()
        model_profit = group.loc[group['pred'] == 1, 'profit'].sum()
        results[sym] = {
            'baseline_profit': float(baseline),
            'model_profit': float(model_profit),
            'profit_improvement': float(model_profit - baseline),
        }
    
    return results
```

**Current State**:
- ✓ `evaluate_profit_impact_corrected` method implemented
- ✓ `evaluate_profit_by_symbol` method added for per-symbol analysis
- ✗ Doesn't use symbol-specific baselines yet
- ✗ No threshold optimization per symbol-strategy
- ✗ No validation of handling 76x profit scales

## 📊 Phase 4: Updated Implementation Timeline [2-3 weeks total]

### Week 1: Data Processing & Feature Engineering
**Days 1-3: Rebuild Data Processing**
- [x] Fix process_magic8_data_optimized_v2.py with all sheets
- [x] Create symbol-specific data splits
- [x] Analyze profit scale patterns
- [x] Document data schema
- [x] Implement model grouping recommendations

**Days 4-5: Feature Engineering**
- [x] Implement Magic8-specific prediction features
- [x] Create strike structure features
- [x] Add market microstructure features
- [x] Implement symbol normalization

### Week 2: Model Development
**Days 6-8: Multi-Model Architecture**
- [x] Implement symbol model strategy with default support
- [x] Create XGBoost symbol-specific model implementation
- [x] Train demo models (NDX, XSP)
- [x] Implement model routing with fallback

**Days 9-10: Evaluation & Optimization**
- [x] Fix baseline calculations with actual data
- [x] Add per-symbol profit evaluation
- [ ] Optimize thresholds per symbol-strategy
- [ ] Test profit improvements
- [ ] Create performance dashboard

### Week 3: Integration & Testing
**Days 11-12: API Updates**
- [x] Update prediction API for multi-model
- [ ] Add symbol-aware feature generation
- [x] Implement model selection logic with default

**Days 13-14: Testing & Documentation**
- [ ] End-to-end testing
- [ ] Performance benchmarking
- [x] Documentation updates
- [ ] Deployment preparation

## 🎯 Success Metrics (Updated)

### Per-Symbol Targets:

**Large Scale (NDX, RUT)**:
- [x] Demo model trained for NDX
- [ ] Train model for RUT
- [ ] Maintain current profit levels
- [ ] Improve selectivity to 70-80%
- [ ] Reduce maximum drawdowns

**Medium Scale (SPX, SPY)**:
- [ ] Train grouped model
- [ ] Increase profit per trade by 50%
- [ ] Optimize for consistency
- [ ] Target 65-75% trade selection

**Small Scale (XSP, QQQ, AAPL, TSLA)**:
- [x] Demo model trained for XSP
- [ ] Train models for remaining symbols
- [ ] Focus on win rate improvement
- [ ] May need different strategy mix
- [ ] Consider discontinuing low-profit strategies

### Overall Targets:
1. **Data Completeness**: ✓ 100% capture of all sheet data
2. **Feature Coverage**: ✓ Use all Magic8 prediction indicators (complete)
3. **Model Accuracy**: ⏳ Appropriate to symbol scale (demo models trained)
4. **Profit Improvement**: ✗ 50%+ over corrected baseline (pending validation)

## 🔑 Critical Next Steps

1. **Complete Symbol-Specific Model Training**: 
   - Train models for ALL symbols (currently only NDX and XSP demo models)
   - Focus on RUT (large scale), SPX/SPY (medium scale), and remaining small scale symbols
   - Use the `train_symbol_models.py` script with appropriate data directories

2. **Implement Grouped Models**:
   - Create grouped model for medium scale symbols (SPX, SPY)
   - Create grouped model for small scale symbols (QQQ, AAPL, TSLA)
   - Test performance vs individual models

3. **Optimize Thresholds Per Symbol-Strategy**:
   - Use `optimize_thresholds.py` to find optimal decision thresholds
   - Apply per-symbol profit evaluation results
   - Ensure each symbol-strategy combination has appropriate thresholds

4. **Validate 76x Scale Handling**:
   - Run comprehensive tests comparing NDX vs XSP model performance
   - Ensure profit calculations properly account for scale differences
   - Verify model predictions are appropriate for each symbol's profit profile

5. **Complete Integration Testing**:
   - Test end-to-end pipeline with all symbol models
   - Verify API correctly routes to appropriate models and falls back to default
   - Validate real-time prediction performance across all symbols
   - Measure actual profit improvements per symbol

This comprehensive update addresses the fundamental data issues and provides a path to symbol-aware modeling that can handle the 76x profit scale differences across symbols.

**Current Status Summary**:
- ✓ Data processing and infrastructure complete
- ✓ Feature engineering complete with all Magic8 prediction features
- ✓ Per-symbol profit evaluation implemented
- ✓ Symbol-specific model architecture implemented with missing feature handling
- ✓ Demo models trained (NDX, XSP) with default fallback
- ✗ Full model training for all symbols pending
- ✗ Performance validation pending

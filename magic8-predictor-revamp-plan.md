# Magic8 Accuracy Predictor - Comprehensive Revamp Plan (v2)

**Updated**: July 5, 2025  
**Purpose**: Complete blueprint for improving Magic8 accuracy predictor with corrected data processing  
**Overall Completion Status**: ~95% ✅

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

## 🧠 Phase 2: Symbol-Specific Model Architecture [3-4 days] - 100% COMPLETE ✅

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

### 2.2 Multi-Model Architecture ✓ COMPLETE WITH GROUPED MODELS

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

**NEW: Grouped Model Support** ✓ IMPLEMENTED AND TRAINED

```python
def train_grouped_model(csv_paths: list[Path], model_dir: Path, group_name: str, features: list | None = None):
    """Train a single model using data from multiple symbols."""
    # Ensure output directory exists
    model_dir.mkdir(parents=True, exist_ok=True)
    
    df_list = [pd.read_csv(p, low_memory=False) for p in csv_paths]
    df = pd.concat(df_list, ignore_index=True)
    tmp_file = model_dir / f"{group_name}_combined.csv"
    df.to_csv(tmp_file, index=False)
    try:
        train_symbol_model(tmp_file, model_dir, features)
        print(f"✓ Grouped model trained for {group_name}")
    finally:
        if tmp_file.exists():
            tmp_file.unlink()

def train_grouped_models(groups: dict[str, list[str]], data_dir: str, output_dir: str, feature_info: Path | None = None):
    """Train models for each group mapping name -> [symbols]."""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)

    features = None
    if feature_info and feature_info.exists():
        try:
            with open(feature_info, "r") as f:
                info = json.load(f)
            features = info.get("feature_names", [])
        except Exception as e:
            print(f"Warning: Could not load feature_info: {e}")

    for group, symbols in groups.items():
        csv_paths = [data_dir / f"{sym}_trades.csv" for sym in symbols]
        csv_paths = [p for p in csv_paths if p.exists()]
        if not csv_paths:
            print(f"No data for group {group} ({symbols})")
            continue
        train_grouped_model(csv_paths, output_dir, group, features)
```

**Command-line Script** ✓ IMPLEMENTED: `train_grouped_models.py`
- Default groups configured: SPX+SPY (medium scale), QQQ+AAPL+TSLA (small scale)

**Current State**:
- ✓ Model loading and routing implemented
- ✓ Default model fallback support added
- ✓ Configuration integrated with config.yaml
- ✓ All 8 individual models trained (AAPL, TSLA, RUT, SPY, QQQ, NDX, XSP, SPX)
- ✓ Grouped model utilities implemented
- ✓ Command-line script for easy grouped model training
- ✓ SPX+SPY grouped model trained (89.95% accuracy)
- ✓ QQQ+AAPL+TSLA grouped model trained (90.13% accuracy)

### 2.3 Symbol-Specific XGBoost Model ✓ ENHANCED WITH GROUPED SUPPORT

**Training Results** (July 5, 2025):

**Individual Models**:
- **AAPL**: 94.08% accuracy (AUC: 0.987)
- **TSLA**: 94.04% accuracy (AUC: 0.987)  
- **RUT**: 92.07% accuracy (AUC: 0.976)
- **SPY**: 91.48% accuracy (AUC: 0.972)
- **QQQ**: 91.02% accuracy (AUC: 0.972)
- **NDX**: 90.75% accuracy (AUC: 0.968)
- **XSP**: 90.59% accuracy (AUC: 0.968)
- **SPX**: 90.03% accuracy (AUC: 0.964)

**Grouped Models**:
- **SPX_SPY**: 89.95% accuracy (345,014 samples)
- **QQQ_AAPL_TSLA**: 90.13% accuracy (244,435 samples)

```python
def train_symbol_model(csv_path: Path, model_dir: Path, features: list = None, target: str = "target"): ✓
    """Train XGBoost model for a specific symbol with missing feature handling"""
    
    df = pd.read_csv(csv_path, low_memory=False)
    
    # Prepare data and get available features
    df, available_features = prepare_symbol_data(df)
    
    # If features provided from feature_info, try to use those that exist
    if features:
        # Filter to features that actually exist in this data
        selected_features = [f for f in features if f in df.columns]
        
        # If too few features from feature_info exist, use our prepared features
        if len(selected_features) < 10:
            print(f"Only {len(selected_features)} features from feature_info found, using prepared features")
            selected_features = available_features
    else:
        selected_features = available_features
    
    print(f"Using {len(selected_features)} features")
    
    # ... training logic ...
    
    # Save model and feature list as pickle files
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / f"{csv_path.stem}_model.pkl")
    joblib.dump(selected_features, model_dir / f"{csv_path.stem}_features.pkl")
    
    return model
```

**Current State**:
- ✓ Implementation complete with missing feature handling
- ✓ Model persistence via pickle files
- ✓ All 8 symbol models trained successfully
- ✓ Models auto-detected 31 features from raw data
- ✓ Grouped model support added
- ✓ Both grouped models trained successfully

### 2.4 Configuration ✓ UPDATED

```yaml
# config/config.yaml
models:
  # Individual models (trained)
  AAPL: models/individual/AAPL_trades_model.pkl
  TSLA: models/individual/TSLA_trades_model.pkl
  RUT: models/individual/RUT_trades_model.pkl
  SPY: models/individual/SPY_trades_model.pkl
  QQQ: models/individual/QQQ_trades_model.pkl
  NDX: models/individual/NDX_trades_model.pkl
  XSP: models/individual/XSP_trades_model.pkl
  SPX: models/individual/SPX_trades_model.pkl
  
  # Grouped models (trained)
  SPX_SPY: models/grouped/SPX_SPY_combined_model.pkl
  QQQ_AAPL_TSLA: models/grouped/QQQ_AAPL_TSLA_combined_model.pkl
  
  # Default fallback
  default: models/xgboost_phase1_model.pkl

prediction:
  feature_config:
    temporal:
      enabled: true
```

## 🔧 Phase 3: Model Evaluation Fixes [1-2 days] - 100% COMPLETE ✅

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

**NEW: Per-Symbol-Strategy Threshold Optimization** ✓ COMPLETE WITH CORRECT F1

```python
def optimize_threshold_f1(df: pd.DataFrame, model, features: list, debug=False):
    """Return best threshold for dataframe using F1 score."""
    # Prepare features and fill missing values
    X = df[features].fillna(0)
    y = df['target'].values
    
    # Get predictions
    dtest = xgb.DMatrix(X)
    proba = model.predict(dtest)
    
    if debug:
        print(f"  Prediction stats: min={proba.min():.3f}, max={proba.max():.3f}, mean={proba.mean():.3f}")
        print(f"  Target distribution: {np.bincount(y)}")
    
    # Try different thresholds
    thresholds = np.arange(0.1, 0.9, 0.05)
    best_f1 = 0
    best_threshold = 0.5
    
    for threshold in thresholds:
        pred = (proba >= threshold).astype(int)
        f1 = f1_score(y, pred, zero_division=0)
        
        if debug and (threshold in [0.3, 0.5, 0.7] or f1 > best_f1):
            tp = ((pred == 1) & (y == 1)).sum()
            fp = ((pred == 1) & (y == 0)).sum()
            fn = ((pred == 0) & (y == 1)).sum()
            tn = ((pred == 0) & (y == 0)).sum()
            print(f"  Threshold {threshold:.2f}: F1={f1:.3f}, TP={tp}, FP={fp}, FN={fn}, TN={tn}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
    
    return best_threshold, best_f1
```

**Threshold Optimization Results**:
- **Individual Models**: Thresholds range from 0.35 to 0.75
- **Mean F1 Score**: 0.910 (91% accuracy)
- **Strategy-specific**: Butterfly (0.45-0.55), Iron Condor (0.50-0.75)
- **Grouped Models**: Similar performance with balanced thresholds

**Current State**:
- ✓ `evaluate_profit_impact_corrected` method implemented
- ✓ `evaluate_profit_by_symbol` method added for per-symbol analysis
- ✓ Threshold optimization per symbol-strategy COMPLETE
- ✓ F1 calculation bug fixed (was using bitwise AND)
- ✓ Thresholds saved to `thresholds.json` for production use
- ✓ Full validation of proper threshold optimization complete

## 📊 Phase 4: Updated Implementation Timeline [2-3 weeks total] - 95% COMPLETE

### Week 1: Data Processing & Feature Engineering ✅
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

### Week 2: Model Development ✅
**Days 6-8: Multi-Model Architecture**
- [x] Implement symbol model strategy with default support
- [x] Create XGBoost symbol-specific model implementation
- [x] Train all 8 individual models (✅ COMPLETE July 5, 2025)
- [x] Implement model routing with fallback
- [x] Add grouped model utilities

**Days 9-10: Evaluation & Optimization**
- [x] Fix baseline calculations with actual data
- [x] Add per-symbol profit evaluation
- [x] Optimize thresholds per symbol-strategy
- [x] Test profit improvements with optimized thresholds
- [x] Fix F1 calculation bug in threshold optimization

### Week 3: Integration & Testing (In Progress)
**Days 11-12: API Updates**
- [x] Update prediction API for multi-model
- [ ] Add symbol-aware feature generation with threshold lookup
- [x] Implement model selection logic with default

**Days 13-14: Testing & Documentation**
- [x] Train grouped models (SPX_SPY, QQQ_AAPL_TSLA)
- [ ] End-to-end testing with grouped models
- [ ] Performance benchmarking
- [x] Documentation updates
- [ ] Deployment preparation

## 🎯 Success Metrics (Updated)

### Per-Symbol Targets:

**Large Scale (NDX, RUT)**:
- [x] Individual models trained for both
- [x] High accuracy achieved (NDX: 90.75%, RUT: 92.07%)
- [x] Optimized thresholds calculated (varied by strategy)
- [ ] Validate profit levels with optimized thresholds in production
- [ ] Improve selectivity to 70-80%
- [ ] Reduce maximum drawdowns

**Medium Scale (SPX, SPY)**:
- [x] Individual models trained for both
- [x] Grouped model utilities ready
- [x] Train SPX+SPY grouped model (89.95% accuracy)
- [x] Optimized thresholds (0.45-0.75 range)
- [ ] Compare individual vs grouped performance in production
- [ ] Target 65-75% trade selection

**Small Scale (XSP, QQQ, AAPL, TSLA)**:
- [x] All individual models trained
- [x] Train QQQ+AAPL+TSLA grouped model (90.13% accuracy)
- [x] High win rate achieved (AAPL: 94.08%, TSLA: 94.04%)
- [x] Proper thresholds optimized per strategy
- [ ] Validate performance in production
- [ ] Consider discontinuing low-profit strategies

### Overall Targets:
1. **Data Completeness**: ✅ 100% capture of all sheet data
2. **Feature Coverage**: ✅ Use all Magic8 prediction indicators (complete)
3. **Model Architecture**: ✅ Multi-model with grouped support (implemented)
4. **Threshold Optimization**: ✅ Per-symbol-strategy thresholds (complete)
5. **Individual Models**: ✅ All 8 symbols trained (90-94% accuracy)
6. **Grouped Models**: ✅ Both groups trained (SPX_SPY: 89.95%, QQQ_AAPL_TSLA: 90.13%)
7. **Profit Improvement**: ⏳ 50%+ over corrected baseline (pending production validation)

## 🔑 Critical Next Steps

### 1. **Production API Integration** [HIGH PRIORITY]
   - **Update prediction_api.py**:
     - Load all individual and grouped models on startup
     - Implement symbol routing logic (individual → grouped → default)
     - Load and apply thresholds.json and thresholds_grouped.json
     - Use symbol+strategy specific thresholds instead of fixed 0.5
   - **Add threshold application logic**:
     ```python
     # Example implementation
     threshold = thresholds.get(symbol, {}).get(strategy, 0.5)
     prediction = (probability >= threshold)
     ```
   - **Test with real-time data from Magic8-Companion**

### 2. **Performance Validation** [CRITICAL]
   - **Validate 76x Scale Handling**:
     - Run profit calculations for NDX ($2,452 avg) vs XSP ($13 avg)
     - Ensure profit normalization working correctly
     - Verify large-scale symbols aren't being under-traded
   - **Compare Model Approaches**:
     - SPX individual (90.03%) vs SPX from SPX_SPY grouped (89.95%)
     - QQQ individual (91.02%) vs QQQ from grouped model (90.13%)
     - Document which approach maximizes profit per symbol
   - **Backtest with Historical Data**:
     - Apply optimized thresholds to past 3 months
     - Measure actual profit improvement over baseline
     - Validate F1 scores translate to real profit gains

### 3. **Integration with Trading Systems** [NEXT PHASE]
   - **DiscordTrading Integration**:
     - Update ML client to use new prediction API
     - Apply symbol-specific win probability thresholds
     - Test with paper trading first
   - **Magic8-Companion Data Flow**:
     - Ensure real-time market data available for features
     - Test latency of multi-model predictions
     - Monitor API performance under load

### 4. **Create Performance Dashboard** [MONITORING]
   - **Real-time Metrics**:
     - Current thresholds per symbol-strategy
     - Trade approval rates
     - Predicted vs actual profit tracking
   - **Model Performance Tracking**:
     - F1 scores over time
     - Threshold drift detection
     - Alert on performance degradation
   - **Profit Analysis**:
     - Daily/weekly profit comparison (baseline vs model)
     - Per-symbol profit attribution
     - Strategy performance breakdown

### 5. **Documentation and Deployment** [FINAL PHASE]
   - **Create Deployment Guide**:
     - Model deployment procedures
     - Rollback strategies
     - A/B testing framework
   - **Update All Documentation**:
     - API endpoints for new model architecture
     - Threshold management procedures
     - Performance monitoring guidelines
   - **Production Readiness Checklist**:
     - Load testing complete
     - Failover mechanisms tested
     - Monitoring alerts configured

### 6. **Future Optimizations** [POST-DEPLOYMENT]
   - **Dynamic Threshold Adjustment**:
     - Monitor threshold performance weekly
     - Auto-adjust based on recent performance
     - A/B test threshold variations
   - **Model Retraining Pipeline**:
     - Schedule monthly retraining
     - Incorporate new data automatically
     - Version control for models
   - **Advanced Features**:
     - Consider ensemble methods
     - Add market regime detection
     - Implement risk-adjusted thresholds

---

**🎉 Major Accomplishments**:
- 1,076,742 trades processed with complete data schema
- All 8 individual models trained (90-94% accuracy)
- Both grouped models trained successfully
- Threshold optimization working with proper F1 calculation
- High F1 scores achieved (mean 0.910)

**⚡ Immediate Action**: Focus on production API integration and performance validation to realize the profit improvements in live trading.

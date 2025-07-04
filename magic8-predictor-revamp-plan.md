# Magic8 Accuracy Predictor - Comprehensive Revamp Plan (v2)

**Updated**: January 1, 2025  
**Purpose**: Complete blueprint for improving Magic8 accuracy predictor with corrected data processing  
**Overall Completion Status**: ~75%

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

## 🧠 Phase 2: Symbol-Specific Model Architecture [3-4 days] - 25% COMPLETE

### 2.1 Model Strategy Decision Tree ✓ BASIC INFRASTRUCTURE EXISTS

```python
class SymbolModelStrategy: ✓ EXISTS
    """Determine optimal model strategy per symbol"""
    
    # Basic implementation exists but no actual strategy logic
```

### 2.2 Multi-Model Architecture ✓ INFRASTRUCTURE ONLY

```python
class MultiModelPredictor: ✓ EXISTS
    """Manage multiple models for different symbols"""
    
    def __init__(self, model_strategy: Dict): ✓
        self.model_strategy = model_strategy
        self.models = {}
        self.scalers = {}
        self.threshold_optimizers = {}
        
    def train_all_models(self, data_dir: str): ✗ NOT IMPLEMENTED
        """Train appropriate models for each symbol group"""
        # Method doesn't exist in current implementation
        
    def predict(self, features: Dict, symbol: str, strategy: str) -> Dict: ✓ BASIC VERSION
        """Route prediction to appropriate model"""
        # Simplified version exists
```

**Current State**:
- ✓ Basic infrastructure created
- ✓ New `train_symbol_models.py` script created for training
- ✗ No actual multi-model training implemented yet
- ✗ No symbol-specific models trained
- ✗ No grouped models created
- ✗ No threshold optimization

### 2.3 Symbol-Specific XGBoost Model ✓ SCRIPT CREATED

```python
# train_symbol_models.py created with:
from src.models.xgboost_symbol_specific import train_all_models

def main():
    parser = argparse.ArgumentParser(description="Train symbol specific models")
    parser.add_argument("data_dir", help="Directory with *_trades.csv files")
    parser.add_argument("output_dir", help="Directory to store models")
    parser.add_argument("feature_info", help="JSON with feature names")
    args = parser.parse_args()

    train_all_models(args.data_dir, args.output_dir, Path(args.feature_info))
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
- [x] Implement symbol model strategy (infrastructure only)
- [ ] Create XGBoost symbol-specific models
- [ ] Train grouped models
- [x] Implement model routing (basic version)

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
- [x] Implement model selection logic (basic)

**Days 13-14: Testing & Documentation**
- [ ] End-to-end testing
- [ ] Performance benchmarking
- [x] Documentation updates
- [ ] Deployment preparation

## 🎯 Success Metrics (Updated)

### Per-Symbol Targets:

**Large Scale (NDX, RUT)**:
- [ ] Maintain current profit levels
- [ ] Improve selectivity to 70-80%
- [ ] Reduce maximum drawdowns

**Medium Scale (SPX, SPY)**:
- [ ] Increase profit per trade by 50%
- [ ] Optimize for consistency
- [ ] Target 65-75% trade selection

**Small Scale (XSP, QQQ, AAPL, TSLA)**:
- [ ] Focus on win rate improvement
- [ ] May need different strategy mix
- [ ] Consider discontinuing low-profit strategies

### Overall Targets:
1. **Data Completeness**: ✓ 100% capture of all sheet data
2. **Feature Coverage**: ✓ Use all Magic8 prediction indicators (complete)
3. **Model Accuracy**: ✗ Appropriate to symbol scale (pending)
4. **Profit Improvement**: ✗ 50%+ over corrected baseline (pending)

## 🔑 Critical Next Steps

1. **Train Symbol-Specific Models**: 
   - Use the new `train_symbol_models.py` script to train models per symbol/group
   - Validate handling of 76x profit scale differences

2. **Complete Phase 2 Implementation**:
   - Move from infrastructure to actual implementation
   - Train separate models for large scale symbols (NDX, RUT)
   - Train grouped models for medium scale (SPX, SPY) and small scale (XSP, QQQ, stocks)

3. **Optimize Thresholds Per Symbol-Strategy**:
   - Use the per-symbol profit evaluation to optimize decision thresholds
   - Ensure each symbol-strategy combination has appropriate thresholds

4. **Validate and Measure Results**:
   - Run comprehensive tests using the new test files
   - Measure actual profit improvements per symbol
   - Ensure the 76x scale differences are properly handled

5. **Integration Testing**:
   - Test the complete pipeline end-to-end
   - Ensure API correctly routes to appropriate models
   - Validate real-time prediction performance

This comprehensive update addresses the fundamental data issues and provides a path to symbol-aware modeling that can handle the 76x profit scale differences across symbols.

**Current Status Summary**:
- ✓ Data processing and infrastructure complete
- ✓ Feature engineering complete with all Magic8 prediction features
- ✓ Per-symbol profit evaluation implemented
- ✗ Symbol-specific models not trained yet
- ✗ Performance validation pending

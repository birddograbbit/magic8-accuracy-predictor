# Magic8 Accuracy Predictor - Comprehensive Revamp Plan (v2)

**Updated**: July 4, 2025  
**Purpose**: Complete blueprint for improving Magic8 accuracy predictor with corrected data processing

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

## 📊 Phase 0: Complete Data Processing Rebuild [3-4 days] - NEW PRIORITY

### 0.1 Fix process_magic8_data_optimized_v2.py

**Key Changes Required**:

```python
class Magic8DataProcessorOptimized:
    def __init__(self, source_path: str, output_path: str, batch_size: int = 1000):
        # ... existing code ...
        
        # EXPANDED column order to include all sheets
        self.column_order = [
            # Time/Identity columns
            'date', 'time', 'timestamp', 'symbol', 'strategy',
            
            # From profit sheet
            'price', 'premium', 'predicted', 'closed', 'expired', 
            'risk', 'reward', 'ratio', 'profit', 'win',
            
            # From trades sheet (NEW)
            'source', 'expected_move', 'low', 'high', 
            'target1', 'target2', 'predicted_trades', 'closing',
            'strike1', 'direction1', 'type1', 'bid1', 'ask1', 'mid1',
            'strike2', 'direction2', 'type2', 'bid2', 'ask2', 'mid2',
            'strike3', 'direction3', 'type3', 'bid3', 'ask3', 'mid3',
            'strike4', 'direction4', 'type4', 'bid4', 'ask4', 'mid4',
            
            # From delta sheet (NEW)
            'call_delta', 'put_delta', 'predicted_delta', 
            'short_term', 'long_term', 'closing_delta',
            
            # Metadata
            'trade_description', 'source_file', 'format_year'
        ]
        
    def process_folder(self, folder: Path):
        """Process all files in a single date folder"""
        # Extract date from folder name
        folder_date = self.extract_date_from_folder(folder.name)
        if not folder_date:
            return
        
        # Get all CSV files
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
        
        # Process all three files and merge data
        trades_data = {}
        
        # 1. Process profit file (base data)
        if files['profit']:
            profit_trades = self.process_profit_file(files['profit'], folder_date)
            for trade in profit_trades:
                key = self._create_trade_key(trade)
                trades_data[key] = trade
        
        # 2. Enhance with trades file data
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
        
        # 3. Add delta sheet data (applies to all trades for that time)
        if files['delta']:
            delta_data = self.process_delta_file(files['delta'], folder_date)
            # Apply delta data to all trades at matching times
            for key, trade in trades_data.items():
                time_key = f"{trade['date']} {trade['time']}"
                if time_key in delta_data:
                    trade.update(delta_data[time_key])
        
        # Add all merged trades to batch
        for trade in trades_data.values():
            self.validate_and_add_trade(trade, str(folder))
    
    def _create_trade_key(self, trade: Dict) -> str:
        """Create unique key for trade matching"""
        return f"{trade.get('date')}_{trade.get('time')}_{trade.get('symbol')}_{trade.get('strategy')}"
    
    def process_trades_file_enhanced(self, file_path: Path, folder_date: datetime):
        """Process trades file with full strike breakdown"""
        trades = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 2):
                # Extract all strike information
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
                    
                    # Strike details (up to 4 legs)
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
                    'format_year': folder_date.year  # FIX: Use actual folder date year
                }
                
                trades.append(trade)
        
        return trades
    
    def process_delta_file(self, file_path: Path, folder_date: datetime):
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

### 0.2 Create Symbol-Specific Data Splits

```python
def split_data_by_symbol(input_file: str, output_dir: str):
    """Split aggregated data into symbol-specific files"""
    
    df = pd.read_csv(input_file)
    symbols = df['symbol'].unique()
    
    os.makedirs(output_dir, exist_ok=True)
    
    symbol_stats = {}
    
    for symbol in symbols:
        symbol_df = df[df['symbol'] == symbol]
        
        # Save symbol-specific file
        output_file = os.path.join(output_dir, f'{symbol}_trades.csv')
        symbol_df.to_csv(output_file, index=False)
        
        # Calculate symbol-specific statistics
        symbol_stats[symbol] = {
            'total_trades': len(symbol_df),
            'strategies': symbol_df['strategy'].value_counts().to_dict(),
            'avg_profit': symbol_df['profit'].mean(),
            'profit_by_strategy': {}
        }
        
        # Profit statistics by strategy
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
    
    # Save statistics
    with open(os.path.join(output_dir, 'symbol_statistics.json'), 'w') as f:
        json.dump(symbol_stats, f, indent=2)
    
    return symbol_stats
```

### 0.3 Analyze Symbol-Specific Patterns

```python
class SymbolSpecificAnalyzer:
    """Analyze profit patterns by symbol"""
    
    def analyze_profit_scales(self, symbol_stats: Dict):
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
    
    def recommend_model_grouping(self, profit_groups: Dict):
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

## 📈 Phase 1: Feature Engineering with Complete Data [2-3 days]

### 1.1 Create Magic8-Specific Features

```python
class Magic8FeatureEngineer:
    """Extract features from Magic8's prediction logic"""
    
    def create_prediction_features(self, df):
        """Features based on Magic8's prediction indicators"""
        
        # Price target features
        df['distance_to_target1'] = (df['target1'] - df['price']) / df['price']
        df['distance_to_target2'] = (df['target2'] - df['price']) / df['price']
        df['targets_spread'] = abs(df['target1'] - df['target2']) / df['price']
        
        # Prediction alignment
        df['predicted_vs_price'] = (df['predicted_trades'] - df['price']) / df['price']
        df['predicted_vs_closing'] = (df['predicted_trades'] - df['closing']) / df['predicted_trades']
        
        # Delta features
        df['call_put_delta_spread'] = df['call_delta'] - df['put_delta']
        df['delta_skew'] = df['call_put_delta_spread'] / df['price']
        
        # Short/Long term bias
        df['short_term_bias'] = (df['short_term'] - df['price']) / df['price']
        df['long_term_bias'] = (df['long_term'] - df['price']) / df['price']
        df['term_structure'] = df['short_term'] - df['long_term']
        
        # Expected move utilization
        df['strike_width_ratio'] = (df['high'] - df['low']) / df['expected_move']
        
        return df
    
    def create_strike_features(self, df):
        """Features from strike structure"""
        
        # Butterfly-specific
        butterfly_mask = df['strategy'] == 'Butterfly'
        df.loc[butterfly_mask, 'butterfly_wing_width'] = (
            (df.loc[butterfly_mask, 'strike1'] - df.loc[butterfly_mask, 'strike2']).abs()
        )
        df.loc[butterfly_mask, 'butterfly_symmetry'] = (
            (df.loc[butterfly_mask, 'strike1'] - df.loc[butterfly_mask, 'strike2']) -
            (df.loc[butterfly_mask, 'strike2'] - df.loc[butterfly_mask, 'strike3'])
        ).abs() / df.loc[butterfly_mask, 'price']
        
        # Iron Condor/Sonar
        ic_mask = df['strategy'].isin(['Iron Condor', 'Sonar'])
        df.loc[ic_mask, 'condor_width'] = (
            df.loc[ic_mask, 'strike1'] - df.loc[ic_mask, 'strike4']
        ).abs()
        df.loc[ic_mask, 'condor_call_spread'] = (
            df.loc[ic_mask, 'strike1'] - df.loc[ic_mask, 'strike2']
        ).abs()
        df.loc[ic_mask, 'condor_put_spread'] = (
            df.loc[ic_mask, 'strike3'] - df.loc[ic_mask, 'strike4']
        ).abs()
        
        # Strike positioning relative to price
        for i in range(1, 5):
            col_name = f'strike{i}'
            if col_name in df.columns:
                df[f'strike{i}_moneyness'] = (df[col_name] - df['price']) / df['price']
        
        return df
    
    def create_market_microstructure_features(self, df):
        """Features from bid-ask spreads"""
        
        # Average bid-ask spread across legs
        spread_cols = []
        for i in range(1, 5):
            if f'bid{i}' in df.columns and f'ask{i}' in df.columns:
                df[f'spread{i}'] = df[f'ask{i}'] - df[f'bid{i}']
                df[f'spread_pct{i}'] = df[f'spread{i}'] / df[f'mid{i}'].replace(0, 1)
                spread_cols.append(f'spread_pct{i}')
        
        if spread_cols:
            df['avg_spread_pct'] = df[spread_cols].mean(axis=1)
            df['max_spread_pct'] = df[spread_cols].max(axis=1)
        
        # Liquidity indicator
        df['total_spread_cost'] = df[[f'spread{i}' for i in range(1, 5) if f'spread{i}' in df.columns]].sum(axis=1)
        
        return df
```

### 1.2 Create Symbol-Normalized Features

```python
class SymbolNormalizer:
    """Normalize features by symbol to handle scale differences"""
    
    def __init__(self):
        self.symbol_stats = {}
    
    def fit(self, df):
        """Calculate symbol-specific statistics"""
        
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol]
            
            self.symbol_stats[symbol] = {
                'price_mean': symbol_df['price'].mean(),
                'price_std': symbol_df['price'].std(),
                'profit_scale': {},
                'premium_scale': {}
            }
            
            # Calculate profit/premium scales by strategy
            for strategy in ['Butterfly', 'Iron Condor', 'Sonar', 'Vertical']:
                strategy_df = symbol_df[symbol_df['strategy'] == strategy]
                if len(strategy_df) > 0:
                    self.symbol_stats[symbol]['profit_scale'][strategy] = {
                        'mean': strategy_df['profit'].mean(),
                        'std': strategy_df['profit'].std(),
                        'p95': strategy_df['profit'].quantile(0.95),
                        'p05': strategy_df['profit'].quantile(0.05)
                    }
                    self.symbol_stats[symbol]['premium_scale'][strategy] = {
                        'mean': strategy_df['premium'].mean(),
                        'std': strategy_df['premium'].std()
                    }
    
    def transform(self, df):
        """Apply symbol-specific normalization"""
        
        df_normalized = df.copy()
        
        for symbol in df['symbol'].unique():
            if symbol not in self.symbol_stats:
                continue
                
            mask = df['symbol'] == symbol
            stats = self.symbol_stats[symbol]
            
            # Normalize prices
            df_normalized.loc[mask, 'price_normalized'] = (
                (df.loc[mask, 'price'] - stats['price_mean']) / stats['price_std']
            )
            
            # Normalize profit by strategy
            for strategy in ['Butterfly', 'Iron Condor', 'Sonar', 'Vertical']:
                strategy_mask = mask & (df['strategy'] == strategy)
                if strategy in stats['profit_scale'] and strategy_mask.any():
                    profit_stats = stats['profit_scale'][strategy]
                    df_normalized.loc[strategy_mask, 'profit_normalized'] = (
                        (df.loc[strategy_mask, 'profit'] - profit_stats['mean']) / 
                        (profit_stats['std'] + 1e-6)
                    )
                    
                    # Profit percentile within symbol-strategy
                    df_normalized.loc[strategy_mask, 'profit_percentile'] = (
                        df.loc[strategy_mask, 'profit'].rank(pct=True)
                    )
        
        return df_normalized
```

## 🧠 Phase 2: Symbol-Specific Model Architecture [3-4 days]

### 2.1 Model Strategy Decision Tree

```python
class SymbolModelStrategy:
    """Determine optimal model strategy per symbol"""
    
    def __init__(self, symbol_stats: Dict):
        self.symbol_stats = symbol_stats
        
    def determine_model_strategy(self) -> Dict:
        """Decide which symbols need separate models"""
        
        strategies = {
            'separate_models': {},
            'grouped_models': {},
            'scaling_factors': {}
        }
        
        # Analyze profit scale differences
        for symbol, stats in self.symbol_stats.items():
            butterfly_avg = stats['profit_by_strategy'].get('Butterfly', {}).get('avg_profit', 0)
            
            # Classify by scale
            if symbol in ['NDX', 'RUT']:  # Large indices
                strategies['separate_models'][symbol] = {
                    'reason': 'Large profit scale',
                    'scale_factor': butterfly_avg / 100  # Normalize to ~100 baseline
                }
            elif symbol in ['SPX', 'SPY']:  # Standard indices
                strategies['grouped_models'].setdefault('standard_indices', []).append(symbol)
            elif symbol in ['XSP', 'QQQ']:  # Small indices
                strategies['grouped_models'].setdefault('small_indices', []).append(symbol)
            else:  # Individual stocks
                strategies['grouped_models'].setdefault('stocks', []).append(symbol)
        
        return strategies
```

### 2.2 Multi-Model Architecture

```python
class MultiModelPredictor:
    """Manage multiple models for different symbols"""
    
    def __init__(self, model_strategy: Dict):
        self.model_strategy = model_strategy
        self.models = {}
        self.scalers = {}
        self.threshold_optimizers = {}
        
    def train_all_models(self, data_dir: str):
        """Train appropriate models for each symbol group"""
        
        # Train separate models
        for symbol, config in self.model_strategy['separate_models'].items():
            print(f"\nTraining separate model for {symbol}")
            
            # Load symbol-specific data
            symbol_data = pd.read_csv(f"{data_dir}/{symbol}_trades.csv")
            
            # Train model
            model = XGBoostSymbolSpecific(symbol=symbol, scale_factor=config['scale_factor'])
            model.train(symbol_data)
            
            self.models[symbol] = model
            
        # Train grouped models
        for group_name, symbols in self.model_strategy['grouped_models'].items():
            print(f"\nTraining grouped model for {group_name}: {symbols}")
            
            # Combine data from all symbols in group
            group_data = []
            for symbol in symbols:
                symbol_data = pd.read_csv(f"{data_dir}/{symbol}_trades.csv")
                group_data.append(symbol_data)
            
            combined_data = pd.concat(group_data, ignore_index=True)
            
            # Train model with symbol as feature
            model = XGBoostGrouped(group_name=group_name, symbols=symbols)
            model.train(combined_data)
            
            self.models[group_name] = model
    
    def predict(self, features: Dict, symbol: str, strategy: str) -> Dict:
        """Route prediction to appropriate model"""
        
        # Find appropriate model
        if symbol in self.models:
            # Use symbol-specific model
            model = self.models[symbol]
        else:
            # Find grouped model
            for group_name, group_symbols in self.model_strategy['grouped_models'].items():
                if symbol in group_symbols:
                    model = self.models[group_name]
                    break
            else:
                raise ValueError(f"No model found for symbol {symbol}")
        
        # Make prediction
        prediction = model.predict(features, strategy)
        
        # Apply symbol-specific threshold
        threshold = self.get_optimal_threshold(symbol, strategy)
        
        return {
            'win_probability': prediction['probability'],
            'threshold': threshold,
            'recommendation': 'TRADE' if prediction['probability'] >= threshold else 'SKIP',
            'model_used': model.name,
            'expected_profit': prediction.get('expected_profit', 0)
        }
```

### 2.3 Symbol-Specific XGBoost Model

```python
class XGBoostSymbolSpecific:
    """XGBoost model trained for a specific symbol"""
    
    def __init__(self, symbol: str, scale_factor: float = 1.0):
        self.symbol = symbol
        self.scale_factor = scale_factor
        self.name = f"XGBoost_{symbol}"
        
    def create_scaled_sample_weights(self, y_train, strategy_df):
        """Create weights scaled by symbol-specific profit ranges"""
        
        weights = np.ones(len(y_train))
        
        # Scale weights by normalized profit impact
        for idx, (target, row) in enumerate(zip(y_train, strategy_df.itertuples())):
            if row.strategy == 'Butterfly':
                # For NDX with $3800 profits, scale down to match other symbols
                base_weight = 10 if target == 1 else 1
                weights[idx] = base_weight / self.scale_factor
            elif row.strategy == 'Iron Condor':
                # IC has more consistent scaling across symbols
                weights[idx] = 5 if target == 0 else 1  # Weight losses more
            # ... other strategies
        
        return weights
```

## 🔧 Phase 3: Model Evaluation Fixes [1-2 days]

### 3.1 Fix Baseline with Complete Data

```python
def evaluate_profit_impact_corrected(model, test_data, symbol_stats):
    """Evaluate with correct baseline using all available features"""
    
    results = {}
    
    for symbol in test_data['symbol'].unique():
        symbol_data = test_data[test_data['symbol'] == symbol]
        symbol_results = {}
        
        for strategy in ['Butterfly', 'Iron Condor', 'Sonar', 'Vertical']:
            strategy_data = symbol_data[symbol_data['strategy'] == strategy]
            if len(strategy_data) == 0:
                continue
            
            # Get actual profit statistics for this symbol-strategy
            actual_stats = symbol_stats[symbol]['profit_by_strategy'][strategy]
            
            # Calculate baseline (trading all)
            baseline_profit = (
                actual_stats['win_rate'] * actual_stats['avg_win'] + 
                (1 - actual_stats['win_rate']) * actual_stats['avg_loss']
            ) * len(strategy_data)
            
            # Calculate model profit (selective trading)
            # ... prediction logic ...
            
            symbol_results[strategy] = {
                'baseline_profit': baseline_profit,
                'model_profit': model_profit,
                'improvement': model_profit - baseline_profit,
                'improvement_pct': (model_profit / baseline_profit - 1) * 100 if baseline_profit != 0 else 0
            }
        
        results[symbol] = symbol_results
    
    return results
```

## 📊 Phase 4: Updated Implementation Timeline [2-3 weeks total]

### Week 1: Data Processing & Feature Engineering
**Days 1-3: Rebuild Data Processing**
- [ ] Fix process_magic8_data_optimized_v2.py with all sheets
- [ ] Create symbol-specific data splits
- [ ] Analyze profit scale patterns
- [ ] Document data schema

**Days 4-5: Feature Engineering**
- [ ] Implement Magic8-specific features
- [ ] Create strike structure features
- [ ] Add market microstructure features
- [ ] Implement symbol normalization

### Week 2: Model Development
**Days 6-8: Multi-Model Architecture**
- [ ] Implement symbol model strategy
- [ ] Create XGBoost symbol-specific models
- [ ] Train grouped models
- [ ] Implement model routing

**Days 9-10: Evaluation & Optimization**
- [ ] Fix baseline calculations with actual data
- [ ] Optimize thresholds per symbol-strategy
- [ ] Test profit improvements
- [ ] Create performance dashboard

### Week 3: Integration & Testing
**Days 11-12: API Updates**
- [ ] Update prediction API for multi-model
- [ ] Add symbol-aware feature generation
- [ ] Implement model selection logic

**Days 13-14: Testing & Documentation**
- [ ] End-to-end testing
- [ ] Performance benchmarking
- [ ] Documentation updates
- [ ] Deployment preparation

## 🎯 Success Metrics (Updated)

### Per-Symbol Targets:

**Large Scale (NDX, RUT)**:
- Maintain current profit levels
- Improve selectivity to 70-80%
- Reduce maximum drawdowns

**Medium Scale (SPX, SPY)**:
- Increase profit per trade by 50%
- Optimize for consistency
- Target 65-75% trade selection

**Small Scale (XSP, QQQ, AAPL, TSLA)**:
- Focus on win rate improvement
- May need different strategy mix
- Consider discontinuing low-profit strategies

### Overall Targets:
1. **Data Completeness**: 100% capture of all sheet data
2. **Feature Coverage**: Use all Magic8 prediction indicators
3. **Model Accuracy**: Appropriate to symbol scale
4. **Profit Improvement**: 50%+ over corrected baseline

## 🔑 Critical Next Steps

1. **Immediately**: Fix data processing to capture all sheets
2. **Verify**: Check format_year and timestamp consistency
3. **Analyze**: Symbol-specific profit patterns
4. **Design**: Appropriate model architecture per symbol
5. **Implement**: Complete feature set from Magic8's logic

This comprehensive update addresses the fundamental data issues and provides a path to symbol-aware modeling that can handle the 76x profit scale differences across symbols.

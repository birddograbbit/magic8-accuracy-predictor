# Magic8 Predictor Revamp - Action Items

## 🚨 Immediate Priority: Fix Data Processing

### Task 1: Update process_magic8_data_optimized_v2.py
**Owner**: Data Engineering Team  
**Timeline**: 2-3 days  
**Critical Issues to Fix**:
1. **Merge all 3 sheets** (profit, trades, delta) by date/time/symbol/strategy
2. **Fix format_year bug** - use actual folder date year, not hardcoded
3. **Capture all columns**:
   - From trades: Strike1-4, Direction1-4, Type1-4, Target1, Target2, Bid1-4, Ask1-4
   - From delta: CallDelta, PutDelta, Predicted, ShortTerm, LongTerm
4. **Handle duplicate entries** - trades appear in both profit and trades sheets

### Task 2: Create Symbol Analysis Pipeline
**Owner**: Data Science Team  
**Timeline**: 1 day  
**Deliverables**:
1. Symbol-specific data files (SPX_trades.csv, NDX_trades.csv, etc.)
2. Profit scale analysis report showing 76x differences
3. Model grouping recommendations ✅

## 📊 Data Schema After Fix

### Complete Trade Record Schema:
```
# Identity
- date, time, timestamp, symbol, strategy

# Trade Details (from profit + trades sheets)
- price, premium, predicted, closed, expired
- risk, reward, ratio, profit, win
- source, expected_move, low, high
- target1, target2, predicted_trades, closing

# Strike Structure (from trades sheet)
- strike1, direction1, type1, bid1, ask1, mid1
- strike2, direction2, type2, bid2, ask2, mid2  
- strike3, direction3, type3, bid3, ask3, mid3
- strike4, direction4, type4, bid4, ask4, mid4

# Magic8 Predictions (from delta sheet)
- call_delta, put_delta, predicted_delta
- short_term, long_term, closing_delta

# Metadata
- trade_description, source_file, format_year
```

## 🎯 Success Criteria

### For Data Processing Fix:
 - [x] All 3 sheets merged correctly
 - [x] No duplicate trades
- [x] Format_year matches actual dates
 - [x] All 40+ columns captured
- [x] Data schema documented
 - [x] Symbol-specific files generated

### For Feature Engineering:
 - [x] Prediction alignment features implemented

### For Model Architecture:
 - [x] Separate models for NDX, RUT (large scale)
 - [x] Grouped model for SPX, SPY (medium scale)
 - [x] Grouped model for XSP, QQQ, stocks (small scale)
 - [ ] Profit improvements measured per symbol
 - [x] Threshold optimization per symbol-strategy
- [x] Symbol-specific models trained (demo NDX & XSP)
- [x] MultiModelPredictor utility implemented for routing

## 📈 Expected Impact

With complete data:
1. **+15-20% accuracy** from Magic8 prediction features
2. **Proper profit optimization** with symbol-aware models
3. **Better risk management** using strike structure
4. **Accurate evaluation** with fixed baselines

## 🔗 References

- **Detailed Plan**: `magic8-predictor-revamp-plan.md`
- **Quick Summary**: `REVAMP_SUMMARY.md`
- **Data Analysis**: `magic8_data_analysis.py`
- **Symbol Scales**: `data/analysis/symbol_profit_scales.png`

## 📅 Updated Timeline

**Week 1**: Fix data processing + feature engineering  
**Week 2**: Multi-model development + evaluation fixes  
**Week 3**: Integration, testing, deployment

**Total**: 2-3 weeks (was 1 week before discovering issues)

---

**Remember**: Nothing else can proceed until data processing is fixed!

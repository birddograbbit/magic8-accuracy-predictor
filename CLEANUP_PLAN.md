# Magic8 Accuracy Predictor - Cleanup Plan

## Overview
This document tracks the codebase organization and cleanup requirements as of July 1, 2025, after successful Phase 1 completion.

## Current Status (July 1, 2025)

### ✅ Phase 1 Complete - Major Success!
1. **Data Processing**: Optimized processor handles 1.5M trades in 0.6 minutes
2. **Feature Engineering**: Reduced from 3+ hours to 2-5 minutes with merge_asof
3. **Model Training**: XGBoost achieved 88.21% test accuracy (target was >60%)
4. **All Strategies Working**: Including Sonar (was missing before)
5. **Production Ready**: Clean pipeline from raw data to predictions

## File Organization

### 🔒 CORE FILES (Keep Permanently)

#### Production Code
```
# Data Processing
process_magic8_data_optimized_v2.py     # ✅ The ONLY processor to use
run_data_processing_v2.sh               # ✅ Runner script

# ML Pipeline  
src/phase1_data_preparation.py          # ✅ Feature engineering (optimized)
src/models/xgboost_baseline.py          # ✅ XGBoost model
src/evaluation/                         # ✅ Evaluation utilities

# Configuration
requirements.txt                        # ✅ Python dependencies
config/                                # ✅ Configuration files
download_phase1_data.sh                # ✅ IBKR data downloader
```

#### Essential Documentation
```
README.md                              # ✅ Updated with results
PROJECT_KNOWLEDGE_BASE.md              # ✅ Comprehensive reference
PROJECT_SUMMARY_NEXT_CHAT.md          # ✅ Session handoff
IMPLEMENTATION_PLAN.md                 # ✅ Overall roadmap
PHASE1_PLAN.md                        # ✅ Phase 1 details
PHASE1_SUMMARY.md                     # ✅ Phase 1 results
REALTIME_INTEGRATION_GUIDE.md         # ✅ Production guide
CLEANUP_PLAN.md                      # ✅ This file
```

#### Trained Models & Results
```
models/phase1/                        # ✅ Trained XGBoost model
logs/xgboost_baseline_*.log          # ✅ Training logs
plots/                               # ✅ Feature importance plots
data/phase1_processed/               # ✅ Processed features
```

### 📦 ARCHIVE (Move to archive/ folder)

#### Old Data Processors
```
process_magic8_data_fixed.py         # ❌ Slow, outdated
process_magic8_data_fixed_v2.py      # ❌ Slow, outdated
process_magic8_data_optimized.py    # ❌ Has datetime issues
process_magic8_complete.py           # ❌ Old version
process_magic8_complete_fixed.py     # ❌ Old version
normalize_data.py                    # ❌ Original slow processor
normalize_data_large.py              # ❌ Memory inefficient
rebuild_data.py                      # ❌ Temporary fix
fix_profit_calculations.py           # ❌ One-time fix
fix_data_preparation.py              # ❌ One-time fix
```

#### Old Scripts & Tests
```
analyze_data.py                      # ❌ Basic analysis, outdated
analyze_data_stdlib.py               # ❌ Duplicate functionality
analyze_existing_data.py             # ❌ Superseded
analyze_profit_issue.py              # ❌ Issue resolved
analyze_source_profits.py            # ❌ Issue resolved
check_duplicate_headers.py           # ❌ One-time check
check_json_reports.py                # ❌ Temporary diagnostic
check_optimized_data.py              # ❌ Can use verify_data.py
check_profit_units.py                # ❌ Issue resolved
check_strategies.py                  # ❌ Issue resolved
deep_diagnose_csv.py                 # ❌ Diagnostic complete
diagnose_csv_structure.py            # ❌ Diagnostic complete
diagnose_failure.py                  # ❌ Issue resolved
diagnose_features.py                 # ❌ Diagnostic complete
diagnose_phase1_model.py             # ❌ Model working now
fix_profit_output.txt                # ❌ Temporary output
inspect_profit_columns.py            # ❌ Issue resolved
scan_timestamp_issues.py             # ❌ Issue resolved
stop_stuck_processing.sh             # ❌ No longer needed
test_processing_fix.py               # ❌ Fix verified
test_xgboost_fix.sh                  # ❌ Fix verified
phase1_5_action_plan.py              # ❌ Outdated plan
quick_start.py                       # ❌ Outdated
replace_normalized_data.sh           # ❌ One-time script
```

#### Obsolete Documentation
```
DATA_PROCESSING_FIX.md               # ❌ Issue resolved
DATA_PROCESSING_FIX_README.md        # ❌ Duplicate
FIX_SUMMARY.md                       # ❌ Issues resolved
TIMESTAMP_ISSUE_FIX.md               # ❌ Issue resolved
PHASE1_ISSUES_AND_SOLUTIONS.md       # ❌ Merged into main docs
MAGIC8_DATA_DISCOVERIES_SUMMARY.md   # ❌ Merged into knowledge base
```

#### Old Data Directories
```
data/processed/                      # ❌ Old, incomplete
data/processed_fixed/                # ❌ Old version
data/processed_fixed_v2/             # ❌ Old version  
data/processed_optimized/            # ❌ Has datetime issues
data/phase1_processed_backup*/       # ❌ Old backups
```

### 🔍 EVALUATION NEEDED (Review before archiving)

```
compare_data_sources.py              # ? Might be useful for validation
analyze_feature_predictiveness.py    # ? Useful for Phase 2
analyze_temporal_wins.py             # ? Could inform Phase 2
diagnose_class_imbalance.py          # ? Might need for monitoring
feature_predictiveness_analysis.png  # ? Keep with results
feature_predictiveness_results.csv   # ? Keep with results
test_strategy_parsing.py             # ? Good for validation
test_data_loading.py                 # ? Good for validation
verify_data.py                       # ? Keep for validation
predict_trades_example.py            # ? Template for Phase 2
setup_directories.py                 # ? Might need for setup
```

## Cleanup Commands

### Step 1: Create Archive Structure
```bash
mkdir -p archive/old_processors
mkdir -p archive/old_scripts  
mkdir -p archive/old_docs
mkdir -p archive/old_data
```

### Step 2: Move Old Processors
```bash
mv process_magic8_data_fixed*.py archive/old_processors/
mv process_magic8_complete*.py archive/old_processors/
mv normalize_data*.py archive/old_processors/
mv process_magic8_data_optimized.py archive/old_processors/
mv rebuild_data.py archive/old_processors/
mv fix_*.py archive/old_processors/
```

### Step 3: Move Old Scripts
```bash
mv analyze_data*.py archive/old_scripts/
mv analyze_profit*.py archive/old_scripts/
mv analyze_source*.py archive/old_scripts/
mv check_*.py archive/old_scripts/
mv deep_diagnose*.py archive/old_scripts/
mv diagnose_*.py archive/old_scripts/
mv inspect_*.py archive/old_scripts/
mv scan_*.py archive/old_scripts/
mv test_processing_fix.py archive/old_scripts/
mv test_xgboost_fix.sh archive/old_scripts/
mv phase1_5_action_plan.py archive/old_scripts/
mv quick_start.py archive/old_scripts/
mv stop_stuck_processing.sh archive/old_scripts/
mv replace_normalized_data.sh archive/old_scripts/
mv fix_profit_output.txt archive/old_scripts/
```

### Step 4: Move Old Documentation
```bash
mv DATA_PROCESSING_FIX*.md archive/old_docs/
mv FIX_SUMMARY.md archive/old_docs/
mv TIMESTAMP_ISSUE_FIX.md archive/old_docs/
mv PHASE1_ISSUES_AND_SOLUTIONS.md archive/old_docs/
mv MAGIC8_DATA_DISCOVERIES_SUMMARY.md archive/old_docs/
```

### Step 5: Archive Old Data (Optional - these are large)
```bash
# Only if you need the disk space
mv data/processed archive/old_data/
mv data/processed_fixed* archive/old_data/
mv data/processed_optimized archive/old_data/
mv data/phase1_processed_backup* archive/old_data/
```

### Step 6: Update .gitignore
```bash
echo "archive/" >> .gitignore
```

### Step 7: Remove from Git Tracking
```bash
# Remove old files from git
git rm --cached process_magic8_data_fixed*.py
git rm --cached normalize_data*.py
git rm --cached DATA_PROCESSING_FIX*.md
# ... etc for other files

# Commit the cleanup
git add .
git commit -m "Archive old files after Phase 1 completion"
```

## Final Clean Structure

```
magic8-accuracy-predictor/
├── src/
│   ├── phase1_data_preparation.py      # Feature engineering
│   ├── models/
│   │   └── xgboost_baseline.py        # XGBoost model
│   └── evaluation/                     # Analysis tools
├── data/
│   ├── source/                         # Original CSVs
│   ├── normalized/                     # Processed trades
│   ├── ibkr/                          # Market data
│   ├── processed_optimized_v2/        # Latest processing
│   └── phase1_processed/              # ML features
├── models/
│   └── phase1/                        # Trained models
├── logs/                              # Training logs
├── plots/                             # Visualizations
├── config/                            # Configuration
├── docs/                              # Additional docs
├── notebooks/                         # Jupyter notebooks
├── process_magic8_data_optimized_v2.py  # Data processor
├── run_data_processing_v2.sh            # Runner script
├── download_phase1_data.sh              # IBKR downloader
├── requirements.txt                     # Dependencies
├── README.md                           # Main documentation
└── [other core documentation files]
```

## Important Notes

1. **Keep the archive/ folder locally** but don't commit to git
2. **Before deleting anything**, verify the production pipeline works
3. **Keep validation scripts** (test_*.py, verify_*.py) for quality checks
4. **Document any custom changes** before archiving

## Next Steps After Cleanup

1. **Test the clean pipeline end-to-end**
2. **Create Phase 2 plan** for real-time predictions
3. **Set up CI/CD** for automated testing
4. **Document API** for prediction service

---

**Last Updated**: July 1, 2025  
**Phase 1 Status**: ✅ Complete - Ready for cleanup  
**Recommendation**: Archive old files but keep locally for reference

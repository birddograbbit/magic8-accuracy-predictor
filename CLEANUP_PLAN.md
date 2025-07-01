# Magic8 Accuracy Predictor - Codebase Cleanup Plan

## Overview
This document tracks the organization and cleanup status of the project codebase as of July 1, 2025.

## Current Status Update (July 1, 2025)

### Major Progress Made ✅
1. **Data Processing Fixed**: Replaced slow processor with optimized version that processes 1.5M trades in 0.6 minutes
2. **All Strategies Found**: Including Sonar (was missing due to wrong column parsing)
3. **Column Mapping Fixed**: Created `phase1_data_preparation_fixed.py` to handle actual CSV column names

### Cleanup Summary
All deprecated processors and outdated documentation have been removed. The
`archive/` directory contains any historical scripts kept for reference.

## File Categories (UPDATED)

### ✅ Core Production Files (Keep Permanently)

#### Main Source Code - THE CORRECT VERSIONS
- `process_magic8_data_optimized_v2.py` - **USE THIS** for data processing (batch processing, 0.6 min)
- `src/phase1_data_preparation_fixed.py` - **USE THIS** for Phase 1 ML pipeline (handles column mapping)
- `src/models/xgboost_baseline.py` - XGBoost model implementation

#### Critical Shell Scripts
- `run_data_processing_v2.sh` - Runs the optimized v2 processor
- `download_phase1_data.sh` - IBKR data download helper

### 🗑️ Deprecated Files
No deprecated processors remain in the repository. Historical scripts that were
previously listed have been moved to `archive/` or removed entirely.

### 📊 Analysis & Diagnostic Scripts (Keep for Now)
- `check_optimized_data.py` - Useful for verifying data
- `compare_data_sources.py` - Useful for checking differences
- `diagnose_class_imbalance.py` - May need for Phase 2
- `analyze_feature_predictiveness.py` - Useful for feature analysis

### 📝 Documentation Updates Needed

#### Files to Update
1. `PROJECT_KNOWLEDGE_BASE.md` - Reflect Phase 1 completion
2. `PROJECT_SUMMARY_NEXT_CHAT.md` - Summarize final metrics
3. `PHASE1_SUMMARY.md` - Document results
4. `README.md` - Include final accuracy numbers

#### Files to Remove/Archive
Legacy troubleshooting notes have been archived under `archive/`.

### 📁 Data Directory Cleanup

#### Keep These
```
data/
├── source/                     # Original Magic8 CSV files
├── processed_optimized_v2/     # CURRENT processed data (1.5M trades)
├── normalized/                 # Where phase1 expects data
├── ibkr/                      # IBKR market data
└── phase1_processed/          # ML-ready features (after phase1 runs)
```

#### Remove These
```
data/
├── processed/                 # Old, incomplete
├── processed_fixed/           # Old version
├── processed_fixed_v2/        # Old version
├── processed_optimized/       # Has datetime issues
└── phase1_processed_backup_*/ # Old backups
```

## Immediate Cleanup Actions (Do Now)

### 1. Consolidate to Correct Versions
```bash
# Use the fixed phase1 script
cp src/phase1_data_preparation_fixed.py src/phase1_data_preparation.py

# Remove old versions
rm src/phase1_data_preparation_original.py
rm src/phase1_data_preparation_v2.py

# Archive old processors
mkdir -p archive/old_processors
mv process_magic8_data_fixed*.py archive/old_processors/
mv normalize_data*.py archive/old_processors/
```

### 2. Clean Data Directories
```bash
# Archive old processed data
mkdir -p archive/old_data
mv data/processed archive/old_data/
mv data/processed_fixed* archive/old_data/
mv data/processed_optimized archive/old_data/  # Keep only v2

# Ensure normalized data is current
cp data/processed_optimized_v2/magic8_trades_complete.csv data/normalized/normalized_aggregated.csv
```

### 3. Update Documentation
- Remove all obsolete .md files listed above
- Update remaining docs with current status
- Create single SOURCE_OF_TRUTH.md if needed

## Git Cleanup Commands

```bash
# Add archive to gitignore
echo "archive/" >> .gitignore

# Remove tracking of old files
git rm process_magic8_data_fixed*.py
git rm normalize_data*.py
git rm src/phase1_data_preparation_v2.py
git rm src/phase1_data_preparation_original.py

# Remove obsolete docs
git rm DATA_PROCESSING_FIX*.md
git rm FIX_SUMMARY.md
git rm TIMESTAMP_ISSUE_FIX.md
```

## Final Clean Structure

```
magic8-accuracy-predictor/
├── src/
│   ├── phase1_data_preparation.py  # Fixed version only
│   └── models/
│       └── xgboost_baseline.py
├── data/
│   ├── source/                     # Raw CSV files
│   ├── normalized/                 # Current processed data
│   ├── ibkr/                      # Market data
│   └── phase1_processed/          # ML features
├── process_magic8_data_optimized_v2.py  # The ONE processor
├── run_data_processing_v2.sh            # The ONE runner
├── download_phase1_data.sh              # IBKR helper
├── README.md                            # Updated instructions
├── PROJECT_KNOWLEDGE_BASE.md            # Comprehensive status
├── IMPLEMENTATION_PLAN.md               # Overall plan
├── PHASE1_PLAN.md                       # Phase 1 details
└── requirements.txt
```

## Next Steps After Cleanup

1. **Run Phase 1 with clean codebase**:
   ```bash
   python src/phase1_data_preparation.py
   python src/models/xgboost_baseline.py
   ```

2. **Continue to Phase 2 planning** based on results

3. **Archive this cleanup plan** once complete

---

**Last Updated**: July 1, 2025  
**Status**: Cleanup complete  
**Priority**: LOW - Completed

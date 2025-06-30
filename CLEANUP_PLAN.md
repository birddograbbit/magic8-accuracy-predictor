# Magic8 Accuracy Predictor - Codebase Cleanup Plan

## Overview
This document tracks the organization and cleanup status of the project codebase as of June 30, 2025.

## Current Status Update (June 30, 2025)

### Major Progress Made ✅
1. **Data Processing Fixed**: Replaced slow processor with optimized version that processes 1.5M trades in 0.6 minutes
2. **All Strategies Found**: Including Sonar (was missing due to wrong column parsing)
3. **Column Mapping Fixed**: Created `phase1_data_preparation_fixed.py` to handle actual CSV column names

### Critical File Confusion Issues 🚨
- Multiple versions of phase1_data_preparation.py (original, v2, fixed)
- Multiple data processing scripts (fixed, fixed_v2, optimized, optimized_v2)
- Multiple data directories with different processing results
- Inconsistent column names between processed data and expected format

## File Categories (UPDATED)

### ✅ Core Production Files (Keep Permanently)

#### Main Source Code - THE CORRECT VERSIONS
- `process_magic8_data_optimized_v2.py` - **USE THIS** for data processing (batch processing, 0.6 min)
- `src/phase1_data_preparation_fixed.py` - **USE THIS** for Phase 1 ML pipeline (handles column mapping)
- `src/models/xgboost_baseline.py` - XGBoost model implementation

#### Critical Shell Scripts
- `run_data_processing_v2.sh` - Runs the optimized v2 processor
- `download_phase1_data.sh` - IBKR data download helper

### 🗑️ DEPRECATED Files (Remove After Cleanup)

#### Old Data Processors (DO NOT USE)
- `process_magic8_data_fixed.py` - Old version, slow
- `process_magic8_data_fixed_v2.py` - Old version, slow
- `process_magic8_data_optimized.py` - Has datetime column issues
- `normalize_data.py` - Original slow processor
- `normalize_data_large.py` - Memory inefficient

#### Old Phase 1 Scripts (DO NOT USE)
- `src/phase1_data_preparation.py` - Expects wrong column names
- `src/phase1_data_preparation_v2.py` - Outdated
- `src/phase1_data_preparation_original.py` - Backup of wrong version

#### Redundant Scripts
- `run_data_processing.sh` - Uses old processor
- `run_data_processing_optimized.sh` - Uses non-v2 version
- `fix_csv_parsing.py` - Temporary fix, not needed
- `fix_csv_v2.py` - Temporary fix, not needed

### 📊 Analysis & Diagnostic Scripts (Keep for Now)
- `check_optimized_data.py` - Useful for verifying data
- `compare_data_sources.py` - Useful for checking differences
- `diagnose_class_imbalance.py` - May need for Phase 2
- `analyze_feature_predictiveness.py` - Useful for feature analysis

### 📝 Documentation Updates Needed

#### Files to Update
1. `PROJECT_KNOWLEDGE_BASE.md` - Update with June 30 progress
2. `PROJECT_SUMMARY_NEXT_CHAT.md` - Update with current status
3. `PHASE1_SUMMARY.md` - Mark data processing as complete
4. `README.md` - Update quick start instructions

#### Files to Remove/Archive
- `DATA_PROCESSING_FIX.md` - Obsolete after fix
- `DATA_PROCESSING_FIX_README.md` - Duplicate
- `FIX_SUMMARY.md` - Obsolete
- `TIMESTAMP_ISSUE_FIX.md` - Issue resolved
- `PHASE1_ISSUES_AND_SOLUTIONS.md` - Merged into main docs
- `MAGIC8_DATA_DISCOVERIES_SUMMARY.md` - Merged into knowledge base

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

**Last Updated**: June 30, 2025, 1:45 PM  
**Status**: URGENT - Multiple version confusion causing errors  
**Priority**: HIGH - Clean before proceeding
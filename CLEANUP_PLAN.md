# Magic8 Accuracy Predictor - Codebase Cleanup Plan

## Overview
This document tracks the organization and cleanup status of the project codebase as of June 29, 2025.

## File Categories

### ✅ Core Production Files (Keep Permanently)

#### Main Source Code
- `src/phase1_data_preparation.py` - Base data preparation pipeline
- `src/phase1_data_preparation_v2.py` - Improved version focusing on market conditions
- `src/models/xgboost_baseline.py` - XGBoost model implementation
- `src/evaluation/` (to be created) - Model evaluation scripts

#### Configuration
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules
- `config.yaml` (if exists) - Project configuration

#### Data Download Scripts
- `ibkr_downloader.py` - IBKR data download utility
- `download_phase1_data.sh` - Helper script for downloading all symbols

### 📊 Analysis & Diagnostic Scripts (Keep During Development)

These are useful for debugging and analysis but can be archived after Phase 1.5:

- `analyze_feature_predictiveness.py` - Feature correlation analysis
- `inspect_profit_columns.py` - Data exploration for profit columns
- `test_data_loading.py` - Data loading verification
- `diagnose_features.py` - Feature engineering diagnostics
- `diagnose_class_imbalance.py` - Class distribution analysis
- `rebuild_data.py` - Data pipeline rebuild utility
- `verify_data.py` - Data verification script

### 📝 Documentation (Keep & Update)

#### Primary Documentation
- `README.md` - Main project documentation
- `IMPLEMENTATION_PLAN.md` - Overall project plan
- `PHASE1_PLAN.md` - Phase 1 specific plan
- `PROJECT_KNOWLEDGE_BASE.md` - Comprehensive project knowledge
- `PROJECT_SUMMARY_NEXT_CHAT.md` - Current status for continuity

#### Status & Summary Documents
- `IMPLEMENTATION_SUMMARY.md` - Implementation progress
- `PHASE1_SUMMARY.md` - Phase 1 completion summary
- `FIX_SUMMARY.md` - Bug fixes and solutions
- `phase1_5_action_plan.py` - Current action plan (convert to .md)

### 🗑️ Temporary Files (Can Remove After Phase 1.5)

- `sample_profit_data.csv` - Sample data for debugging
- `feature_predictiveness_results.csv` - Analysis output
- `feature_predictiveness_analysis.png` - Visualization output
- Any `.pyc` or `__pycache__` files
- Jupyter notebook checkpoints

### 📁 Directory Structure Cleanup

Current structure that should be maintained:
```
magic8-accuracy-predictor/
├── data/
│   ├── normalized/              # Original trade data
│   ├── ibkr/                   # IBKR historical data
│   ├── phase1_processed/       # Processed features
│   └── phase1_processed_backup_*/ # Backups (can archive)
├── src/
│   ├── models/                 # Model implementations
│   ├── evaluation/             # Evaluation scripts (create)
│   └── utils/                  # Utility functions (create)
├── notebooks/                  # Jupyter notebooks (create)
├── models/                     # Saved models
│   └── phase1/                # Phase 1 models
├── logs/                      # Log files (auto-generated)
└── docs/                      # Move some .md files here
```

## Cleanup Actions

### Immediate Actions (Do Now)
1. ✅ Fix `day_of_week` derivation in scripts
2. ❌ Create missing directories: `src/evaluation/`, `src/utils/`, `notebooks/`
3. ❌ Move utility scripts to `src/utils/`
4. ❌ Convert `phase1_5_action_plan.py` to `PHASE1_5_PLAN.md`

### Phase 1.5 Completion Actions
1. Archive diagnostic scripts to `scripts/diagnostics/`
2. Move documentation to `docs/` folder
3. Create proper test suite in `tests/`
4. Remove temporary output files

### Before Phase 2 Actions
1. Archive Phase 1 specific scripts
2. Clean up data backups (keep only latest)
3. Document lessons learned
4. Update all documentation

## Git Cleanup

### Files to Add to .gitignore
```
# Temporary outputs
*.csv
*.png
*.jpg

# Python
__pycache__/
*.pyc
.pytest_cache/

# Jupyter
.ipynb_checkpoints/

# Logs
logs/
*.log

# Data backups
data/phase1_processed_backup_*/

# Model outputs
models/*/results.json
models/*/feature_importance.png
```

## Script Consolidation Plan

### Combine Similar Scripts
1. Merge all diagnostic scripts into `src/utils/diagnostics.py`
2. Create `src/utils/data_validation.py` from test scripts
3. Consolidate feature analysis into `src/evaluation/feature_analysis.py`

### Create New Organized Modules
- `src/utils/plotting.py` - All visualization functions
- `src/utils/metrics.py` - Performance metrics calculations
- `src/config/settings.py` - Centralized configuration

## Timeline

### Week 1 (Current)
- ✅ Fix immediate issues (day_of_week)
- ❌ Create missing directories
- ❌ Start moving scripts to proper locations

### Week 2
- Archive diagnostic scripts after use
- Consolidate utility functions
- Update documentation

### Week 3
- Final cleanup before Phase 2
- Create comprehensive test suite
- Archive Phase 1 artifacts

## Maintenance Notes

### Keep Updated
- This cleanup plan
- PROJECT_SUMMARY_NEXT_CHAT.md after each session
- Requirements.txt when adding packages

### Regular Cleanup
- Remove old log files weekly
- Clean data backups monthly
- Update documentation after major changes

---

**Last Updated**: June 29, 2025  
**Status**: In Progress  
**Priority**: Medium (functionality first, cleanup second)

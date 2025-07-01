# QUICK_START_GUIDE.md - Get Your First Prediction in 5 Minutes! 🚀

## Overview

This guide will help you get your first real-time Magic8 order prediction running quickly, following the "ship-fast" principle.

## 🆕 Just Trained Your Model? Run This First!

If you just completed Phase 1 training (like the output shows), you need to convert your model:

```bash
# Pull latest changes and fix everything
git pull origin main
python fix_and_run.py
```

This script will:
1. Convert your trained model to the right format
2. Set up test configuration (no external dependencies)
3. Run your first prediction automatically

## Manual Steps (if fix_and_run.py doesn't work)

### Step 1: Convert Your Trained Model

```bash
# The training created models/phase1/xgboost_baseline.json
# We need to convert it to .pkl format
python prepare_model_for_predictor.py
```

### Step 2: Run Quick Start

```bash
python quick_start.py
```

## Complete Flow After Training

You've already done:
- ✅ `python src/phase1_data_preparation.py` (Data prepared)
- ✅ `python src/models/xgboost_baseline.py` (Model trained - 88.21% accuracy!)

Now do:
1. **Convert Model**: `python prepare_model_for_predictor.py`
2. **Test Prediction**: `python quick_start.py`
3. **Monitor**: `python monitor_predictions.py` (in another terminal)

## Using Different Data Sources

### Option 1: Mock Data (Default - No Dependencies)
```bash
# Already configured in config/config.test.yaml
# Just run:
python quick_start.py
```

### Option 2: Magic8-Companion (Real Data)
```bash
# Set up Magic8-Companion API
python setup_companion_api.py

# Configuration now defaults to the companion provider
```

### Option 3: Direct IBKR (Standalone)
```bash
# Update config/config.yaml:
# Change primary: "mock" to primary: "standalone"
# Make sure IBKR Gateway is running on port 7498
```

## What Each Script Does

### 🛠️ `prepare_model_for_predictor.py`
- Converts `models/phase1/xgboost_baseline.json` to `models/phase1/xgboost_model.pkl`
- Creates a wrapper that the real-time predictor can use
- **Run this after training!**

### 🎯 `quick_start.py`
- Checks prerequisites
- Tests data providers
- Makes first prediction
- Shows next steps

### 🔧 `fix_and_run.py`
- One-click solution
- Runs all the fixes automatically
- Gets you to first prediction fastest

### 📊 `monitor_predictions.py`
- Real-time dashboard
- Live statistics
- Performance tracking

## Troubleshooting

### "Model not found at models/xgboost_phase1_model.pkl"
```bash
# You need to convert your trained model:
python prepare_model_for_predictor.py
```

### "Failed to connect to Magic8-Companion"
```bash
# Use mock provider for testing:
cp config/config.test.yaml config/config.yaml
python quick_start.py
```

### "No module named 'aiohttp'"
```bash
# Install dependencies:
pip install -r requirements-minimal.txt
```

## Your Current Status

Based on your output:
- ✅ Data preparation complete (1.5M records processed)
- ✅ Model trained successfully (88.21% test accuracy!)
- ✅ Performance by strategy:
  - Butterfly: 75.98%
  - Iron Condor: 96.24%
  - Sonar: 88.70%
  - Vertical: 91.92%
- ❌ Model needs conversion for real-time predictor
- ❌ Dependencies might need updating

## Next Steps

1. **Get First Prediction**:
   ```bash
   python fix_and_run.py
   ```

2. **Set Up Monitoring**:
   ```bash
   python monitor_predictions.py
   ```

3. **Integrate with DiscordTrading**:
   ```bash
   python integrate_discord_trading.py
   ```

## Success Checklist

- [ ] Model converted to .pkl format
- [ ] First prediction successful
- [ ] Monitoring dashboard running
- [ ] DiscordTrading integration complete

---

**Remember**: Ship fast, enhance later! Start with mock data, then add real connections. 🚀

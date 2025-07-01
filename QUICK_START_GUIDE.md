# QUICK_START_GUIDE.md - Get Your First Prediction in 5 Minutes! 🚀

## Overview

This guide will help you get your first real-time Magic8 order prediction running quickly, following the "ship-fast" principle.

## Step 1: Check Your Setup (1 minute)

```bash
# Clone the repo if you haven't already
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor

# Install dependencies
pip install -r requirements.txt

# Run the quick start script
python quick_start.py
```

This script will:
- ✅ Check if you have a trained model
- ✅ Test data provider connections
- ✅ Make a sample prediction (even with mock data!)
- ✅ Show you exactly what to do next

## Step 2: Get Your First Real Prediction (2 minutes)

### Option A: Quick Test (No Model Training Required)

If you don't have a trained model yet, the quick_start script creates a mock model for testing:

```bash
# The script already created a mock model for you!
# Just run the test predictor:
python test_real_time_predictor.py
```

### Option B: With Real Model (If You Have Training Data)

```bash
# If you have the IBKR data and normalized trades:
python src/phase1_data_preparation.py
python src/models/xgboost_baseline.py
```

## Step 3: Set Up Data Source (1 minute)

### Easiest: Use Magic8-Companion

```bash
# Set up Magic8-Companion API automatically
python setup_companion_api.py

# This will:
# - Find your Magic8-Companion installation
# - Create API endpoints
# - Show you how to start it
```

### Alternative: Use Mock Data Provider

Edit `config/config.yaml`:
```yaml
data_source:
  primary: "standalone"  # Works without external dependencies
```

## Step 4: Integrate with DiscordTrading (1 minute)

```bash
# Automatic integration!
python integrate_discord_trading.py

# This will:
# - Find your DiscordTrading installation
# - Copy all necessary files
# - Update the configuration
# - Show you the integration code
```

## Step 5: Monitor Your Predictions

```bash
# Start the real-time monitoring dashboard
python monitor_predictions.py

# You'll see:
# - Live prediction statistics
# - Approval rates by symbol/strategy
# - Recent predictions feed
# - Performance metrics
```

## Complete Example: From Zero to Prediction

```bash
# Terminal 1: Get everything set up
git clone https://github.com/birddograbbit/magic8-accuracy-predictor.git
cd magic8-accuracy-predictor
pip install -r requirements.txt
python quick_start.py

# Terminal 2: Start Magic8-Companion (if using)
python setup_companion_api.py
# Follow instructions to start companion with API

# Terminal 3: Monitor predictions
python monitor_predictions.py

# Terminal 4: Run DiscordTrading with ML predictions
python integrate_discord_trading.py
# Follow instructions to restart DiscordTrading
```

## What Each Script Does

### 🎯 `quick_start.py`
- Checks prerequisites
- Creates mock model if needed
- Tests data providers
- Makes first prediction
- Shows next steps

### 🔧 `setup_companion_api.py`
- Configures Magic8-Companion API
- Creates start scripts
- Tests API endpoints
- Shows manual setup if needed

### 🔌 `integrate_discord_trading.py`
- Finds DiscordTrading automatically
- Copies integration files
- Updates configuration
- Shows integration code

### 📊 `monitor_predictions.py`
- Real-time dashboard
- Live statistics
- Performance tracking
- Recent predictions feed

## Troubleshooting

### "No trained model found"
```bash
# Use mock model for testing:
python quick_start.py
# Answer 'y' when asked about mock model
```

### "Failed to connect to Magic8-Companion"
```bash
# Make sure companion is running with API:
python setup_companion_api.py
cd /path/to/Magic8-Companion
./start_with_api.sh
```

### "DiscordTrading not found"
```bash
# Specify path manually:
python integrate_discord_trading.py --discord-path /path/to/DiscordTrading
```

## Next Steps

1. **Train Real Model**: Follow Phase 1 instructions in PROJECT_KNOWLEDGE_BASE.md
2. **Configure Thresholds**: Adjust `min_win_probability` in config
3. **Set Up Production**: Use Redis for better performance
4. **Add Monitoring**: Set up alerts for failed predictions

## Need Help?

- Check `docs/REAL_TIME_INTEGRATION_PLAN.md` for detailed documentation
- Run any script with `--help` for options
- Review logs in `logs/` directory
- Monitor predictions with `monitor_predictions.py`

## Success Metrics

You'll know it's working when:
- ✅ `quick_start.py` shows successful prediction
- ✅ `monitor_predictions.py` shows live stats
- ✅ DiscordTrading logs show "ML prediction approved/rejected"
- ✅ Orders are being filtered by win probability

---

**Remember**: Ship fast, enhance later! Get it working first, optimize second. 🚀

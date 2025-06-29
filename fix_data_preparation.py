#!/usr/bin/env python
"""
Script to fix the phase1 data preparation to drop original categorical columns
after one-hot encoding. This is the permanent fix for the issue.
"""

import shutil
import os
from datetime import datetime

print("Backing up and fixing phase1_data_preparation.py...")
print("=" * 50)

# Create backup
backup_dir = "backups"
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"{backup_dir}/phase1_data_preparation_{timestamp}.py"

shutil.copy("src/phase1_data_preparation.py", backup_file)
print(f"✓ Created backup: {backup_file}")

# Read the original file
with open("src/phase1_data_preparation.py", "r") as f:
    content = f.read()

# Fix 1: Update add_vix_features to drop original vix_regime
fix1 = """            # One-hot encode VIX regime
            regime_dummies = pd.get_dummies(self.df['vix_regime'], prefix='vix_regime')
            self.df = pd.concat([self.df, regime_dummies], axis=1)"""

fix1_replacement = """            # One-hot encode VIX regime
            regime_dummies = pd.get_dummies(self.df['vix_regime'], prefix='vix_regime')
            self.df = pd.concat([self.df, regime_dummies], axis=1)
            
            # Drop the original categorical column
            self.df = self.df.drop('vix_regime', axis=1)"""

# Fix 2: Update add_trade_features to drop original strategy_type
fix2 = """            # One-hot encode
            strategy_dummies = pd.get_dummies(self.df['strategy_type'], prefix='strategy')
            self.df = pd.concat([self.df, strategy_dummies], axis=1)"""

fix2_replacement = """            # One-hot encode
            strategy_dummies = pd.get_dummies(self.df['strategy_type'], prefix='strategy')
            self.df = pd.concat([self.df, strategy_dummies], axis=1)
            
            # Drop the original categorical column
            self.df = self.df.drop('strategy_type', axis=1)"""

# Apply fixes
content = content.replace(fix1, fix1_replacement)
content = content.replace(fix2, fix2_replacement)

# Write the fixed file
with open("src/phase1_data_preparation.py", "w") as f:
    f.write(content)

print("✓ Fixed phase1_data_preparation.py")
print("\nChanges made:")
print("1. Drop 'vix_regime' after one-hot encoding")
print("2. Drop 'strategy_type' after one-hot encoding")

print("\nNext steps:")
print("1. Re-run data preparation: python src/phase1_data_preparation.py")
print("2. Run XGBoost model: python src/models/xgboost_baseline.py")
print("\nNote: Re-running data preparation will take some time as it processes all the IBKR data.")

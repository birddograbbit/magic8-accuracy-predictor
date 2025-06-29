#!/usr/bin/env python
"""
Clean rebuild script for Phase 1 data processing
This script will help rebuild the data from scratch with proper validation
"""

import os
import shutil
import pandas as pd
import json
from datetime import datetime

def check_ibkr_data():
    """Check which IBKR data files are available"""
    print("\n1. Checking IBKR Data Availability")
    print("=" * 50)
    
    ibkr_path = "data/ibkr"
    required_symbols = {
        'SPX': 'INDEX_SPX',
        'SPY': 'STOCK_SPY',
        'XSP': 'INDEX_XSP',
        'NDX': 'INDEX_NDX',
        'QQQ': 'STOCK_QQQ',
        'RUT': 'INDEX_RUT',
        'AAPL': 'STOCK_AAPL',
        'TSLA': 'STOCK_TSLA',
        'VIX': 'INDEX_VIX'
    }
    
    available = []
    missing = []
    
    for symbol, ibkr_name in required_symbols.items():
        filename = f'historical_data_{ibkr_name}_5_mins.csv'
        filepath = os.path.join(ibkr_path, filename)
        
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            available.append(f"✓ {symbol}: {len(df)} records")
        else:
            missing.append(f"✗ {symbol}: Missing file {filename}")
    
    print("Available data:")
    for item in available:
        print(f"  {item}")
    
    if missing:
        print("\nMissing data:")
        for item in missing:
            print(f"  {item}")
    
    return len(missing) == 0

def check_normalized_data():
    """Check the normalized trading data"""
    print("\n2. Checking Normalized Trading Data")
    print("=" * 50)
    
    filepath = "data/normalized/normalized_aggregated.csv"
    if not os.path.exists(filepath):
        print(f"✗ Missing normalized data at {filepath}")
        return False
    
    df = pd.read_csv(filepath)
    print(f"✓ Found normalized data: {len(df)} records")
    
    # Check for required columns
    required_cols = ['interval_datetime', 'pred_symbol', 'trad_profited', 'prof_profit']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"✗ Missing required columns: {missing_cols}")
        return False
    
    # Check target distribution
    if 'trad_profited' in df.columns:
        target_dist = df['trad_profited'].value_counts()
        print(f"  Target distribution: {target_dist.to_dict()}")
    
    return True

def backup_existing_processed_data():
    """Backup existing processed data before reprocessing"""
    print("\n3. Backing Up Existing Processed Data")
    print("=" * 50)
    
    if os.path.exists("data/phase1_processed"):
        backup_dir = f"data/phase1_processed_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.move("data/phase1_processed", backup_dir)
        print(f"✓ Backed up existing data to {backup_dir}")
    else:
        print("  No existing processed data to backup")

def run_data_preparation():
    """Run the data preparation pipeline"""
    print("\n4. Running Data Preparation Pipeline")
    print("=" * 50)
    
    try:
        # Import and run the pipeline
        from src.phase1_data_preparation import Phase1DataPreparation
        
        prep = Phase1DataPreparation()
        train_data, val_data, test_data = prep.run_phase1_pipeline()
        
        print("\n✓ Data preparation completed successfully!")
        print(f"  Train samples: {len(train_data)}")
        print(f"  Val samples: {len(val_data)}")
        print(f"  Test samples: {len(test_data)}")
        
        # Check class distribution
        print("\nClass distribution:")
        print(f"  Train: {train_data['target'].value_counts().to_dict()}")
        print(f"  Val: {val_data['target'].value_counts().to_dict()}")
        print(f"  Test: {test_data['target'].value_counts().to_dict()}")
        
        return True
    except Exception as e:
        print(f"✗ Error during data preparation: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_processed_data():
    """Validate the processed data quality"""
    print("\n5. Validating Processed Data Quality")
    print("=" * 50)
    
    try:
        # Load feature info
        with open('data/phase1_processed/feature_info.json', 'r') as f:
            feature_info = json.load(f)
        
        print(f"✓ Total features: {feature_info['n_features']}")
        
        # Check for categorical columns in the saved data
        train_df = pd.read_csv('data/phase1_processed/train_data.csv')
        
        object_cols = []
        for col in feature_info['feature_names']:
            if col in train_df.columns and train_df[col].dtype == 'object':
                object_cols.append(col)
        
        if object_cols:
            print(f"⚠️  Warning: Found object columns in processed data: {object_cols}")
        else:
            print("✓ No object/string columns in features (good!)")
        
        # Check class balance
        class_dist = feature_info['class_distribution']
        for split, dist in class_dist.items():
            total = sum(dist.values())
            if total > 0:
                positive_ratio = dist.get('1', 0) / total
                print(f"  {split}: {positive_ratio:.1%} positive samples")
                
                if positive_ratio < 0.01:
                    print(f"    ⚠️  Warning: Very few positive samples in {split} set!")
        
        return True
    except Exception as e:
        print(f"✗ Error validating data: {e}")
        return False

def main():
    """Main execution flow"""
    print("Phase 1 Data Rebuild Script")
    print("=" * 70)
    print("This script will rebuild the Phase 1 data from scratch")
    print("Make sure you have all IBKR data downloaded first!")
    
    # Step 1: Check prerequisites
    has_ibkr = check_ibkr_data()
    has_normalized = check_normalized_data()
    
    if not has_ibkr or not has_normalized:
        print("\n❌ Missing required data! Please ensure:")
        print("  1. All IBKR data is downloaded to data/ibkr/")
        print("  2. Normalized trade data exists at data/normalized/normalized_aggregated.csv")
        return
    
    # Ask for confirmation
    print("\n" + "="*70)
    response = input("Ready to rebuild data? This will take several minutes. (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    # Step 2: Backup existing data
    backup_existing_processed_data()
    
    # Step 3: Run data preparation
    success = run_data_preparation()
    
    if not success:
        print("\n❌ Data preparation failed!")
        return
    
    # Step 4: Validate results
    validate_processed_data()
    
    print("\n" + "="*70)
    print("✅ Data rebuild complete!")
    print("\nNext steps:")
    print("1. Review the class distribution warnings above")
    print("2. Run the XGBoost model: python src/models/xgboost_baseline.py")
    print("3. Check logs/ for detailed processing logs")

if __name__ == "__main__":
    main()

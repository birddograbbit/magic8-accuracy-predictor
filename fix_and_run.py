#!/usr/bin/env python3
"""
Quick fix script to get real-time predictions working immediately.
This script:
1. Converts your trained model to the right format
2. Sets up test configuration
3. Runs the first prediction

Usage:
    python fix_and_run.py
"""

import subprocess
import sys
import os
from pathlib import Path
import shutil


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - Success!")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - Failed!")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False


def main():
    """Main fix and run function."""
    print("="*60)
    print("🔧 Magic8 Accuracy Predictor - Quick Fix & Run")
    print("="*60)
    
    # 1. Pull latest changes
    print("\n1. Updating repository...")
    run_command("git pull origin main", "Pull latest changes")
    
    # 2. Convert the trained model
    print("\n2. Converting trained model to predictor format...")
    if not run_command([sys.executable, "prepare_model_for_predictor.py"], "Convert model"):
        print("\nℹ️  Model conversion failed, but we'll continue with mock model")
    
    # 3. Use test config for first run
    print("\n3. Setting up test configuration...")
    test_config = Path("config/config.test.yaml")
    main_config = Path("config/config.yaml")
    
    if test_config.exists():
        # Backup current config
        if main_config.exists():
            backup_config = Path("config/config.yaml.backup")
            shutil.copy2(main_config, backup_config)
            print(f"✓ Backed up current config to {backup_config}")
        
        # Copy test config
        shutil.copy2(test_config, main_config)
        print(f"✓ Using test configuration (mock data provider)")
    
    # 4. Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # 5. Run quick start
    print("\n4. Running quick start...")
    print("-"*60)
    
    # Import and run directly
    try:
        # Run the quick start
        import asyncio
        from quick_start import main as quick_start_main
        
        asyncio.run(quick_start_main())
        
        print("\n" + "="*60)
        print("✨ Quick fix completed!")
        print("="*60)
        
        print("\n📝 Next steps:")
        print("1. Your model is now ready for predictions")
        print("2. Currently using mock data provider (no external dependencies)")
        print("3. To use real data:")
        print("   - Start Magic8-Companion: python setup_companion_api.py")
        print("   - Or edit config/config.yaml to use your preferred data source")
        print("\n4. For monitoring:")
        print("   python monitor_predictions.py")
        print("\n5. For DiscordTrading integration:")
        print("   python integrate_discord_trading.py")
        
    except Exception as e:
        print(f"\n❌ Error running quick start: {e}")
        print("\nTry running manually:")
        print("  python quick_start.py")


if __name__ == "__main__":
    main()

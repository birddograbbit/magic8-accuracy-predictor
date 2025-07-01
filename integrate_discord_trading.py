#!/usr/bin/env python3
"""
Integration Script for DiscordTrading
Copies necessary files and provides integration instructions.

Usage:
    python integrate_discord_trading.py [--discord-path /path/to/DiscordTrading]
"""

import shutil
import os
import sys
from pathlib import Path
import argparse
import yaml


def find_discord_trading_path():
    """Try to find DiscordTrading path automatically."""
    possible_paths = [
        Path.home() / "DiscordTrading",
        Path.home() / "projects" / "DiscordTrading",
        Path.home() / "code" / "DiscordTrading",
        Path("..") / "DiscordTrading",
        Path("../..") / "DiscordTrading"
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "discord_trading_bot.py").exists():
            return path
    
    return None


def copy_integration_files(discord_path):
    """Copy necessary files to DiscordTrading."""
    discord_path = Path(discord_path)
    
    if not discord_path.exists():
        print(f"❌ DiscordTrading path not found: {discord_path}")
        return False
    
    print(f"📁 Integrating with DiscordTrading at: {discord_path}")
    
    # Files to copy
    files_to_copy = [
        ("src/real_time_predictor.py", "real_time_predictor.py"),
        ("src/data_providers", "data_providers"),
        ("src/feature_engineering", "feature_engineering")
    ]
    
    copied_files = []
    
    for src, dst in files_to_copy:
        src_path = Path(src)
        dst_path = discord_path / dst
        
        try:
            if src_path.is_dir():
                # Copy directory
                if dst_path.exists():
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
                print(f"✓ Copied directory: {src} -> {dst}")
            else:
                # Copy file
                shutil.copy2(src_path, dst_path)
                print(f"✓ Copied file: {src} -> {dst}")
            
            copied_files.append(dst_path)
            
        except Exception as e:
            print(f"❌ Failed to copy {src}: {e}")
            return False
    
    return True


def create_integration_wrapper(discord_path):
    """Create integration wrapper for DiscordTrading."""
    wrapper_content = '''"""
Magic8 Accuracy Predictor Integration for DiscordTrading
This module provides seamless integration with the ML prediction system.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from real_time_predictor import get_prediction_service, PredictionResult

logger = logging.getLogger(__name__)


class Magic8PredictorIntegration:
    """Integration wrapper for Magic8 accuracy predictions."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the predictor integration."""
        self.config = config.get('accuracy_predictor', {})
        self.enabled = self.config.get('enabled', False)
        self.min_win_probability = self.config.get('min_win_probability', 0.55)
        self.skip_on_error = self.config.get('skip_on_error', False)
        self.log_all_predictions = self.config.get('log_all_predictions', True)
        
        self.prediction_service = None
        self._initialized = False
        
        if self.enabled:
            logger.info("Magic8 Accuracy Predictor integration enabled")
            logger.info(f"Minimum win probability threshold: {self.min_win_probability:.1%}")
    
    async def initialize(self):
        """Initialize the prediction service."""
        if not self.enabled or self._initialized:
            return
        
        try:
            logger.info("Initializing Magic8 prediction service...")
            self.prediction_service = get_prediction_service()
            
            # Warmup
            await self.prediction_service.warmup_all()
            
            self._initialized = True
            logger.info("✓ Magic8 prediction service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize prediction service: {e}")
            if not self.skip_on_error:
                raise
    
    async def should_trade(self, order: Dict[str, Any]) -> tuple[bool, Optional[PredictionResult]]:
        """
        Determine if a trade should be executed based on ML prediction.
        
        Returns:
            tuple: (should_trade, prediction_result)
        """
        if not self.enabled:
            return True, None
        
        if not self._initialized:
            await self.initialize()
        
        try:
            # Make prediction
            result = await self.prediction_service.predict(order)
            
            if result is None:
                logger.warning(f"No predictor available for {order.get('symbol')}")
                return self.skip_on_error, None
            
            # Log prediction
            if self.log_all_predictions:
                logger.info(
                    f"Prediction for {order['symbol']} {order['strategy']}: "
                    f"Win Prob={result.win_probability:.1%}, "
                    f"Confidence={result.confidence:.1%}, "
                    f"Latency={result.prediction_time_ms:.0f}ms"
                )
            
            # Make decision
            should_trade = result.win_probability >= self.min_win_probability
            
            if not should_trade:
                logger.warning(
                    f"Trade rejected by ML prediction: "
                    f"{result.win_probability:.1%} < {self.min_win_probability:.1%}"
                )
            
            return should_trade, result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self.skip_on_error, None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the predictor."""
        if not self.enabled:
            return {"enabled": False}
        
        status = {
            "enabled": True,
            "initialized": self._initialized,
            "min_win_probability": self.min_win_probability
        }
        
        if self._initialized and self.prediction_service:
            status.update(self.prediction_service.get_status())
        
        return status


# Convenience function for easy integration
async def check_trade_ml(order: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """
    Quick function to check if a trade should be executed.
    
    Args:
        order: The trade order to check
        config: DiscordTrading configuration
        
    Returns:
        bool: True if trade should be executed
    """
    integration = Magic8PredictorIntegration(config)
    should_trade, _ = await integration.should_trade(order)
    return should_trade
'''
    
    wrapper_path = discord_path / "magic8_predictor_integration.py"
    wrapper_path.write_text(wrapper_content)
    print(f"✓ Created integration wrapper: {wrapper_path.name}")
    
    return wrapper_path


def update_discord_config(discord_path):
    """Update DiscordTrading config with predictor settings."""
    config_path = discord_path / "config.yaml"
    
    if not config_path.exists():
        print("⚠️  No config.yaml found in DiscordTrading")
        return False
    
    # Read existing config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f) or {}
    
    # Add accuracy predictor config
    if 'accuracy_predictor' not in config:
        config['accuracy_predictor'] = {
            'enabled': True,
            'min_win_probability': 0.55,
            'skip_on_error': False,
            'log_all_predictions': True,
            'model_path': str(Path.cwd() / 'models' / 'xgboost_phase1_model.pkl'),
            'data_source': 'companion'
        }
        
        # Backup original config
        backup_path = config_path.with_suffix('.yaml.backup')
        shutil.copy2(config_path, backup_path)
        print(f"✓ Backed up config to: {backup_path.name}")
        
        # Write updated config
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print("✓ Updated config.yaml with accuracy_predictor settings")
    else:
        print("ℹ️  accuracy_predictor already configured in config.yaml")
    
    return True


def show_integration_code():
    """Show code snippets for manual integration."""
    print("\n" + "="*60)
    print("Integration Code Snippets")
    print("="*60)
    
    print("\n1. Add to discord_trading_bot.py imports:")
    print("-"*40)
    print("""
from magic8_predictor_integration import Magic8PredictorIntegration
""")
    
    print("\n2. Initialize in __init__:")
    print("-"*40)
    print("""
# Initialize ML predictor
self.ml_predictor = Magic8PredictorIntegration(self.config)
""")
    
    print("\n3. Add to process_trade_instruction():")
    print("-"*40)
    print("""
# Check ML prediction before executing trade
if hasattr(self, 'ml_predictor'):
    should_trade, prediction = await self.ml_predictor.should_trade(order)
    
    if not should_trade:
        logger.info(f"Trade rejected by ML prediction")
        return None
    
    if prediction:
        logger.info(f"ML prediction approved: {prediction.win_probability:.1%}")
""")
    
    print("\n4. Add to status command:")
    print("-"*40)
    print("""
# Add ML predictor status
if hasattr(self, 'ml_predictor'):
    ml_status = self.ml_predictor.get_status()
    status_msg += f"\\nML Predictor: {ml_status.get('enabled', False)}"
""")


def main():
    """Main integration function."""
    parser = argparse.ArgumentParser(description="Integrate Magic8 Predictor with DiscordTrading")
    parser.add_argument(
        '--discord-path',
        type=str,
        help='Path to DiscordTrading directory'
    )
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🎱 Magic8 Predictor - DiscordTrading Integration")
    print("="*60)
    
    # Find DiscordTrading path
    if args.discord_path:
        discord_path = Path(args.discord_path)
    else:
        discord_path = find_discord_trading_path()
        
        if discord_path:
            print(f"✓ Found DiscordTrading at: {discord_path}")
        else:
            print("❌ Could not find DiscordTrading automatically")
            discord_path = input("Please enter the path to DiscordTrading: ").strip()
            discord_path = Path(discord_path)
    
    if not discord_path.exists():
        print(f"❌ DiscordTrading not found at: {discord_path}")
        return 1
    
    # Copy integration files
    print("\nCopying integration files...")
    if not copy_integration_files(discord_path):
        return 1
    
    # Create integration wrapper
    create_integration_wrapper(discord_path)
    
    # Update config
    update_discord_config(discord_path)
    
    # Show integration code
    show_integration_code()
    
    print("\n" + "="*60)
    print("✅ Integration Complete!")
    print("="*60)
    
    print("\nNext steps:")
    print("1. Review and update the config settings in config.yaml")
    print("2. Add the integration code to discord_trading_bot.py")
    print("3. Restart DiscordTrading")
    print("\nFor testing:")
    print("  python quick_start.py  # Test predictions standalone")
    print("\nFor help:")
    print("  See docs/REAL_TIME_INTEGRATION_PLAN.md")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

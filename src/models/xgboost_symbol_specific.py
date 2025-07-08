"""Train XGBoost models for each symbol separately."""

from pathlib import Path
import pandas as pd
import joblib
import xgboost as xgb
import json
import numpy as np
from sklearn.model_selection import train_test_split


def prepare_symbol_data(df: pd.DataFrame):
    """Prepare raw symbol data for training."""
    # Create target from profit
    if 'profit' in df.columns:
        df['target'] = (df['profit'] > 0).astype(int)
    else:
        raise ValueError("No profit column found for creating target")
    
    # Create basic features from raw data
    features_created = []
    
    # Convert timestamp to datetime features
    if 'timestamp' in df.columns:
        df['datetime'] = pd.to_datetime(df['timestamp'], errors='coerce')
    elif 'date' in df.columns and 'time' in df.columns:
        df['datetime'] = pd.to_datetime(
            df['date'].astype(str) + ' ' + df['time'].astype(str), 
            errors='coerce'
        )
    
    if 'datetime' in df.columns:
        df['hour'] = df['datetime'].dt.hour
        df['minute'] = df['datetime'].dt.minute
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        features_created.extend(['hour', 'minute', 'day_of_week', 'hour_sin', 'hour_cos'])
    
    # Numeric features from raw data
    numeric_features = ['price', 'premium', 'predicted', 'risk', 'reward', 
                       'expected_move', 'low', 'high', 'target1', 'target2',
                       'strike1', 'strike2', 'strike3', 'strike4',
                       'bid1', 'ask1', 'bid2', 'ask2']
    
    available_numeric = [f for f in numeric_features if f in df.columns]
    
    # Create risk/reward ratio if possible
    if 'risk' in df.columns and 'reward' in df.columns:
        df['risk_reward_ratio'] = df['reward'] / (df['risk'].abs() + 1e-8)
        features_created.append('risk_reward_ratio')
    
    # Create premium normalized by price if possible
    if 'premium' in df.columns and 'price' in df.columns:
        df['premium_normalized'] = df['premium'] / (df['price'] + 1e-8)
        features_created.append('premium_normalized')
    
    # Create strike width features if strikes available
    strike_cols = ['strike1', 'strike2', 'strike3', 'strike4']
    if all(col in df.columns for col in strike_cols):
        df['strike_width'] = df['strike4'] - df['strike1']
        df['strike_width_normalized'] = df['strike_width'] / (df['price'] + 1e-8)
        features_created.extend(['strike_width', 'strike_width_normalized'])
    
    # One-hot encode strategy
    if 'strategy' in df.columns:
        strategy_dummies = pd.get_dummies(df['strategy'], prefix='strategy')
        for col in strategy_dummies.columns:
            df[col] = strategy_dummies[col]
            features_created.append(col)
    
    # Combine all features
    all_features = features_created + available_numeric
    
    # Remove duplicates and filter to existing columns
    all_features = list(set(f for f in all_features if f in df.columns))
    
    return df, all_features


def train_symbol_model(csv_path: Path, model_dir: Path, features: list = None, target: str = "target"):
    """Train a symbol-specific model handling raw data."""
    print(f"\nTraining model for {csv_path.stem}...")
    
    # Load data
    df = pd.read_csv(csv_path, low_memory=False)
    
    # Prepare data and get available features
    df, available_features = prepare_symbol_data(df)
    
    # If features provided from feature_info, try to use those that exist
    if features:
        # Filter to features that actually exist in this data
        selected_features = [f for f in features if f in df.columns]
        
        # If too few features from feature_info exist, use our prepared features
        if len(selected_features) < 10:
            print(f"Only {len(selected_features)} features from feature_info found, using prepared features")
            selected_features = available_features
    else:
        selected_features = available_features
    
    print(f"Using {len(selected_features)} features")
    
    # Remove any non-numeric columns
    numeric_features = []
    for feat in selected_features:
        if df[feat].dtype in [np.float64, np.float32, np.int64, np.int32, np.uint8]:
            numeric_features.append(feat)
        else:
            try:
                df[feat] = pd.to_numeric(df[feat], errors='coerce')
                numeric_features.append(feat)
            except:
                print(f"Skipping non-numeric feature: {feat}")
    
    selected_features = numeric_features
    
    # Prepare training data
    X = df[selected_features].fillna(0)
    y = df[target]
    
    # Remove rows with missing target
    valid_mask = y.notna()
    X = X[valid_mask]
    y = y[valid_mask]
    
    print(f"Training samples: {len(X)}")
    print(f"Target distribution: {y.value_counts().to_dict()}")
    print(f"Win rate: {y.mean():.2%}")
    
    # Split data for evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Create DMatrix
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    
    # XGBoost parameters
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 4,
        'eta': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
    }
    
    # Train with early stopping
    evals = [(dtrain, 'train'), (dtest, 'eval')]
    model = xgb.train(
        params, 
        dtrain, 
        num_boost_round=200,
        evals=evals,
        early_stopping_rounds=20,
        verbose_eval=50
    )
    
    # Evaluate
    test_pred = model.predict(dtest)
    test_pred_binary = (test_pred > 0.5).astype(int)
    accuracy = (test_pred_binary == y_test).mean()
    print(f"Test accuracy: {accuracy:.2%}")
    
    # Save model and feature list
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"{csv_path.stem}_model.json"
    features_path = model_dir / f"{csv_path.stem}_features.pkl"

    booster = model if isinstance(model, xgb.Booster) else model.get_booster()
    booster.save_model(str(model_path))
    joblib.dump(selected_features, features_path)
    
    print(f"Model saved to: {model_path}")
    print(f"Features saved to: {features_path}")
    
    return model


def train_all_models(data_dir: str, output_dir: str, feature_info: Path = None):
    """Train models for all symbols in the directory."""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    
    # Load feature info if provided
    features = None
    if feature_info and feature_info.exists():
        try:
            with open(feature_info, "r") as f:
                info = json.load(f)
            features = info.get('feature_names', [])
            print(f"Loaded {len(features)} features from feature_info.json")
        except Exception as e:
            print(f"Warning: Could not load feature_info: {e}")
    
    # Train model for each symbol CSV
    csv_files = list(data_dir.glob("*_trades.csv"))
    print(f"Found {len(csv_files)} symbol files to process")
    
    for csv_file in csv_files:
        try:
            symbol = csv_file.stem.split("_")[0]
            train_symbol_model(csv_file, output_dir, features)
            print(f"✓ Successfully trained model for {symbol}")
        except Exception as e:
            print(f"✗ Error training model for {csv_file.stem}: {e}")
            import traceback
            traceback.print_exc()


def train_grouped_model(csv_paths: list[Path], model_dir: Path, group_name: str, features: list | None = None):
    """Train a single model using data from multiple symbols."""
    # Ensure output directory exists
    model_dir.mkdir(parents=True, exist_ok=True)
    
    df_list = [pd.read_csv(p, low_memory=False) for p in csv_paths]
    df = pd.concat(df_list, ignore_index=True)
    tmp_file = model_dir / f"{group_name}_combined.csv"
    df.to_csv(tmp_file, index=False)
    try:
        train_symbol_model(tmp_file, model_dir, features)
        print(f"✓ Grouped model trained for {group_name}")
    finally:
        if tmp_file.exists():
            tmp_file.unlink()


def train_grouped_models(groups: dict[str, list[str]], data_dir: str, output_dir: str, feature_info: Path | None = None):
    """Train models for each group mapping name -> [symbols]."""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)

    features = None
    if feature_info and feature_info.exists():
        try:
            with open(feature_info, "r") as f:
                info = json.load(f)
            features = info.get("feature_names", [])
        except Exception as e:
            print(f"Warning: Could not load feature_info: {e}")

    for group, symbols in groups.items():
        csv_paths = [data_dir / f"{sym}_trades.csv" for sym in symbols]
        csv_paths = [p for p in csv_paths if p.exists()]
        if not csv_paths:
            print(f"No data for group {group} ({symbols})")
            continue
        train_grouped_model(csv_paths, output_dir, group, features)

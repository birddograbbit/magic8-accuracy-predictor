"""Train XGBoost models for each symbol separately."""

from pathlib import Path
import pandas as pd
import joblib
import xgboost as xgb
import json


def train_symbol_model(csv_path: Path, model_dir: Path, features: list, target: str = "target"):
    df = pd.read_csv(csv_path)
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' missing in {csv_path}")
    X = df[features]
    y = df[target]
    dtrain = xgb.DMatrix(X, label=y)
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 4,
        'eta': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
    }
    model = xgb.train(params, dtrain, num_boost_round=200)
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(str(model_dir / f"{csv_path.stem}_model.json"))
    joblib.dump(features, model_dir / f"{csv_path.stem}_features.pkl")
    return model


def train_all_models(data_dir: str, output_dir: str, feature_info: Path):
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    with open(feature_info, "r") as f:
        info = json.load(f)
    features = info.get('feature_names')

    for csv_file in data_dir.glob("*_trades.csv"):
        symbol = csv_file.stem.split("_")[0]
        if not features:
            df_tmp = pd.read_csv(csv_file)
            features = [c for c in df_tmp.columns if c != 'target']
        train_symbol_model(csv_file, output_dir, features)
        print(f"Trained model for {symbol}")


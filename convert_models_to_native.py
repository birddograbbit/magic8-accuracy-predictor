import argparse
from pathlib import Path
import joblib
import xgboost as xgb


def convert_model(pkl_path: Path):
    booster = joblib.load(pkl_path)
    if hasattr(booster, "get_booster"):
        booster = booster.get_booster()
    out_path = pkl_path.with_suffix(".json")
    booster.save_model(str(out_path))
    print(f"Converted {pkl_path} -> {out_path}")


def convert_directory(model_dir: Path):
    for pkl in model_dir.glob("*_model.pkl"):
        convert_model(pkl)


def main():
    parser = argparse.ArgumentParser(description="Convert pickled XGBoost models to JSON format")
    parser.add_argument("model_dir", help="Directory containing *_model.pkl files")
    args = parser.parse_args()
    convert_directory(Path(args.model_dir))


if __name__ == "__main__":
    main()

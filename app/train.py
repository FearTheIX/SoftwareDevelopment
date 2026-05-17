# app/train.py
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
import joblib
import logging
import sqlite3
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "features.db"

def load_features() -> pd.DataFrame:
    logger.info("Загрузка признаков из SQLite...")
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM features", conn, index_col="date")
    return df

def prepare_data(df: pd.DataFrame):
    features = ["lag_1", "lag_7", "ma_7", "ma_30", "day_of_week", "month", "is_weekend"]
    target = "usd_rate"
    X = df[features]
    y = df[target]
    
    # Временное разделение (последние 20% — тест)
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    return X_train, X_test, y_train, y_test

def train_and_log():
    df = load_features()
    X_train, X_test, y_train, y_test = prepare_data(df)

    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    }

    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("USD_RUB_Prediction")

    best_model = None
    best_score = float("inf")
    best_name = ""

    for name, model in models.items():
        logger.info(f"🔹 Обучение {name}...")
        with mlflow.start_run(run_name=name):
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            mae = mean_absolute_error(y_test, preds)
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            r2 = r2_score(y_test, preds)

            logger.info(f"   📊 {name} → MAE: {mae:.2f} | RMSE: {rmse:.2f} | R²: {r2:.2f}")

            mlflow.log_params({"model_type": name, "n_estimators": 100 if name == "RandomForest" else None})
            mlflow.log_metrics({"MAE": mae, "RMSE": rmse, "R2": r2})
            mlflow.sklearn.log_model(model, "model")

            if mae < best_score:
                best_score = mae
                best_model = model
                best_name = name

    model_path = MODELS_DIR / "best_model.pkl"
    joblib.dump(best_model, model_path)
    logger.info(f"✅ Лучшая модель: {best_name} (MAE={best_score:.2f}). Сохранена в {model_path}")
    return best_model, best_name

if __name__ == "__main__":
    train_and_log()
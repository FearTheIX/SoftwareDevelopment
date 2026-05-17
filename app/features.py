# app/features.py
import pandas as pd
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "features.db"
META_PATH = DATA_DIR / "feature_metadata.json"

def load_data() -> pd.DataFrame:
    path = DATA_DIR / "cbr_history.csv"
    if not path.exists():
        raise FileNotFoundError(f"Файл {path} не найден. Сначала запустите scraper.py")
    logger.info(f"Загрузка данных из {path}")
    df = pd.read_csv(path, parse_dates=["date"])
    df.sort_values("date", inplace=True)
    df.set_index("date", inplace=True)
    return df

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Создание признаков...")
    df = df.copy()

    # Временные признаки
    df["day_of_week"] = df.index.dayofweek
    df["month"] = df.index.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # Лаги
    df["lag_1"] = df["usd_rate"].shift(1)
    df["lag_7"] = df["usd_rate"].shift(7)

    # Скользящие средние
    df["ma_7"] = df["usd_rate"].rolling(window=7).mean()
    df["ma_30"] = df["usd_rate"].rolling(window=30).mean()

    # Убираем строки с NaN (появляются из-за shift и rolling)
    df.dropna(inplace=True)
    logger.info(f"После обработки пропусков осталось {len(df)} записей.")
    return df

def save_to_sqlite(df: pd.DataFrame) -> None:
    logger.info(f"Сохранение Feature Store в SQLite: {DB_PATH}")
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("features", conn, if_exists="replace", index=True, index_label="date")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON features(date)")

def save_metadata(df: pd.DataFrame) -> None:
    meta = {
        "created_at": datetime.now().isoformat(),
        "source": "cbr-xml-daily.ru",
        "total_records": int(len(df)),
        "columns": list(df.columns),
        "description": "Признаки для прогнозирования USD/RUB: лаги, скользящие средние, временные флаги",
        "missing_values_handled": "dropna после вычисления лагов/rolling"
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    logger.info(f"Метаданные сохранены в {META_PATH}")

if __name__ == "__main__":
    try:
        DATA_DIR.mkdir(exist_ok=True)
        df = load_data()
        df_feat = create_features(df)
        save_to_sqlite(df_feat)
        save_metadata(df_feat)
        logger.info("✅ Feature engineering завершено успешно!")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
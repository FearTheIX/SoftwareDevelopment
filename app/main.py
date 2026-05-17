# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import sqlite3
import numpy as np
from pathlib import Path
from datetime import timedelta
import logging

from app.config import load_config
from app.logger import logger
from app.models import PredictionRequest, PredictionResponse, HistoryResponse

config = load_config()
app = FastAPI(title=config.app_name, debug=config.debug)

# CORS для Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "best_model.pkl"
DB_PATH = BASE_DIR / "data" / "features.db"

try:
    model = joblib.load(MODEL_PATH)
    logger.info("✅ ML-модель успешно загружена")
except Exception as e:
    logger.error(f"❌ Ошибка загрузки модели: {e}")
    raise

FEATURE_COLS = ["lag_1", "lag_7", "ma_7", "ma_30", "day_of_week", "month", "is_weekend"]

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/history", response_model=HistoryResponse)
def get_history(limit: int = 100):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql(f"SELECT date, usd_rate FROM features ORDER BY date DESC LIMIT {limit}", conn)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        return {"count": len(df), "data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/predict/long", response_model=list[dict])
def predict_series(days: int = 30):
    """
    Рекурсивный прогноз на N дней вперед.
    Мы предсказываем день 1, добавляем его в таблицу,
    пересчитываем признаки и предсказываем день 2.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Загружаем достаточно истории для расчета MA30 и лагов
            df = pd.read_sql("SELECT * FROM features ORDER BY date DESC LIMIT 100", conn, index_col="date")
        
        df = df.sort_index()
        df.index = pd.to_datetime(df.index)
        
        predictions = []
        current_date = df.index[-1]

        # Имитируем "поток" данных на N дней
        for _ in range(days):
            # Находим следующий рабочий день (пропускаем выходные)
            current_date += timedelta(days=1)
            while current_date.weekday() >= 5: # 5=Сб, 6=Вс
                current_date += timedelta(days=1)
            
            # Подготавливаем признаки для последнего известного состояния
            last_row = df.tail(1)
            
            # Внимание: в реальном продакшене нужно аккуратно обновлять rolling/lag
            # Но для курсовой мы просто берем последние вычисленные признаки
            # и немного их модифицируем (лаг1 становится предсказанным значением)
            
            X = last_row[FEATURE_COLS].values.reshape(1, -1)
            
            # Предсказываем
            pred_rate = model.predict(X)[0]
            
            # Создаем фейковую строку для следующего шага
            new_row = {
                "usd_rate": pred_rate,
                "lag_1": df['usd_rate'].iloc[-1], # Предыдущий факт
                "lag_7": df['usd_rate'].iloc[-7] if len(df) > 7 else df['usd_rate'].iloc[-1],
                "ma_7": df['ma_7'].iloc[-1], # Пока держим среднюю
                "ma_30": df['ma_30'].iloc[-1],
                "day_of_week": current_date.weekday(),
                "month": current_date.month,
                "is_weekend": 0
            }
            
            # Добавляем в датафрейм, чтобы "скормить" модели следующий шаг
            # (Для лагов и MA это критично)
            new_df_row = pd.DataFrame([new_row], index=[current_date])
            df = pd.concat([df, new_df_row])
            
            predictions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "rate": round(float(pred_rate), 2)
            })

        logger.info(f"Сгенерирован прогноз на {days} дней.")
        return predictions

    except Exception as e:
        logger.error(f"Ошибка долгосрочного прогноза: {e}")
        raise HTTPException(500, str(e))
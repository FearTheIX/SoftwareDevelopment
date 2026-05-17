# app/generate_mock_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def generate_mock_usd_rub_data(start_date: str = "2016-01-01", 
                                end_date: str = None) -> pd.DataFrame:
    """
    Генерирует реалистичные исторические данные USD/RUB с учетом:
    - Трендов (кризисы, санкции, нефть)
    - Волатильности
    - Сезонности
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Генерируем все рабочие дни (исключая выходные)
    dates = pd.date_range(start=start_date, end=end_date, freq="B")  # B = business days
    
    np.random.seed(42)  # Для воспроизводимости
    n_days = len(dates)
    
    # Базовый тренд с ключевыми точками (реальная история USD/RUB)
    base_rate = np.zeros(n_days)
    
    for i, date in enumerate(dates):
        year = date.year
        month = date.month
        
        # 2016-2017: восстановление после кризиса 2014-2015 (~60-65)
        if year == 2016:
            base = 65 + 3 * np.sin((month - 1) * np.pi / 6)
        elif year == 2017:
            base = 60 + 2 * np.sin((month - 1) * np.pi / 6)
        # 2018-2019: стабильность (~63-68)
        elif year == 2018:
            base = 65 + 3 * np.sin((month - 1) * np.pi / 6)
        elif year == 2019:
            base = 64 + 2 * np.sin((month - 1) * np.pi / 6)
        # 2020: ковидный кризис (март-апрель скачок до 75-80)
        elif year == 2020:
            if month <= 2:
                base = 64
            elif month == 3:
                base = 72 + np.random.uniform(0, 5)
            elif month == 4:
                base = 75 + np.random.uniform(0, 3)
            else:
                base = 73 - (month - 4) * 0.5
        # 2021: стабилизация (~70-75)
        elif year == 2021:
            base = 73 + 2 * np.sin((month - 1) * np.pi / 6)
        # 2022: санкции, резкий рост (февраль-март до 100-120)
        elif year == 2022:
            if month == 1:
                base = 76
            elif month == 2:
                base = 80 + np.random.uniform(0, 10)
            elif month == 3:
                base = 105 + np.random.uniform(0, 15)
            elif month == 4:
                base = 95 + np.random.uniform(-5, 10)
            else:
                base = 85 - (month - 4) * 1.5
        # 2023: волатильность (~80-100)
        elif year == 2023:
            base = 85 + 8 * np.sin((month - 1) * np.pi / 6)
        # 2024: стабилизация (~90-95)
        elif year == 2024:
            base = 92 + 3 * np.sin((month - 1) * np.pi / 6)
        # 2025: текущий год (~95-100)
        elif year == 2025:
            base = 96 + 4 * np.sin((month - 1) * np.pi / 6)
        # 2026: прогноз (~98-105)
        elif year == 2026:
            base = 100 + 3 * np.sin((month - 1) * np.pi / 6)
        else:
            base = 70
        
        base_rate[i] = base
    
    # Добавляем случайную волатильность (шум)
    noise = np.random.normal(0, 1.5, n_days)
    
    # Добавляем тренд (небольшой рост со временем)
    trend = np.linspace(0, 5, n_days)
    
    # Итоговый курс
    usd_rate = base_rate + noise + trend
    usd_rate = np.round(usd_rate, 2)
    
    # EUR/RUB (примерно на 10-15% выше USD)
    eur_rate = np.round(usd_rate * (1.08 + np.random.normal(0, 0.02, n_days)), 2)
    
    df = pd.DataFrame({
        "date": dates,
        "usd_rate": usd_rate,
        "eur_rate": eur_rate
    })
    
    return df

if __name__ == "__main__":
    logger.info("🎲 Генерация мок-данных USD/RUB (2016-2026)...")
    
    df = generate_mock_usd_rub_data()
    
    from pathlib import Path
    OUTPUT_DIR = Path("data")
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    output_file = OUTPUT_DIR / "cbr_history.csv"
    df.to_csv(output_file, index=False)
    
    logger.info(f"✅ Сгенерировано {len(df)} записей")
    logger.info(f"📊 Период: {df['date'].min().date()} — {df['date'].max().date()}")
    logger.info(f"💵 Курс USD: {df['usd_rate'].min()} - {df['usd_rate'].max()} RUB")
    logger.info(f"💶 Курс EUR: {df['eur_rate'].min()} - {df['eur_rate'].max()} RUB")
    logger.info(f"💾 Сохранено в: {output_file}")
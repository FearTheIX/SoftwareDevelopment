# app/scraper.py
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging

# Настраиваем логирование, чтобы видеть всё
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://www.cbr-xml-daily.ru/archive"
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

def fetch_daily_rate(date_str: str) -> dict | None:
    """Запрашивает курс за один день. Каждая сессия изолирована."""
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Coursework Project / FastAPI)"})
    url = f"{BASE_URL}/{date_str.replace('-', '/')}/daily_json.js"
    
    try:
        resp = session.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            return {"date": date_str, "usd_rate": data["Valute"]["USD"]["Value"]}
        else:
            logger.warning(f"HTTP {resp.status_code} для {date_str}")
            return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Сетевая ошибка для {date_str}: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка для {date_str}: {e}")
        return None
    finally:
        session.close()

def fetch_historical_rates(start_date: str = "2016-01-01", end_date: str = None) -> pd.DataFrame:
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    # Исключаем выходные (ЦБ не публикует в сб/вс)
    date_strs = [d.strftime("%Y-%m-%d") for d in dates if d.weekday() < 5]
    total = len(date_strs)
    logger.info(f"📅 Всего дней для запроса: {total}")

    records = []
    # 4 потока - оптимально для баланса скорости и стабильности
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_date = {executor.submit(fetch_daily_rate, d): d for d in date_strs}
        
        for i, future in enumerate(as_completed(future_to_date), 1):
            date_str = future_to_date[future]
            result = future.result()
            
            if result:
                records.append(result)
            
            # Выводим прогресс каждые 50 запросов (вместо 200)
            if i % 50 == 0 or i == total:
                logger.info(f"🔄 Прогресс: {i}/{total} | Собрано: {len(records)} записей")
            
            # Минимальная задержка, чтобы не упереться в лимиты зеркала ЦБ
            time.sleep(0.08)

    return pd.DataFrame(records)

if __name__ == "__main__":
    logger.info("🚀 Запуск скрейпера (отлаженная версия)...")
    
    # Быстрый тест доступности API
    try:
        test = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=5)
        if test.status_code == 200:
            logger.info("✅ Связь с API ЦБ установлена.")
        else:
            logger.warning(f"⚠️ API вернул статус {test.status_code}. Проверь интернет.")
    except Exception as e:
        logger.error(f"❌ Не могу достучаться до API ЦБ: {e}")
        logger.info("💡 Если API недоступен, можем сгенерировать тестовые данные для курсовой. Дай знать!")
        exit()

    df = fetch_historical_rates()
    
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        output_file = OUTPUT_DIR / "cbr_history.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"✅ Готово! {len(df)} записей сохранены в {output_file}")
        logger.info(f"📊 Период: {df['date'].min().date()} — {df['date'].max().date()}")
    else:
        logger.error("❌ Данные не собраны. Проверь логи выше.")
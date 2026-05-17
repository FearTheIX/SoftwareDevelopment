# 💱 Currency Predictor: USD/RUB Forecasting App

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-✓-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 О проекте

**Currency Predictor** — это полнофункциональное клиент-серверное приложение для прогнозирования курса доллара США к российскому рублю (USD/RUB) на основе исторических данных ЦБ РФ.

### 🔑 Ключевые возможности
- 📊 **Сбор данных**: Web Scraping с `cbr-xml-daily.ru` (исторические курсы с 2016 года)
- 🧠 **ML-прогнозирование**: Регрессионная модель (RandomForestRegressor) с оценкой качества (MAE, RMSE, R²)
- 🗄️ **Feature Store**: Упрощённое хранилище признаков на SQLite + JSON-метаданные
- 🚀 **REST API**: FastAPI-бэкенд с автоматической документацией (Swagger)
- 🎨 **Интерактивный UI**: Streamlit-фронтенд с графиками и прогнозом на 1–60 дней
- 🐳 **Контейнеризация**: Docker + docker-compose для воспроизводимости среды
- ☸️ **Kubernetes**: Готовые манифесты для деплоя в Minikube

---

## 🛠️ Технологический стек

| Категория | Технологии |
|-----------|-----------|
| **Язык** | Python 3.11+ |
| **Backend** | FastAPI, Uvicorn, Pydantic, environs |
| **Frontend** | Streamlit, Plotly |
| **Data & ML** | pandas, numpy, scikit-learn, MLflow, joblib |
| **Хранение** | SQLite, CSV, JSON |
| **DevOps** | Docker, docker-compose, Kubernetes manifests |
| **Инструменты** | Git, VS Code, pre-commit (black, flake8, isort) |


## 🚀 Быстрый старт

### ▶️ Локальный запуск (без Docker)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/FearTheIX/SoftwareDevelopment.git
cd SoftwareDevelopment

# 2. Создать и активировать виртуальное окружение
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить бэкенд (в одном терминале)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Запустить фронтенд (в другом терминале)
streamlit run frontend/app.py --server.port 8501
```

🌐 Открой в браузере:
Frontend: http://localhost:8501
Backend (Swagger): http://localhost:8000/docs

🐳 Запуск через Docker (рекомендуется)
```bash
# 1. Убедись, что Docker Desktop запущен

# 2. Собери и запусти контейнеры
docker compose up --build -d

# 3. Проверь статус
docker compose ps

# 4. Открой приложение
# Frontend: http://localhost:8501
# Backend:  http://localhost:8000/docs
```

🛑 Остановка:
```bash
docker compose down
```

☸️ Деплой в Kubernetes (Minikube)
```bash
# 1. Запусти Minikube
minikube start

# 2. Собери образы внутри Minikube
eval $(minikube docker-env)
docker build -t currency-backend:latest -f Dockerfile.backend .
docker build -t currency-frontend:latest -f Dockerfile.frontend .

# 3. Примени манифесты
kubectl apply -f k8s/

# 4. Проверь поды и сервисы
kubectl get pods
kubectl get services

# 5. Открой фронтенд (NodePort)
minikube service currency-frontend-svc --url
```
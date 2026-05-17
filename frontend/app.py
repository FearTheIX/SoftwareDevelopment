# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="USD/RUB Predictor", layout="wide")
st.title(" Прогнозирование курса USD/RUB")
st.markdown("Клиент-серверное приложение: FastAPI + Streamlit + ML (RandomForest)")

# Боковая панель
with st.sidebar:
    st.header("⚙️ Настройки")
    forecast_days = st.slider("Горизонт прогноза (дней):", 1, 60, 30)
    if st.button("🔄 Обновить данные", use_container_width=True):
        st.rerun()
    st.info("Данные: Feature Store (SQLite)\nМодель: RandomForestRegressor")

# Загрузка истории
try:
    resp = requests.get(f"{API_URL}/history?limit=200")
    resp.raise_for_status()
    history = resp.json()["data"]
    df_hist = pd.DataFrame(history)
    df_hist["date"] = pd.to_datetime(df_hist["date"])
    df_hist = df_hist.sort_values("date")
except Exception as e:
    st.error(f"❌ Ошибка подключения к API: {e}")
    st.stop()

# Блок прогноза
st.subheader("🔮 Прогнозирование")
col1, col2 = st.columns([3, 1])

with col1:
    if st.button(f"🚀 Рассказать прогноз на {forecast_days} дней", type="primary", use_container_width=True):
        with st.spinner(f"Вычисляем тренд на {forecast_days} дней..."):
            try:
                # Запрос к новому эндпоинту
                pred_resp = requests.post(f"{API_URL}/predict/long?days={forecast_days}")
                pred_resp.raise_for_status()
                forecast_data = pred_resp.json()
                
                df_forecast = pd.DataFrame(forecast_data)
                df_forecast["date"] = pd.to_datetime(df_forecast["date"])
                
                st.session_state['forecast_df'] = df_forecast
                st.success("✅ Прогноз построен!")
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")

# График
st.subheader(" Динамика и Прогноз")

fig = go.Figure()

# Историческая линия
fig.add_trace(go.Scatter(
    x=df_hist["date"], y=df_hist["usd_rate"],
    mode='lines', name='История',
    line=dict(color='blue', width=2)
))

# Линия прогноза (если есть)
if 'forecast_df' in st.session_state:
    df_f = st.session_state['forecast_df']
    # Добавляем точку стыковки
    last_hist_point = df_hist.iloc[[-1]]
    df_combined = pd.concat([last_hist_point, df_f])
    
    fig.add_trace(go.Scatter(
        x=df_combined["date"], y=df_combined["rate"],
        mode='lines', name='Прогноз (ML)',
        line=dict(color='red', width=3, dash='dash')
    ))
    
    # Метрика последнего прогноза
    st.metric("Курс через месяц (прогноз)", f"{df_f['rate'].iloc[-1]} RUB")

fig.update_layout(
    xaxis_title="Дата",
    yaxis_title="Курс USD/RUB",
    template="plotly_white",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# Таблица
if 'forecast_df' in st.session_state:
    st.subheader("📊 Таблица прогноза")
    st.dataframe(st.session_state['forecast_df'], hide_index=True)
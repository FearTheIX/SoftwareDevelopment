from pydantic import BaseModel
from typing import Optional

class PredictionRequest(BaseModel):
    # В реальном проекте здесь могут быть параметры запроса
    # Для демо оставляем пустым, но модель валидации должна присутствовать
    pass

class PredictionResponse(BaseModel):
    predicted_rate: float
    date: str
    model_name: str
    confidence: Optional[float] = None

class HistoryResponse(BaseModel):
    count: int
    data: list[dict]
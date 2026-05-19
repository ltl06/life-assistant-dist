"""天气路由"""
import os
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User
from routers.auth import get_current_user

router = APIRouter()

class WeatherResponse(BaseModel):
    city: str
    temp: float
    condition: str
    humidity: int
    wind_speed: float
    suggestion: str
    icon: str

WEATHER_ICONS = {
    "晴": "☀️", "多云": "⛅", "阴": "☁️", "小雨": "🌧️", "中雨": "🌧️",
    "大雨": "⛈️", "雷阵雨": "⛈️", "小雪": "🌨️", "雪": "❄️", "雾": "🌫️",
    "霾": "🌫️", "沙尘暴": "🌪️", "雾霾": "🌫️",
}

WEATHER_SUGGESTIONS = {
    "晴": "天气晴朗，适合户外活动！记得多喝水，做好防晒。",
    "多云": "多云天气，不冷不热，散步或骑行都是好选择。",
    "阴": "天气阴沉，注意保持好心情，可以室内运动。",
    "小雨": "有小雨，外出记得带伞，室内健身也不错。",
    "中雨": "雨势渐大，建议室内活动，注意添衣保暖。",
    "大雨": "大雨天气，尽量减少外出，在家看看书吧。",
    "雷阵雨": "雷雨天气，注意安全，避免在户外活动。",
    "雪": "下雪啦！注意防滑保暖，喝点热饮暖暖身子。",
    "雾": "有雾天气，能见度低，驾车出行注意安全。",
    "霾": "有雾霾，建议戴口罩，减少户外活动时间。",
}

def parse_condition(code: int) -> str:
    mapping = {
        1000: "晴", 1003: "多云", 1006: "阴", 1009: "阴",
        1030: "雾", 1135: "霾", 1147: "雾霾",
        1063: "小雨", 1150: "小雨", 1153: "小雨",
        1180: "中雨", 1183: "中雨", 1186: "大雨", 1189: "大雨",
        1273: "雷阵雨", 1276: "雷阵雨",
        1066: "小雪", 1114: "雪", 1210: "小雪", 1213: "雪",
    }
    return mapping.get(code, "多云")

def get_suggestion(condition: str) -> str:
    return WEATHER_SUGGESTIONS.get(condition, "今日天气一般，注意保重身体！")

@router.get("/current", response_model=WeatherResponse)
def get_weather(
    city: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    location = city or current_user.location or "北京"

    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return WeatherResponse(
            city=location,
            temp=22.0,
            condition="多云",
            humidity=60,
            wind_speed=3.0,
            suggestion="天气服务未配置，请在 .env 中设置 WEATHER_API_KEY。",
            icon="⛅",
        )

    try:
        import httpx
        resp = httpx.get(
            f"https://api.weatherapi.com/v1/current.json",
            params={"key": api_key, "q": location, "lang": "zh"},
            timeout=5.0,
        )
        if resp.status_code == 200:
            d = resp.json()["current"]
            cond = d["condition"]["text"]
            return WeatherResponse(
                city=d.get("location", {}).get("name", location),
                temp=round(d["temp_c"], 1),
                condition=cond,
                humidity=d["humidity"],
                wind_speed=round(d["wind_kph"] / 3.6, 1),
                suggestion=get_suggestion(cond),
                icon=WEATHER_ICONS.get(cond, "🌤️"),
            )
    except Exception:
        pass

    return WeatherResponse(
        city=location,
        temp=22.0,
        condition="多云",
        humidity=60,
        wind_speed=3.0,
        suggestion="天气获取失败，请检查网络或 API Key。",
        icon="⛅",
    )

"""天气查询工具"""
import os
import httpx
from datetime import date

functions = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前天气和穿衣建议。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海、广州、深圳。留空则使用用户设置的城市。",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "查询指定城市未来3天天气预报。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海、广州、深圳。",
                    },
                },
                "required": ["city"],
            },
        },
    },
]

WEATHER_ICONS = {
    "晴": "☀️", "多云": "⛅", "阴": "☁️", "小雨": "🌧️", "中雨": "🌧️",
    "大雨": "⛈️", "雷阵雨": "⛈️", "小雪": "🌨️", "雪": "❄️", "雾": "🌫️",
    "霾": "🌫️", "沙尘暴": "🌪️", "雾霾": "🌫️",
}

SUGGESTIONS = {
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


def execute(name: str, args: dict, db, user_id: int):
    if name == "get_weather":
        return _get_weather(args, db, user_id)
    if name == "get_weather_forecast":
        return _get_forecast(args, db, user_id)
    return {"error": f"未知工具: {name}"}


def _get_default_city(db, user_id: int):
    from database import User
    user = db.query(User).filter(User.id == user_id).first()
    return user.location if user and user.location else "北京"


def _get_weather(args: dict, db, user_id: int):
    city = args.get("city", "").strip()
    if not city:
        city = _get_default_city(db, user_id)

    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return {
            "city": city,
            "temp": 22.0,
            "condition": "多云",
            "humidity": 60,
            "wind_speed": 3.0,
            "suggestion": "天气服务未配置，请在设置中填写城市。",
            "icon": "⛅",
            "note": "API Key 未配置，返回模拟数据",
        }

    try:
        resp = httpx.get(
            f"https://api.weatherapi.com/v1/current.json",
            params={"key": api_key, "q": city, "lang": "zh"},
            timeout=5.0,
        )
        if resp.status_code == 200:
            d = resp.json()["current"]
            cond_text = d["condition"]["text"]
            cond = parse_condition(d["condition"]["code"])
            suggestion = SUGGESTIONS.get(cond, "今日天气一般，注意保重身体！")
            return {
                "city": d.get("location", {}).get("name", city),
                "temp": round(d["temp_c"], 1),
                "feels_like": round(d["feelslike_c"], 1),
                "condition": cond_text,
                "condition_emoji": WEATHER_ICONS.get(cond, "🌤️"),
                "humidity": d["humidity"],
                "wind_speed": round(d["wind_kph"] / 3.6, 1),
                "uv_index": d.get("uv", 0),
                "suggestion": suggestion,
            }
        else:
            return {"error": f"天气查询失败：{resp.status_code}"}
    except Exception as e:
        return {"error": f"天气查询异常：{str(e)}"}


def _get_forecast(args: dict, db, user_id: int):
    city = args.get("city", "").strip()
    if not city:
        city = _get_default_city(db, user_id)

    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        days = ["明天", "后天", "大后天"]
        return {
            "city": city,
            "forecast": [
                {"date": str(date.today()), "day": days[i], "high": 25, "low": 18, "condition": "多云", "icon": "⛅"}
                for i in range(3)
            ],
            "note": "API Key 未配置，返回模拟数据",
        }

    try:
        resp = httpx.get(
            f"https://api.weatherapi.com/v1/forecast.json",
            params={"key": api_key, "q": city, "lang": "zh", "days": 3},
            timeout=5.0,
        )
        if resp.status_code == 200:
            d = resp.json()
            forecast_days = d["forecast"]["forecastday"]
            result = []
            day_labels = ["明天", "后天", "大后天"]
            for i, day in enumerate(forecast_days[1:] if len(forecast_days) > 1 else forecast_days):
                cond = parse_condition(day["day"]["condition"]["code"])
                result.append({
                    "date": day["date"],
                    "day": day_labels[i] if i < len(day_labels) else day["date"],
                    "high": round(day["day"]["maxtemp_c"], 1),
                    "low": round(day["day"]["mintemp_c"], 1),
                    "condition": day["day"]["condition"]["text"],
                    "icon": WEATHER_ICONS.get(cond, "🌤️"),
                    "rain_chance": day["day"].get("daily_chance_of_rain", 0),
                })
            return {"city": city, "forecast": result}
        else:
            return {"error": f"天气预报查询失败：{resp.status_code}"}
    except Exception as e:
        return {"error": f"天气预报异常：{str(e)}"}

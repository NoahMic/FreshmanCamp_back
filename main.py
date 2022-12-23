from fastapi import FastAPI

import requests as req
from bs4 import BeautifulSoup
from time import time
from random import randint

from dotenv import load_dotenv
import os 

load_dotenv()

NEWS_URL = "https://news.naver.com/"

news_res = req.get(NEWS_URL)
news_soup = BeautifulSoup(news_res.text, "html.parser")
news_data = news_soup.select(".cjs_journal_wrap")

API_KEY = os.environ.get("API_KEY")
WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/forecast'
AIR_POLLUTION_API_URL = "http://api.openweathermap.org/data/2.5/air_pollution"

one_day = 10800 * 8
now = time() // one_day * one_day

news = {"dt": now, "data" : []}
for i in news_data:
    title = i.select_one(".cjs_t").text
    contents = i.select_one(".cjs_d").text
    news["data"].append({"title": title, "contents":contents})
    
weather = {
    -1: {
        "dt": now - one_day * 2
    },
    0: {
        "dt": now - one_day
    },
    1: {
        "dt": now
    }
}


app = FastAPI()
lat = 37.564214
lng = 127.001699

@app.get("/{day}")
async def main_get(day:int):
    pollution_res = req.get(f"{AIR_POLLUTION_API_URL}?lat={lat}&lon={lng}&appid={API_KEY}").json().get("list")
    if "dt" not in weather[0].keys() or weather[0]["dt"] // one_day != time() // one_day:
        weather[-1] = weather[0]
        weather_res = req.get(f"{WEATHER_API_URL}?lat={lat}&lon={lng}&appid={API_KEY}&units=metric").json()["list"]
        weather[0] = next((item for item in weather_res if item["dt"] // one_day == weather[-1]["dt"] // one_day + 1), False)
        weather[0] = {
            "dt": weather[0]["dt"],
            "humidity": weather[0]["main"]["humidity"],
            "temp": weather[0]["main"]["temp"],
            "rain":weather[0]["pop"],
        }
        weather[1] = next((item for item in weather_res if item["dt"] // one_day == weather[0]["dt"] // one_day + 1), False)
        weather[1] = {
            "dt": weather[1]["dt"],
            "humidity": weather[1]["main"]["humidity"],
            "temp": weather[1]["main"]["temp"],
            "rain": weather[1]["pop"],
        }
    if news["dt"] // one_day != time() // one_day:
        news["dt"] = time()
        news_res = req.get(NEWS_URL)
        news_soup = BeautifulSoup(news_res.text, "html.parser")
        news_data = news_soup.select(".cjs_journal_wrap")
        for i in news_data:
            title = i.select_one(".cjs_t").text
            contents = i.select_one(".cjs_d").text
            news["data"].append({"title": title, "contents":contents})
    news_one = news["data"][randint(0, len(news["data"]))]
    return {
        **weather[day],
        "PM10": pollution_res[0]["components"]["pm10"],
        "PM2_5": pollution_res[0]["components"]["pm2_5"],
        "newsTitle": news_one["title"],
        "newsContent": news_one["contents"]
    }

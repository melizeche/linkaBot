import requests
import tweepy

from datetime import datetime
from typing import List, Dict

from config import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET

AQI_URL = "https://rald-dev.greenbeep.com/api/v1/aqi"


class AirQuality:
    def __init__(self, aqi_index, source):
        self.index = aqi_index
        self.source = source

        if self.index < 51:
            self.legend = "👍 Libre"
        elif self.index < 101:
            self.legend = "😐 Maso"
        elif self.index < 151:
            self.legend = "⚠😷️👶💔👴🤰 No tan bien"
        elif self.index < 201:
            self.legend = "⚠😷‼️ Insalubre"
        elif self.index < 301:
            self.legend = "☣️☣️☣️ Muy Insalubre"
        else:
            self.legend = "☠️☠️☠️ Peligroso"


def parse_aqi(api_response: List[Dict]) -> List:
    sensors = []
    for sensor in api_response:
        source = (
            sensor["description"]
            if sensor.get("description")
            else f"Sensor {sensor['source']}"
        )
        aq = AirQuality(aqi_index=sensor["quality"]["index"], source=source)
        sensors.append(aq)
    return sensors


def get_data() -> List:
    resp = requests.get(AQI_URL)
    return resp.json()


def build_text(aqs: list) -> str:
    updated = datetime.now().strftime("%d/%b/%Y, %H:%M")
    sensors = ""
    for aq in aqs:
        sensors += f"\n{aq.source}: {aq.index} - {aq.legend}"

    text = f"""Koa nde aire? #AireLibre
{updated}
{sensors}

Más info en airelib.re
"""
    return text


if __name__ == "__main__":
    data = parse_aqi(get_data())
    print("d", data)
    tweet = build_text(data)
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    api = tweepy.API(auth)
    api.update_status(tweet)
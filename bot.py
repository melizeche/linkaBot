import requests
import tweepy

from datetime import datetime, timedelta
from typing import List, Dict

from config import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET

AQI_URL = "https://rald-dev.greenbeep.com/api/v1/aqi"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

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

    def __repr__(self):
        return f"<{self.source}:{self.index}>"


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
    end = datetime.utcnow()
    start = end - timedelta(minutes=30)
    params = f"start={start.strftime(DATETIME_FORMAT)}&end={end.strftime(DATETIME_FORMAT)}"
    url = f"{AQI_URL}?{params}"
    print(url)
    resp = requests.get(url)
    return resp.json()


def build_text(aqs: list) -> str:
    updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    sensors = ""
    for aq in aqs:
        sensors += f"\n{aq.source}: {aq.index} - {aq.legend}"

    text = f"""Koa nde aire? #AireLibre
{updated}
{sensors}

Más info en airelib.re
"""
    return text


def send_tweet(msg: str, reply_id=None) -> str:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    api = tweepy.API(auth)
    if reply_id:
        result = api.update_status(status=msg, in_reply_to_status_id=reply_id)
    else:
        result = api.update_status(status=msg)

    return result.id


if __name__ == "__main__":
    data = parse_aqi(get_data())
    print("d", data)
    tweet = build_text(data)

    send_tweet(msg=tweet)

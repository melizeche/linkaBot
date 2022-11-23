import pickle
import requests
import tweepy

from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import List, Dict

from config import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from telegram_helper import TelegramService as ts

AQI_URL = "https://rald-dev.greenbeep.com/api/v1/aqi"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

class AirQuality:
    def __init__(self, aqi_index, source):
        self.index = aqi_index
        self.source = source

        if self.index < 51:
            self.legend = "🟢👍 Libre"
        elif self.index < 101:
            self.legend = "🟡😐 Maso"
        elif self.index < 151:
            self.legend = "🟠⚠😷️👶💔👴🤰 No tan bien"
        elif self.index < 201:
            self.legend = "🔴⚠😷‼️ Insalubre"
        elif self.index < 301:
            self.legend = "🟣☣️☣️ Muy Insalubre"
        else:
            self.legend = "🟤☠️☠️ Peligroso"

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
    try:
        with requests.Session() as s:
            retries = Retry(
                total=8,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )

            s.mount('https://', HTTPAdapter(max_retries=retries))
            resp = s.get(url)
    except Exception:
        ts.network_down()
        exit()

    if resp.status_code != 200:
        ts.network_down()
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

def chunkify(a_list: list, n: int) -> list:
    k, m = divmod(len(a_list), n)
    return (a_list[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def parse_tweets(text: str)-> list:
    parts = len(text) // 250 + 1
    if parts == 1:
        return [text]
    lines = text.splitlines()
    pre_lists = chunkify(lines, parts)
    tweets = ['\n'.join(pre_tweet) for pre_tweet in pre_lists]  # re build the tweets
    return tweets

def send_tweet(msg: str, reply_id=None) -> str:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    api = tweepy.API(auth)
    if reply_id:
        result = api.update_status(status=msg, in_reply_to_status_id=reply_id)
    else:
        result = api.update_status(status=msg)

    return result.id

def write_sensors(sensors: List[AirQuality]) -> List:
    sensor_list = [s.source for s in sensors] 
    with open("sensors.dat", "wb") as file:
        pickle.dump(sensor_list, file)
    return sensor_list

def read_file() -> List:
    sensors = None
    with open("sensors.dat", "rb") as file:
        sensors = pickle.load(file)

    return sensors

def sensor_diff(old_data, new_data):
    new_data = [s.source for s in new_data] 
    up = None  # set(new) - set(old_data)
    down = set(old_data) - set(new_data)
    if up or down:
        ts.sensor_diff(up, down)
    return up, down 



if __name__ == "__main__":
    data = parse_aqi(get_data())
    print("d", data)
    try:
        old_data = read_file()
        sensor_diff(old_data=old_data, new_data=data)
        write_sensors(data)
    except Exception as e:
        print(f"exception reading or writing sensors file: {e}")

    tweet_text = build_text(data)
    print(tweet_text)
    tweets = parse_tweets(tweet_text)
    reply_id = None
    for tweet in tweets:
        reply_id = send_tweet(msg=tweet, reply_id=reply_id)

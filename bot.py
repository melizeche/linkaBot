import pickle
import requests
import tweepy

from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import List, Dict, Tuple, Optional, Set

from config import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from screen import get_screenshot
from telegram_helper import TelegramService as ts

AQI_URL = "https://api.airelib.re/api/v1/aqi"
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
    """
    Converts API response data into a list of AirQuality objects.

    Args:
        api_response (List[Dict]): API response containing sensor data.

    Returns:
        List: A list of processed AirQuality objects.
    """
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
    """
    Fetches air quality data from the AQI API.

    Returns:
        List: JSON response from the API converted into a list of sensors.
    """
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
    """
    Generates a descriptive text summarizing air quality levels.

    Args:
        aqs (list): List of AirQuality objects.

    Returns:
        str: Text summary of sensors and their indices.
    """
    updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    sensors = ""
    for aq in aqs:
        sensors += f"\n{aq.source}: {aq.index} - {aq.legend}"

    text = f"""Calidad del Aire, mas info en: AireLib.re
{updated}

Top 👎
{sensors}
"""
    return text

def chunkify(a_list: list, n: int) -> list:
    """
    Divides a list into approximately `n` equal parts.

    Args:
        a_list (list): List to be divided.
        n (int): Number of parts to divide into.

    Returns:
        list: List of sublists.
    """
    k, m = divmod(len(a_list), n)
    return (a_list[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def parse_tweets(text: str)-> list:
    """
    Splits a long text into tweet-friendly segments.

    Args:
        text (str): Text to be split.

    Returns:
        list: List of split texts, each within Twitter's character limits.
    """
    parts = len(text) // 250 + 1
    if parts == 1:
        return [text]
    lines = text.splitlines()
    pre_lists = chunkify(lines, parts)
    tweets = ['\n'.join(pre_tweet) for pre_tweet in pre_lists]  # re build the tweets
    return tweets

def send_tweet(msg: str, images=[], alt_text=None, reply_id=None) -> str:
    """
    Sends a tweet with text, optional images, and metadata.

    Args:
        msg (str): Text content of the tweet.
        images (list): List of paths to images to attach.
        alt_text (str, optional): Alt text for the image.
        reply_id (str, optional): ID of the tweet to reply to.

    Returns:
        str: ID of the sent tweet.
    """
    client = tweepy.Client(
        consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET,
        access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
    )
    # We need to use twitter API v1.1 for media upload, this is stupid
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    api = tweepy.API(auth)
    print(images)
    media_ids = [api.simple_upload(i).media_id_string for i in images]
    if media_ids and alt_text:
        api.create_media_metadata(media_ids[0], alt_text[:1000])
    print(media_ids)
   
    if reply_id:
        result = client.create_tweet(text=msg, in_reply_to_tweet_id=reply_id,)
    else:
        result = client.create_tweet(text=msg, media_ids=media_ids)

    return result.data['id']

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

def sensor_diff(old_data: List, new_data: List) -> Tuple[Optional[Set[str]], Set[str]]:
    new_data = [s.source for s in new_data] 
    up = None  # set(new) - set(old_data)
    down = set(old_data) - set(new_data)
    if up or down:
        ts.sensor_diff(up, down)
    return up, down 



if __name__ == "__main__":
    """
    Main script for fetching air quality data and posting updates.

    Steps:
    1. Fetch and process AQI data.
    2. Detect sensor changes.
    3. Generate updates for Twitter, Mastodon, and Bluesky.
    """
    data = parse_aqi(get_data())
    ordered_data = sorted(data, key=lambda obj: obj.index, reverse=True)
    print("d", data)
    try:
        old_data = read_file()
        sensor_diff(old_data=old_data, new_data=data)
        write_sensors(data)
    except Exception as e:
        print(f"exception reading or writing sensors file: {e}")

    tweet_text_alphabetical = build_text(data)
    tweet_text = build_text(ordered_data)
    print(tweet_text)
    tweets = parse_tweets(tweet_text)
    reply_id = None
    map = get_screenshot()
    # Commenting this part because twitter API limits
    #for tweet in tweets:
    try:
        reply_id = send_tweet(msg=tweets[0], images=[map._str], alt_text=tweet_text_alphabetical, reply_id=reply_id)
    except Exception as e:
        print(f"exception sending tweet: {e}")

    try:  # Mastodon integration
        from mastodon import Mastodon
        from config import MASTODON_ACCESS_TOKEN, MASTODON_API_BASE

        mastodon = Mastodon(access_token=MASTODON_ACCESS_TOKEN, api_base_url = MASTODON_API_BASE)
        toot_text = tweet_text.replace("AireLib.re", "https://AireLib.re").replace("#AireLibre", "#AireLibre #AirQuality #AQI")

        img_dict = mastodon.media_post(media_file=map._str, description=tweet_text_alphabetical)
        mastodon.status_post(toot_text, language='es', visibility="unlisted", media_ids=img_dict)

    except Exception as e:
        print("Mastodon: ", e)
# Bluesky Integration
    try:
        from atproto import Client, client_utils
        from config import BSKY_HANDLE, BSKY_APP_PASSWORD
        client = Client()
        client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)
        with open(map._str, "rb") as f:
            img_data = f.read()
        post_text = tweets[0].replace("Calidad del Aire, mas info en: AireLib.re", "")
        post_text = client_utils.TextBuilder().text("Calidad del Aire, mas info en: ").link("AireLib.re","https://AireLib.re").text(post_text)
        client.send_image(text=post_text, image=img_data, image_alt=tweet_text_alphabetical)
    except Exception as e:
        print("Bluesky: ", e)
    

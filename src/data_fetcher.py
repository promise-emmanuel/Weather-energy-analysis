import os, requests
import yaml, json, time
import pandas as pd
import datetime
from dotenv import find_dotenv, load_dotenv
load_dotenv()

NAOO_TOKEN = os.environ["NAOO_TOKEN"]
EIA = os.getenv("EIA_KEY")



def get_cities(config_path):
    with open(config_path) as f:
        data = yaml.safe_load(f)
    city_list = data["cities"]
    return city_list

def get_weather_dates_per_city(file_path):
    df = pd.read_csv(file_path, parse_dates=["date"])
    # 2. Get last date per city
    weather_last_dates = df.groupby("city")["date"].max().to_dict()
    return weather_last_dates
        # return df["date"].max().date() + datetime.timedelta(days=1)


def get_energy_dates_per_city(file_path):    
    df = pd.read_csv(file_path, parse_dates=["period"])
    # 2. Get last date per city
    energy_last_dates = df.groupby(["city", "type"])["period"].max().to_dict()
    return energy_last_dates
    # return df["period"].max().date() + datetime.timedelta(days=1)


def get_weather_start_date(city, date_dict):
    start_date = date_dict.get(city, pd.Timestamp("2025-03-01")) + datetime.timedelta(days=1)
    return str(start_date.date())
    
    
def get_energy_start_date(city, type, date_dict):
    key = (city, type)
    start_date = date_dict.get(key, pd.Timestamp("2025-03-01")) + datetime.timedelta(days=1)
    return str(start_date.date())


def fetch_with_retry(url, headers, retries=3, delay=5):
    for attempt in range(retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response
        print(f"Attempt {attempt+1} failed. Retrying in {delay} seconds...")
        time.sleep(delay)
    response.raise_for_status()


def fetch_weather_data(station, start, end):
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
    hdr = {"token": NAOO_TOKEN}
    prm = {
        "datasetid": "GHCND",
        "stationid": station,
        "startdate": start,
        "enddate": end,
        "datatypeid": ["TMAX, TMIN"],
        "limit": 1000,
        "units": "standard"
    }
    
    for i in range(3):
        try:
            
            response = requests.get(f"{url}", headers=hdr, params=prm, timeout=300)
            response.raise_for_status()
            break # if successful, exit loop
        except requests.exceptions.HTTPError as e:
            print(f"Attempt {i+1} falied: {e}")
            time.sleep(5)
    return response.json()

def fetch_energy_data(region, types, timezone, start, end):
    
    url = "https://api.eia.gov/v2/electricity/rto/daily-region-data/data/"
    params = {
        "api_key": EIA,
        "facets[respondent][]": region,
        "facets[type][]": types, 
        # "facets[type][]": "NG",
        "facets[timezone][]": timezone,
        "start": start,
        "end": end,
        "data[]": "value",
        
    }
    for i in range(3):
        try:
            
            response = requests.get(url, params=params, timeout=300)
            response.raise_for_status()
            break # if successful, exit loop
        except requests.exceptions.HTTPError as e:
            print(f"Attempt {i+1} falied: {e}")
            time.sleep(5)
    return response.json()
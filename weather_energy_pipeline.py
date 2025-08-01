import os
from dotenv import load_dotenv
import pandas as pd
import datetime, time
# from pathlib import path

from src.data_fetcher import (
    get_weather_dates_per_city,
    get_energy_dates_per_city,
    get_cities,
    get_weather_start_date,
    get_energy_start_date,
    fetch_weather_data,
    fetch_energy_data
)


load_dotenv()
NAOO_TOKEN = os.environ["NAOO_TOKEN"]
EIA = os.getenv("EIA_KEY")


def run_pipeline():
    #step 1: determine dates
    today = str(datetime.date.today())
    
    if os.path.exists("./data/raw"):
        weather_dates_per_city = get_weather_dates_per_city("./data/raw/all_weather.csv")
        energy_dates_per_city = get_energy_dates_per_city("./data/raw/all_energy.csv")
        # print(weather_dates_per_city) #for debugging
        # print(
        # print(energy_dates_per_city)

    
    #step 2: get cities, fetch current weather data and store in csv
    if os.path.exists("./config"):
        cities = get_cities("./config/config.yaml")
    
    
    for city_info in cities:
        city = city_info["city"]
        state = city_info["state"]
        station = city_info["station"]
        
        #get start date
        start_date =  get_weather_start_date(city=city, date_dict=weather_dates_per_city)
        if start_date >= today:
            print(f"Data for {city} is up-to-date.")
            continue
        
        print(f"Fetching data for {city}...{start_date} - {today}")
        weather_result = fetch_weather_data(station=station, start=start_date, end=today)
        # print("Raw weather response:", weather_result)
    

        if weather_result and "results" in weather_result and weather_result["results"]:
            weather_df = pd.DataFrame(weather_result["results"])
            weather_df["city"] = city
            weather_df["state"] = state
            weather_df.to_csv(
                "./data/raw/all_weather.csv", 
                mode="a", 
                header=False,
                index=False
            )        
            print(f"Saved {len(weather_df)} rows for {city}. Sleeping for 10 Seconds…")
    
        else:
            print()
            print(f"⚠️ Warning: No weather data for {city}. Skipping...")
            continue
            
        
        print()
        # print("-"*50)
        time.sleep(10)
        
   
    # step 3  fetch current energy data and store in csv
    print()
    print("Retrieving energy data......")
    for city_info in cities:
        city = city_info["city"]
        state = city_info["state"]
        region = city_info["region"]
        timezone = city_info["timezone"]
        types = ["D", "NG"]
        
        for type in types:
            #get start date
            energy_start_date = get_energy_start_date(city=city, type=type, date_dict=energy_dates_per_city)
            if energy_start_date >= today:
                print(f"Data for {city} is up-to-date")
                continue
            print(f"Fetching data for {city}...{energy_start_date} - {today}")   
            energy_result = fetch_energy_data(region=region, types=type, timezone=timezone, start=energy_start_date, end=today)
    
              
            if energy_result: #and "response" in energy_result and energy_result["response"]["data"]:
                data = energy_result["response"]["data"] 
                
                energy_df = pd.DataFrame(data)
                energy_df["city"] = city
                energy_df["state"] = state
        
                # Write to CSV with mode (w) at the first loop, then (a) for subsequent loops
                energy_df.to_csv("./data/raw/all_energy.csv",
                mode = "a",
                header = False,
                index = False
                )
                print(f"Saved {len(energy_df)} - {type} rows for {city}.")   
            else:
                print(f"⚠️ Warning: {type} Energy report unavailable for {city}. Skipping...")
                continue
        
    
        print("Sleeping for 10 seconds")        
        # print()
        # time.sleep(10)
    print("Data retriever done...")

    #  now that the data has been retrieved, it is time to pivot and merge
    weather = pd.read_csv("./data/raw/all_weather.csv")
    weather["date"] = pd.to_datetime(weather["date"]).dt.date   # convert to proper date format
    weather_pivot = weather.pivot_table(
        index=["date", "city", "state"],
        columns="datatype",
        values="value"
    ).reset_index()
    
    
    energy = pd.read_csv("./data/raw/all_energy.csv")
    # # rename period to date and convert to proper date format
    energy_df = energy.rename(columns={"period":"date"})
    energy_df["date"] = pd.to_datetime(energy_df["date"]).dt.date
    energy_pivot = energy_df.pivot_table(
        index= ['date', 'respondent-name', "timezone", "city", "state", "value-units"],
        columns=["type-name"],
        values="value"
    ).reset_index()

    merged = pd.merge(weather_pivot, energy_pivot, on=["date", "city", "state"], how="inner")
    
    output_path="./data/processed/weather_energy_data.csv"
    if os.path.exists(output_path):
        os.remove(output_path)
    merged.to_csv(output_path, index=False)
        
    #     existing = pd.read_csv(output_path)
    #     existing["date"] = pd.to_datetime(existing["date"]).dt.date

    #     # Filter out already existing rows
    #     merged["date"] = pd.to_datetime(merged["date"]).dt.date
    #     merged_key = merged[["date", "city", "state"]].astype(str)
    #     existing_key = existing[["date", "city", "state"]].astype(str)

    #     # Create a mask for new rows not already in the file
    #     mask = ~merged_key.apply(tuple, axis=1).isin(existing_key.apply(tuple, axis=1))
    #     new_rows = merged[mask]

    #     # Combine and save
    #     combined = pd.concat([existing, new_rows], ignore_index=True)
    # else:
    #     combined = merged

    #     combined.to_csv(output_path, index=False)

    
    #     existing = pd.read_csv("./data/processed/weather_energy_data.csv")
    #     combined = pd.concat([existing, merged]).drop_duplicates(subset=["date", "city", "state"])
    # else:
    #     combined = merged
        
    # combined.to_csv("./data/processed/weather_energy_data.csv", index=False)
    print()
    print("completed task")
    
    
if __name__ == "__main__":
    run_pipeline()
    
    
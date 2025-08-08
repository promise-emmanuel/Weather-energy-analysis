import pandas as pd
import datetime

def missing_values(df):
    """returns the number of missing values per column and where the data is incomplete"""
    # df = pd.read_csv(csv)
    # counts = df[df.isna.sum()].to_dict()
    rows = df[df.isna().any(axis=1)]
    return rows
    # return {"counts": counts, "rows": rows}

def outliers(df):
    """Returns rows where weather or energy values are outside expected ranges.
        - TMAX > 130°F or TMIN < -50°F
        - Any energy column (Demand, Net Generation) < 0
    why: catching errors or bad API data
    """
    
    bad_weather = df[(df["TMAX"]>130.0) | (df["TMIN"]<-50.0)][["date", "city", "state", "TMAX", "TMIN"]]
    bad_energy = df[df["Demand"]<0][["date", "city", "state", "Demand", "Net generation", "value-units"]]
    if not bad_weather.empty  or not bad_energy.empty:
        return pd.concat([bad_weather, bad_energy], axis=0, ignore_index=True)
    else:
        return []
        # return f"No outliers detected"



def report_city_freshness(df, date_col="date", city_col="city"):
    """
    Flags cities without fresh data
    why: To ensure data freshness
    """


    # 1) Load and normalize
    # df = pd.read_csv(csv_path) 
    # 2) Parse date and keep just the date part
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    

    today = datetime.date.today()

    reports = []
    # 3) For each city
    for city, grp in df.groupby(city_col):

        last_date = grp[date_col].max()      # get the last date for city
        
        # if it's a datetime.datetime, convert it
        if isinstance(last_date, datetime.datetime):
            last_date = last_date.date()
        if (today - last_date).days > 1:
            
            start_missing = last_date + datetime.timedelta(days=1)
            end_missing   = today
            reports.append(
                f"{city} is missing Temperature and Energy data from {start_missing.isoformat()} to {end_missing.isoformat()}"
            )
        else:
            reports.append(f"{city} - Temeperature and Energy data is up-to-date. ({city} has data up to {last_date.isoformat()})")
    return reports

    
import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime
import yaml
# import plotly.express as px
# import statsmodels.api as sm

from src.quality_checks import (
    missing_values,
    report_city_freshness, outliers
)

from src.analysis import(
    geographic_overview,
    time_series_analysis,
    correlation_analysis,
    usage_patterns_heatmap
)

# load weather and energy data
df = pd.read_csv("./data/processed/weather_energy_data.csv")

# load cities data and store in dataframe
with open("./config/config.yaml", "r") as file:
    config = yaml.safe_load(file)
    
cities = config["cities"]
df_cities = pd.DataFrame(cities)


st.title(":blue[U.S Weather] & :red[Energy Dashboard]")


# 1. Get geographic overview

map = geographic_overview(df, df_cities)
st.pydeck_chart(map)


# 2. Time-series analysis
st.subheader("Time Series Chart")
fig = time_series_analysis(df, df_cities)
st.plotly_chart(fig, use_container_width=True)


# 3. Correlation analysis

st.subheader("Correlation")
fig = correlation_analysis(df, df_cities)
st.plotly_chart(fig, use_container_width=True)

# 4. usage pattern heatmaps
st.subheader("Usage Patterns Heatmap")
fig = usage_patterns_heatmap(df, df_cities)
st.plotly_chart(fig, use_container_width=True)

# data quality report
st.header("_Data Quality Report_")

st.subheader("Missing Values")
missing_value = missing_values(df)
st.dataframe(missing_value)

st.subheader("Outliers")
outlier = outliers(df)
st.dataframe(outlier)

st.subheader("Data Freshness")
data_freshness = report_city_freshness(df)
st.dataframe(data_freshness)




import yaml
import pandas as pd
from datetime import datetime
import streamlit as st
import pydeck as pdk

# Visualization 1 - Geographic Overview
# step 1 - show geographic location




def geographic_overview(cities):
    df_cities = pd.DataFrame(cities)

    # Streamlit page setup
    st.subheader("US Cities Interactive Map")
    st.write("Showing all cities...")

    # Define layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_cities,
        get_position="[Longitude, Latitude]",
        get_color="[200, 30, 0, 160]",
        # elevation_scale = 20,
        get_radius=100000,
        pickable=True
    )

    # Set the initial view
    view_state = pdk.ViewState(
        latitude=df_cities["Latitude"].mean(),
        longitude=df_cities["Longitude"].mean(),
        zoom=3.3,
        pitch=50
    )

    st.sidebar.subheader("Map layers")

    # Create and show chart
    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{city}, {state}"})

    return r





#  Example: Load your CSV

# # Ensure date is datetime
# df["date"] = pd.to_datetime(df["date"])

# # Compute % change from yesterday
# df["pct_change"] = ((df["today_usage"] - df["yesterday_usage"]) / df["yesterday_usage"]) * 100

# # Add coordinates for cities (hardcoded for demo)
# city_coords = {
#     "Chicago": [41.8781, -87.6298],
#     "Houston": [29.7604, -95.3698],
#     "New York": [40.7128, -74.0060],
#     "Phoenix": [33.4484, -112.0740],
#     "Seattle": [47.6062, -122.3321]
# }
# df["lat"] = df["city"].map(lambda c: city_coords[c][0])
# df["lon"] = df["city"].map(lambda c: city_coords[c][1])

# # Keep only the most recent date for each city
# latest_df = df.sort_values("date").groupby("city").tail(1)

# # Choose color scale based on usage
# def usage_color(val):
#     # Higher usage → more red; lower → more green
#     max_usage = latest_df["today_usage"].max()
#     min_usage = latest_df["today_usage"].min()
#     ratio = (val - min_usage) / (max_usage - min_usage)
#     r = int(255 * ratio)
#     g = int(255 * (1 - ratio))
#     return [r, g, 0]

# latest_df["color"] = latest_df["today_usage"].apply(usage_color)


# # Streamlit title and last updated time
# st.title("US City Energy & Weather Overview")
# last_update = latest_df["date"].max().strftime("%Y-%m-%d")
# st.caption(f"Last updated: {last_update}")

# # Create Pydeck layer
# layer = pdk.Layer(
#     "ScatterplotLayer",
#     latest_df,
#     get_position='[lon, lat]',
#     get_fill_color="color",
#     get_radius=50000,
#     pickable=True
# )

# # Set the view
# view_state = pdk.ViewState(
#     latitude=39.5,
#     longitude=-98.35,
#     zoom=4,
#     pitch=0
# )

# # Define tooltip
# tooltip = {
#     "html": "<b>{city}, {state}</b><br/>"
#             "Temp: {max_temp}°F<br/>"
#             "Energy Usage: {today_usage} MWh<br/>"
#             "Change from yesterday: {pct_change}%",
#     "style": {"backgroundColor": "steelblue", "color": "white"}
# }

# # Render in Streamlit
# st.pydeck_chart(pdk.Deck(
#     layers=[layer],
#     initial_view_state=view_state,
#     tooltip=tooltip
# ))

from webbrowser import get
import yaml
import pandas as pd
import datetime
import streamlit as st
import pydeck as pdk
import plotly.graph_objects as go
import plotly.express as px
import statsmodels.api as sm
import numpy as np

def _get_pct_change(df):
    df.sort_values(by=["city", "date"])

    # Group by city and shift Demand column
    df["Demand_yesterday"] = df.groupby("city")["Demand"].shift(1)

    # Calculate percentage change
    df["Demand_pct_change"] = round(((df["Demand"] - df["Demand_yesterday"]) / df["Demand_yesterday"]) * 100, 2)
    return df
# Optional: same for Net generation
# df["NetGen_yesterday"] = df.groupby("city")["Net generation"].shift(1)
# df["NetGen_pct_change"] = ((df["Net generation"] - df["NetGen_yesterday"]) / df["NetGen_yesterday"]) * 100

def _merge_df(df, cities):
    df_2 = cities[["city", "state", "Latitude", "Longitude"]].copy()
    merged_df = pd.merge(df, df_2, on=["city", "state"], how="inner")
    return merged_df



# Visualization 1 - 
# Function to create a geographic overview of cities
def geographic_overview(df, cities):
    merged_df = _merge_df(df, cities)
    last_date = merged_df["date"].max()
    data = _get_pct_change(merged_df)   
    
    
    # Normalize demand for color mapping
    min_demand = data["Demand"].min()
    max_demand = data["Demand"].max()
    data["color_red"] = ((data["Demand"] - min_demand) / (max_demand - min_demand) * 255).astype(int)
    data["color_green"] = (255 - data["color_red"]).astype(int)
    data["color_blue"] = 0
    data["color_alpha"] = 160
    
    
    
    st.write(f"Data last updated on: {last_date}")
    # Define layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=data,
        get_position="[Longitude, Latitude]",
        # get_color="[200, 30, 0, 160]",
        get_color="[color_red, color_green, color_blue, color_alpha,]",
        get_radius=120000,
        pickable=True
    )

    # Set the initial view
    view_state = pdk.ViewState(
        latitude=merged_df["Latitude"].mean(),
        longitude=merged_df["Longitude"].mean(),
        zoom=3,
        pitch=50
    )

    tooltip = {
    "html": "<b>{city}, {state}</b><br/>"
            "Temperature: {TMIN}°F - {TMAX}°F<br/>"
            "Energy Usage: {Demand} {value-units}<br/>"
            "% Change from yesterday: {Demand_pct_change}%",
    "style": {"backgroundColor": "steelblue", "color": "white"}
    }

    
    
    # Create and show chart
    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)

    return r



# visualization 2 - Function to create a time series analysis of energy usage and weather
def time_series_analysis(data, cities):
    """
    data, cities -> inputs you already pass (keeps your existing _merge_df usage).
    Returns a Plotly figure with:
      - TAVG (avg temp) on left axis
      - Demand on right axis
      - Weekend shading: Saturday = LightGray, Sunday = LightBlue
    """
    
    df = _merge_df(data, cities)
    
    # Ensure the 'date' column is datetime
    df["date"] = pd.to_datetime(df["date"])
    
    # dropdown for city selection
    cities = ["All Cities"] + sorted(df["city"].unique())
    selected_city = st.selectbox("Select a city", cities)
    
    # filter for city if not all cities
    if selected_city != "All Cities":
        df_filtered = df[df["city"] == selected_city].copy()
    else:
        #group by date and average_values
        df_filtered = df.groupby("date", as_index=False).agg({
            "TAVG": "mean",
            "Demand": "mean"
        })
    
    
    # calculate the date 90 days ago from today
    last_date = df_filtered["date"].max()
    ninety_days_ago = last_date - datetime.timedelta(days=90)
    df_recent = df_filtered[df_filtered["date"] >= ninety_days_ago].sort_values("date")
    
    
    if df_recent.empty:
        st.warning("No data available for the selected city / date range.")
        return go.Figure()
    
    
    # create a plotly figure
    fig = go.Figure()
    
    # add temperature trace (left side)
    fig.add_trace(go.Scatter(
        x=df_recent["date"],
        y=df_recent["TAVG"],
        name="Average Daily Temperature (°F)",
        # mode="lines+markers",
        mode="lines",
        line=dict(color='firebrick', width=2),
        yaxis="y1"
    ))
    
    # add Energy demand trace (right axis)
    fig.add_trace(go.Scatter(
        x=df_recent["date"],
        y=df_recent["Demand"],
        name="Energy Demand",
        # mode="lines+markers",
        mode="lines",
        line=dict(color='royalblue', width=2, dash="dot"), 
        yaxis="y2"
    ))
    
     # 🔹 Weekend shading: Loop through dates and add rectangles for Sat/Sun
    for date in pd.date_range(df_recent["date"].min(), df_recent["date"].max()):
        weekday = date.weekday()
        
        if weekday == 5:
            fillcolor = "LightGray"
            opacity= 0.25
        elif weekday == 6:
            fillcolor="LightBlue"
            opacity = 0.18
        else:
            continue 
            
        fig.add_shape(
            type="rect",
            x0=date,  
            x1=date + datetime.timedelta(days=1),
            y0=0, y1=1,  # Normalized coordinates for full height
            xref="x",
            yref="paper",  # "paper" means relative to chart height
            fillcolor=fillcolor,
            opacity=opacity,
            layer="below",
            line_width=0
            )
    
    
    
    fig.update_layout(
        title=f"Temperature vs Energy Demand (Last 90 Days) - {selected_city}",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Temperature (°F)", side="left"),
        yaxis2=dict(title="Energy Demand (MWh)", side="right", overlaying="y"),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0)"),
        template="plotly_white",
        hovermode="x unified"
    )
    
    return fig

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import statsmodels.api as sm

def correlation_analysis(data, cities):
    # Merge data with city info
    df = _merge_df(data, cities)
    df["date"] = pd.to_datetime(df["date"])
    
    # Dropdown: city selection
    city_options = ["All Cities"] + sorted(df["city"].unique())
    selected_city = st.selectbox("Select a city for correlation analysis", city_options)
    
    if selected_city != "All Cities":
        df_filtered = df[df["city"] == selected_city]
    else:
        df_filtered = df.copy()
    
    # X = Temperature, Y = Energy Demand
    X = df_filtered["TAVG"]
    y = df_filtered["Demand"]
    
    # Regression model
    X_with_const = sm.add_constant(X)  # adds intercept term
    model = sm.OLS(y, X_with_const).fit()
    
    slope = model.params["TAVG"]
    intercept = model.params["const"]
    r_squared = model.rsquared
    corr_coef = np.corrcoef(X, y)[0, 1]
    
    # Regression line values
    x_vals = np.linspace(X.min(), X.max(), 100)
    y_pred = intercept + slope * x_vals
    
    # Scatter plot with city colors
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_filtered["TAVG"],
        y=df_filtered["Demand"],
        mode="markers",
        marker=dict(
            size=7,
            color=df_filtered["city"].astype('category').cat.codes,
            colorscale="Viridis",
            showscale=True
        ),
        text=df_filtered.apply(lambda row: f"{row['city']}, {row['state']}<br>Date: {row['date'].date()}<br>TAVG: {row['TAVG']}°F<br>Demand: {row['Demand']} MWh", axis=1),
        hoverinfo="text",
        name="Data Points"
    ))
    
    # Add regression line
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_pred,
        mode="lines",
        line=dict(color="red", width=2),
        name=f"Regression Line: y = {intercept:.2f} + {slope:.2f}x"
    ))
    
    # Layout
    fig.update_layout(
        title=f"Temperature vs Energy Demand - {selected_city}",
        xaxis_title="Average Temperature (°F)",
        yaxis_title="Energy Demand (MWh)",
        template="plotly_white",
        legend=dict(x=0.01, y=0.99)
    )
    
    # Show stats
    st.write(f"**Slope:** {slope:.2f}  |  **Intercept:** {intercept:.2f}")
    st.write(f"**R²:** {r_squared:.3f}  |  **Correlation (r):** {corr_coef:.3f}")
    
    return fig




def usage_patterns_heatmap(data, cities):
    # Merge datasets
    df = _merge_df(data, cities)
    df["date"] = pd.to_datetime(df["date"])
    
    # Dropdown for city
    city_options = ["All Cities"] + sorted(df["city"].unique())
    selected_city = st.selectbox("Select a city for heatmap", city_options)
    
    if selected_city != "All Cities":
        df_filtered = df[df["city"] == selected_city]
    else:
        df_filtered = df.copy()
    
    # Create temperature bins
    temp_bins = [-float("inf"), 50, 60, 70, 80, 90, float("inf")]
    temp_labels = ["<50°F", "50-60°F", "60-70°F", "70-80°F", "80-90°F", ">90°F"]
    df_filtered["TempRange"] = pd.cut(df_filtered["TAVG"], bins=temp_bins, labels=temp_labels)
    
    # Extract day of week
    df_filtered["DayOfWeek"] = df_filtered["date"].dt.day_name()
    
    # Group and calculate average demand
    heatmap_data = df_filtered.groupby(["TempRange", "DayOfWeek"])["Demand"].mean().reset_index()
    
    # Pivot for heatmap
    heatmap_pivot = heatmap_data.pivot(index="TempRange", columns="DayOfWeek", values="Demand")
    
    # Ensure consistent day order
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap_pivot = heatmap_pivot[day_order]
    
    # Plotly heatmap
    fig = px.imshow(
        heatmap_pivot,
        color_continuous_scale="RdBu_r",
        aspect="auto",
        labels=dict(color="Avg Energy Demand (MWh)"),
        text_auto=".1f"  # show demand values in each cell
    )
    
    fig.update_layout(
        title=f"Usage Patterns by Temperature & Day of Week - {selected_city}",
        xaxis_title="Day of Week",
        yaxis_title="Temperature Range",
        coloraxis_colorbar=dict(title="Avg Energy Demand (MWh)")
    )
    
    return fig




# def correlation_analysis(data, cities):
    # Merge data and ensure correct types
    # df = _merge_df(data, cities)
    # df["date"] = pd.to_datetime(df["date"])

    # # Keep only necessary columns
    # df = df[["city", "TAVG", "Demand", "date"]].dropna()

    # # Regression model
    # X = df["TAVG"]
    # y = df["Demand"]
    # X_with_const = sm.add_constant(X)  # Adds intercept term
    # model = sm.OLS(y, X_with_const).fit()

    # # Extract regression stats
    # slope = model.params["TAVG"]
    # intercept = model.params["const"]
    # r_squared = model.rsquared
    # corr_coef = np.corrcoef(df["TAVG"], df["Demand"])[0, 1]

    # # Create regression line points
    # x_range = np.linspace(df["TAVG"].min(), df["TAVG"].max(), 100)
    # y_pred = intercept + slope * x_range

    # # Scatter plot with Plotly
    # fig = px.scatter(
    #     df,
    #     x="TAVG",
    #     y="Demand",
    #     color="city",
    #     hover_data={"date": True, "TAVG": True, "Demand": True}
    # )

    # # Add regression line
    # fig.add_scatter(
    #     x=x_range,
    #     y=y_pred,
    #     mode="lines",
    #     name="Regression Line",
    #     line=dict(color="white", width=2)
    # )

    # # Add equation and R² in layout
    # fig.update_layout(
    #     title=(
    #         f"Temperature vs Energy Demand<br>"
    #         f"y = {intercept:.2f} + {slope:.2f}x, "
    #         f"R² = {r_squared:.3f}, r = {corr_coef:.3f}"
    #     ),
    #     xaxis_title="Average Temperature (°F)",
    #     yaxis_title="Energy Demand (MWh)",
    #     legend_title="City",
    #     template="plotly_white"
    # )

    # return fig




# st.sidebar.subheader("Map layers")


#  Example: Load your CSV

# # Ensure date is datetime
# df["date"] = pd.to_datetime(df["date"])

# # Compute % change from yesterday
# df["pct_change"] = ((df["today_usage"] - df["yesterday_usage"]) / df["yesterday_usage"]) * 100

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
    # "html": "<b>{city}, {state}</b><br/>"
            # "Temp: {max_temp}°F<br/>"
            # "Energy Usage: {today_usage} MWh<br/>"
            # "Change from yesterday: {pct_change}%",
    # "style": {"backgroundColor": "steelblue", "color": "white"}
# }



# # Render in Streamlit
# st.pydeck_chart(pdk.Deck(
#     layers=[layer],
#     initial_view_state=view_state,
#     tooltip=tooltip
# ))

# def time_series_3d(data, cities):
#     # Merge and prepare the data
#     df = _merge_df(data, cities)
#     df["date"] = pd.to_datetime(df["date"])
    
#     # Dropdown city selector
#     city_options = ["All Cities"] + sorted(df["city"].unique())
#     selected_city = st.selectbox("Select a city for 3D view", city_options)
    
#     if selected_city != "All Cities":
#         df_filtered = df[df["city"] == selected_city]
#     else:
#         df_filtered = (
#             df.groupby("date", as_index=False)
#               .agg({"TAVG": "mean", "Demand": "mean"})
#         )
    
#     # Last 90 days
#     ninety_days_ago = df["date"].max() - datetime.timedelta(days=90)
#     df_recent = df_filtered[df_filtered["date"] >= ninety_days_ago]
    
#     # Create 3D scatter/line plot
#     fig = go.Figure(data=[go.Scatter3d(
#         x=df_recent["date"],          # X-axis: time
#         y=df_recent["TAVG"],          # Y-axis: temperature
#         z=df_recent["Demand"],        # Z-axis: energy demand
#         mode='lines+markers',
#         marker=dict(
#             size=4,
#             color=df_recent["Demand"],  # Color by demand
#             colorscale='Viridis',
#             opacity=0.8
#         ),
#         line=dict(color='royalblue', width=2)
#     )])
    
#     fig.update_layout(
#         scene=dict(
#             xaxis_title='Date',
#             yaxis_title='Temperature (°F)',
#             zaxis_title='Energy Demand (MWh)',
#             xaxis=dict(type='date')
#         ),
#         title=f"3D Time Series: Temperature vs Demand ({selected_city})",
#         template="plotly_white"
#     )
    
#     return fig


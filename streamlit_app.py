import streamlit as st
import folium
import re
from streamlit_folium import st_folium
from datetime import datetime, timedelta, date
from meteostat import Point, Hourly
from zoneinfo import ZoneInfo
from astral.sun import sun
from astral import LocationInfo
import os


# Load location data
locations_file = os.path.join('data', 'locations.json')
try:
    with open(locations_file, 'r') as f:
        locations = json.load(f)
except FileNotFoundError:
    st.error(f"Location file not found at {locations_file}")
    locations = []


# Streamlit app title
st.title('Chicagoland Area Tennis Courts')

# Create a Folium map
#m = folium.Map(location=[41.8781, -87.6298], zoom_start=10)

# Add markers to the map
#for location in locations:
#    folium.Marker(
#        [location['latitude'], location['longitude']],
#        popup=location['name']
#    ).add_to(m)

# Display the map in the Streamlit app
#st_folium(m, width=700, height=500)

# 1️⃣ Add a text input for regex searches
search_term = st.text_input(
    "🔍 Search parks by name or address:",
    value="",
    placeholder="e.g. Lincoln or Englewood"
)

# 2️⃣ Compile regex and filter your list
if search_term:
    try:
        pattern = re.compile(search_term, re.IGNORECASE)
        filtered = [
            loc for loc in locations
            if pattern.search(loc['name']) or pattern.search(loc['address'])
        ]
    except re.error:
        st.error("Invalid pattern.")
        filtered = []
else:
    filtered = locations

st.write(f"Showing {len(filtered)} of {len(locations)} locations")

# 3️⃣ Build the map and add only filtered markers
m = folium.Map(location=[41.8781, -87.6298], zoom_start=10)
for loc in filtered:
    folium.Marker(
        [loc['latitude'], loc['longitude']],
        popup=(
            f"<b>Park Name:</b> {loc['name']}<br>"
            f"<b>Address:</b> {loc['address']}<br>"
            f"<b>Court Count:</b> {loc['count']}"
        ),
        tooltip=loc['name']
    ).add_to(m)

# 4️⃣ Render in Streamlit
st_folium(m, width=700, height=500)

# ------------- List View -------------
header = "Location List"
st.markdown(f"## {header}")
st.write(f"Showing {len(filtered)} of {len(locations)} locations")

if st.button("🌦️ Check Weather"):
    # Time range (use UTC for Meteostat)
    end = datetime.utcnow()
    start = end - timedelta(hours=1)
    

    for loc in filtered:
        # Create Point
        point = Point(loc["latitude"], loc["longitude"])
        
        # Fetch weather
        try:
            weather = Hourly(point, start, end).fetch()
            latest = weather.tail(1)

            if latest.empty:
                st.write(f"**{loc['name']}**")
                st.write("Weather data unavailable.")
                st.write("---")
                continue

            temp_c = latest['temp'].values[0]
            temp_f = (temp_c * 9/5) + 32
            rhum = latest['rhum'].values[0]
            prcp = latest['prcp'].values[0]

            # Infer condition
            if prcp > 0:
                condition = "Rainy"
            elif rhum > 85:
                condition = "Cloudy or foggy"
            else:
                condition = "Likely clear or partly cloudy"

            historical_end = datetime.utcnow()
            historical_start = end - timedelta(hours=12)

            # Fetch hourly weather data
            historical_data = Hourly(point, historical_start, historical_end).fetch()

            # Check total precipitation
            total_precip_mm = historical_data['prcp'].sum()

            # Check if any rain occurred
            if total_precip_mm > 0:
                print(f"Yes, it rained in the last 12 hours. Total: {total_precip_mm:.2f} mm. The court may be wet.")
                #print(historical_data[historical_data['prcp'] > 0][['prcp']])  # Show hours when it rained
            else:
                print("No rain recorded in the last 12 hours.")

            #Display court info
            st.write("**" + "Park Name: " + loc['name'] + "**")
            st.write("Address: " + loc['address'])
            st.write(f"*Court Count:* {loc['count']} • *Type:* {loc['facility_type']}")
            # Display weather info
            st.write("**" + "Weather Report for " + loc['name'] + "**")
            st.write(f"🌡️ Temperature: {temp_f:.1f}°F")
            st.write(f"💧 Humidity: {rhum}%")
            st.write(f"🌤️ Condition: {condition}")
            st.write("**Court Wetness Check:**")
            if total_precip_mm > 0:
                st.write(f"It rained {total_precip_mm:.2f} mm in the last 12 hours. The court may be wet.")
                #print(historical_data[historical_data['prcp'] > 0][['prcp']])  # Show hours when it rained
            else:
                st.write("No rain recorded in the last 12 hours.")
            st.write("---")
        except Exception as e:
            st.write(f"Error fetching weather for {loc['name']}: {e}")
            st.write("---")

## show the results in a list view

timezone = "America/Chicago"

for loc in filtered:
    location = LocationInfo(timezone=timezone,
                        latitude=loc["latitude"], longitude=loc["longitude"]) 
    # Get today's sun times
    sun_times = sun(location.observer, date=date.today(), tzinfo=ZoneInfo(timezone))
    sunset = sun_times['sunset']

    # Get current time in local timezone
    now = datetime.now(ZoneInfo(timezone))

    # Compute daylight remaining
    

    st.write("**" + "Park Name: " + loc['name'] + "**")
    st.write("Address: " + loc['address'])
    st.write(f"*Court Count:* {loc['count']} • *Type:* {loc['facility_type']}")
    if now < sunset:
        remaining = sunset - now
        hours, remainder = divmod(remaining.total_seconds(), 3600)
        minutes = remainder // 60
        st.write(f"🌅 Sunset at: {sunset.strftime('%I:%M %p')}")
        st.write(f"🌞 Daylight remaining: {int(hours)}h {int(minutes)}m")
    else:
        st.write(f"Sun has already set at: {sunset.strftime('%I:%M %p')}")
    st.write("---")

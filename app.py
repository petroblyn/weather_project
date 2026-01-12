# ----------------------------
# Matplotlib setup (CRITICAL)
# ----------------------------
import matplotlib
matplotlib.use("Agg")

# ----------------------------
# Imports
# ----------------------------
from flask import Flask, render_template, request
from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime

# ----------------------------
# Flask App
# ----------------------------
app = Flask(__name__)

# ----------------------------
# Configuration
# ----------------------------
DB_URL = "postgresql+psycopg2://weather_user:weather_pass@localhost:5432/weather_db"

API_KEY = "0c95b98a72641aa24f0cf692ae8e683d"
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"

# ----------------------------
# Helper Functions
# ----------------------------
def fetch_and_store_city(city):
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(WEATHER_URL, params=params)
    if response.status_code != 200:
        return None

    data = response.json()

    engine = create_engine(DB_URL)

    df = pd.DataFrame([{
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "condition": data["weather"][0]["description"]
    }])

    df.to_sql("weather", engine, if_exists="append", index=False)

    return data


def fetch_hourly_forecast(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
        "exclude": "daily,minutely,alerts"
    }

    response = requests.get(ONECALL_URL, params=params)
    if response.status_code != 200:
        return None

    return response.json()["hourly"][:12]


def store_hourly_forecast(city, hourly_data):
    engine = create_engine(DB_URL)

    rows = []
    for hour in hourly_data:
        rows.append({
            "city": city,
            "hour": datetime.fromtimestamp(hour["dt"]),
            "temperature": hour["temp"],
            "condition": hour["weather"][0]["description"]
        })

    df = pd.DataFrame(rows)
    df.to_sql("hourly_weather", engine, if_exists="append", index=False)


# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    searched_city = request.args.get("city")
    engine = create_engine(DB_URL)

    if not searched_city:
        query = """
        SELECT city, temperature, humidity, condition, created_at
        FROM weather
        ORDER BY created_at DESC
        LIMIT 1;
        """
        df = pd.read_sql(query, engine)
    else:
        query = """
        SELECT city, temperature, humidity, condition, created_at
        FROM weather
        WHERE LOWER(city) = LOWER(%s)
        ORDER BY created_at ASC;
        """
        df = pd.read_sql(query, engine, params=(searched_city,))

        if df.empty:
            api_data = fetch_and_store_city(searched_city)
            if not api_data:
                return render_template(
                    "index.html",
                    error=f"City '{searched_city}' not found."
                )

            df = pd.read_sql(query, engine, params=(searched_city,))
            lat = api_data["coord"]["lat"]
            lon = api_data["coord"]["lon"]
        else:
            params = {
                "q": searched_city,
                "appid": API_KEY,
                "units": "metric"
            }
            api_data = requests.get(WEATHER_URL, params=params).json()
            lat = api_data["coord"]["lat"]
            lon = api_data["coord"]["lon"]

        hourly = fetch_hourly_forecast(lat, lon)
        if hourly:
            store_hourly_forecast(searched_city, hourly)

    if df.empty:
        return render_template("index.html", error="No weather data available.")

    os.makedirs("static", exist_ok=True)

    city_name = df.iloc[0]["city"]
    latest = df.iloc[-1]

    # Temperature chart
    plt.figure()
    plt.plot(df["created_at"], df["temperature"])
    plt.title(f"Temperature Trend - {city_name}")
    plt.xlabel("Time")
    plt.ylabel("Temperature (°C)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/temp.png")
    plt.close()

    # Humidity chart
    plt.figure()
    plt.plot(df["created_at"], df["humidity"])
    plt.title(f"Humidity Trend - {city_name}")
    plt.xlabel("Time")
    plt.ylabel("Humidity (%)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/humidity.png")
    plt.close()

    hourly_df = pd.read_sql(
        """
        SELECT hour, temperature
        FROM hourly_weather
        WHERE LOWER(city) = LOWER(%s)
        ORDER BY hour ASC
        LIMIT 12;
        """,
        engine,
        params=(city_name,)
    )

    plt.figure()
    plt.plot(hourly_df["hour"], hourly_df["temperature"])
    plt.title(f"Next 12 Hours - {city_name}")
    plt.xlabel("Hour")
    plt.ylabel("Temperature (°C)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/hourly_temp.png")
    plt.close()

    return render_template(
        "index.html",
        city=latest["city"],
        temp=latest["temperature"],
        humidity=latest["humidity"],
        condition=latest["condition"]
    )


# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)

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
import matplotlib.dates as mdates

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
ONECALL_URL_V2 = "https://api.openweathermap.org/data/2.5/onecall"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

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
        # If One Call 3.0 is not available (requires subscription) or the key is restricted,
        # try One Call v2.5 first, then fall back to the 3-hour forecast endpoint.
        if response.status_code == 401:
            try:
                response2 = requests.get(ONECALL_URL_V2, params=params)
                if response2.status_code == 200:
                    return response2.json().get("hourly", [])[:12]
            except Exception:
                pass

        # As a final fallback, use the 3-hour `forecast` endpoint and approximate the next 12 hours
        try:
            resp_f = requests.get(FORECAST_URL, params={"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"})
            if resp_f.status_code == 200:
                data = resp_f.json().get("list", [])
                # take enough 3-hour entries to cover ~12 hours (4 entries)
                selected = data[:4]
                hourly_like = []
                for item in selected:
                    hourly_like.append({
                        "dt": item.get("dt"),
                        "temp": item.get("main", {}).get("temp"),
                        "weather": [{"description": item.get("weather", [{}])[0].get("description")}]
                    })
                return hourly_like
        except Exception:
            pass

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

    # Temperature chart - show previous hours
    # Ensure created_at is parsed as datetime
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values("created_at")

    # Prefer entries from the last 10 hours; if none, use the last 10 entries
    try:
        from datetime import timedelta
        now = datetime.now(df["created_at"].dt.tz) if df["created_at"].dt.tz is not None else datetime.now()
        cutoff = now - timedelta(hours=10)
        recent = df[df["created_at"] >= cutoff]
    except Exception:
        recent = pd.DataFrame()

    if recent.empty:
        temp_df = df.tail(10)
    else:
        temp_df = recent

    # Resample to an hourly series covering the last 10 hours and interpolate missing points
    try:
        # create an hourly index from cutoff to now
        from datetime import timedelta
        now = datetime.now(temp_df["created_at"].dt.tz) if temp_df["created_at"].dt.tz is not None else datetime.now()
        start = now - timedelta(hours=10)

        # set index and resample
        temp_idx = temp_df.set_index("created_at").sort_index()
        # resample to hourly frequency and take the mean of any points within the hour
        hourly_series = temp_idx["temperature"].resample('H').mean()

        # ensure the series covers the full desired range (start .. now)
        full_index = pd.date_range(start=start.replace(minute=0, second=0, microsecond=0), end=now, freq='H')
        hourly_series = hourly_series.reindex(full_index)

        # interpolate missing values using time interpolation
        hourly_series = hourly_series.interpolate(method='time', limit_direction='both')

        plt.figure()
        plt.plot(hourly_series.index, hourly_series.values, marker='o', linestyle='-')

        # overlay original recorded points (if any) as dots
        if not temp_df.empty:
            plt.scatter(temp_df['created_at'], temp_df['temperature'], color='orange', zorder=5)

        plt.title(f"Temperature Trend - {city_name} (last 10 hours)")
        plt.xlabel("Time")
        plt.ylabel("Temperature (°C)")

        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("static/temp.png")
        plt.close()
    except Exception:
        # fallback: plot raw points if something goes wrong
        plt.figure()
        plt.plot(temp_df["created_at"], temp_df["temperature"], marker="o")
        plt.title(f"Temperature Trend - {city_name}")
        plt.xlabel("Time")
        plt.ylabel("Temperature (°C)")
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("static/temp.png")
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

    # Ensure 'hour' column is parsed as datetimes for plotting
    if hourly_df.empty:
        # create a placeholder image when no hourly data is available
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, "No hourly data available", ha="center", va="center")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig("static/hourly_temp.png")
        plt.close()
    else:
        hourly_df["hour"] = pd.to_datetime(hourly_df["hour"])

        plt.figure()
        plt.plot(hourly_df["hour"], hourly_df["temperature"], marker="o")
        plt.title(f"Next 12 Hours - {city_name}")
        plt.xlabel("Hour")
        plt.ylabel("Temperature (°C)")

        # format x-axis to show hour:minute labels
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator())
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

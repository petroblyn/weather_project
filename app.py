import requests

API_KEY = "0c95b98a72641aa24f0cf692ae8e683d"
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"


# ----------------------------
# Matplotlib setup (IMPORTANT)
# ----------------------------
import matplotlib
matplotlib.use("Agg")  # Non-GUI backend for Flask

# ----------------------------
# Imports
# ----------------------------
from flask import Flask, render_template, request
from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt
import os

def fetch_and_store_city(city):
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(WEATHER_URL, params=params)

    if response.status_code != 200:
        return False

    data = response.json()

    engine = create_engine(DB_URL)

    query = """
    INSERT INTO weather (city, temperature, humidity, condition)
    VALUES (%s, %s, %s, %s)
    """

    df = pd.DataFrame([{
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "condition": data["weather"][0]["description"]
    }])

    df.to_sql("weather", engine, if_exists="append", index=False)

    return True


# ----------------------------
# Flask App
# ----------------------------
app = Flask(__name__)

# ----------------------------
# Database Configuration
# ----------------------------
DB_URL = "postgresql+psycopg2://weather_user:weather_pass@localhost:5432/weather_db"

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    searched_city = request.args.get("city")

    engine = create_engine(DB_URL)

    # If no city searched, show most recent record
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

    if df.empty and searched_city:
        fetched = fetch_and_store_city(searched_city)

        if not fetched:
            return render_template(
                "index.html",
                error=f"City '{searched_city}' not found in weather API."
        )

        # Re-run query after fetching
        df = pd.read_sql(query, engine, params=(searched_city,))


    # Ensure static folder exists
    os.makedirs("static", exist_ok=True)

    city_name = df.iloc[0]["city"]

    # ----------------------------
    # Temperature Chart
    # ----------------------------
    plt.figure()
    plt.plot(df["created_at"], df["temperature"])
    plt.title(f"Temperature Trend - {city_name}")
    plt.xlabel("Time")
    plt.ylabel("Temperature (°C)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/temp.png")
    plt.close()

    # ----------------------------
    # Humidity Chart
    # ----------------------------
    plt.figure()
    plt.plot(df["created_at"], df["humidity"])
    plt.title(f"Humidity Trend - {city_name}")
    plt.xlabel("Time")
    plt.ylabel("Humidity (%)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/humidity.png")
    plt.close()

    latest = df.iloc[-1]

    return render_template(
        "index.html",
        city=latest["city"],
        temp=latest["temperature"],
        humidity=latest["humidity"],
        condition=latest["condition"]
    )

# ----------------------------
# App Entry Point
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

DB_CONFIG = {
    "dbname": "weather_db",
    "user": "weather_user",
    "password": "weather_pass",
    "host": "localhost",
    "port": 5432
}

@app.route("/")
def index():
    selected_city = request.args.get("city")

    conn = psycopg2.connect(**DB_CONFIG)

    # Get list of cities for dropdown
    cities_query = "SELECT DISTINCT city FROM weather ORDER BY city;"
    cities = pd.read_sql(cities_query, conn)["city"].tolist()

    if not selected_city and cities:
        selected_city = cities[0]

    query = """
    SELECT city, temperature, humidity, condition, created_at
    FROM weather
    WHERE city = %s
    ORDER BY created_at ASC;
    """

    df = pd.read_sql(query, conn, params=(selected_city,))
    conn.close()

    if df.empty:
        return "No weather data found for this city."

    os.makedirs("static", exist_ok=True)

    # Temperature chart
    plt.figure()
    plt.plot(df["created_at"], df["temperature"])
    plt.title(f"Temperature Trend - {selected_city}")
    plt.xlabel("Time")
    plt.ylabel("Temperature (°C)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/temp.png")
    plt.close()

    # Humidity chart
    plt.figure()
    plt.plot(df["created_at"], df["humidity"])
    plt.title(f"Humidity Trend - {selected_city}")
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
        condition=latest["condition"],
        cities=cities,
        selected_city=selected_city
    )

if __name__ == "__main__":
    app.run(debug=True)

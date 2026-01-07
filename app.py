from flask import Flask, render_template
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
    conn = psycopg2.connect(**DB_CONFIG)

    query = """
    SELECT city, temperature, humidity, condition, created_at
    FROM weather
    ORDER BY created_at ASC;
    """

    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        return "No weather data found. Run weather_fetch.py first."

    # Create charts folder
    os.makedirs("static", exist_ok=True)

    # Temperature chart
    plt.figure()
    plt.plot(df["created_at"], df["temperature"])
    plt.title("Temperature Trend")
    plt.xlabel("Time")
    plt.ylabel("Temperature (°C)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/temp.png")
    plt.close()

    # Humidity chart
    plt.figure()
    plt.plot(df["created_at"], df["humidity"])
    plt.title("Humidity Trend")
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

if __name__ == "__main__":
    app.run(debug=True)






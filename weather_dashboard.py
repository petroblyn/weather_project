import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

# Database config
DB_CONFIG = {
    "dbname": "weather_db",
    "user": "weather_user",
    "password": "weather_pass",
    "host": "localhost",
    "port": 5432
}

# Connect to DB
conn = psycopg2.connect(**DB_CONFIG)

# Load data into pandas DataFrame
query = """
SELECT city, temperature, humidity, created_at
FROM weather
ORDER BY created_at ASC;
"""

df = pd.read_sql(query, conn)
conn.close()

if df.empty:
    print("No data found in database. Run weather_fetch.py first.")
    exit()

# Plot temperature
plt.figure()
plt.plot(df["created_at"], df["temperature"])
plt.title("Temperature Trend")
plt.xlabel("Time")
plt.ylabel("Temperature (°C)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Plot humidity
plt.figure()
plt.plot(df["created_at"], df["humidity"])
plt.title("Humidity Trend")
plt.xlabel("Time")
plt.ylabel("Humidity (%)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

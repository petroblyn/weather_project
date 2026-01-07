import requests
import psycopg2

# --------------------
# API CONFIG
# --------------------
API_KEY = "0c95b98a72641aa24f0cf692ae8e683d"
CITY = "Johannesburg"
URL = "http://api.openweathermap.org/data/2.5/weather"

# --------------------
# DATABASE CONFIG
# --------------------
DB_CONFIG = {
    "dbname": "weather_db",
    "user": "weather_user",
    "password": "weather_pass",
    "host": "localhost",
    "port": 5432
}

# --------------------
# API REQUEST
# --------------------
params = {
    "q": CITY,
    "appid": API_KEY,
    "units": "metric"
}

response = requests.get(URL, params=params)

if response.status_code != 200:
    print("Error fetching weather data:", response.text)
    exit(1)

data = response.json()

weather = {
    "city": data["name"],
    "temperature": data["main"]["temp"],
    "humidity": data["main"]["humidity"],
    "condition": data["weather"][0]["description"]
}

print("Fetched weather:", weather)

# --------------------
# DATABASE INSERT
# --------------------
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO weather (city, temperature, humidity, condition)
    VALUES (%s, %s, %s, %s)
    """,
    (
        weather["city"],
        weather["temperature"],
        weather["humidity"],
        weather["condition"]
    )
)

conn.commit()
cursor.close()
conn.close()

print("Weather data successfully stored in database.")

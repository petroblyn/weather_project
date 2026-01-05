import requests

API_KEY = "0c95b98a72641aa24f0cf692ae8e683d"
CITY = "Johannesburg"
URL = "http://api.openweathermap.org/data/2.5/weather"

params = {
    "q": CITY,
    "appid": API_KEY,
    "units": "metric"
}

response = requests.get(URL, params=params)

if response.status_code == 200:
    data = response.json()
    weather = {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "condition": data["weather"][0]["description"]
    }
    print(weather)
else:
    print("Error fetching weather data")

    
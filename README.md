# weather_project

This is a small Flask-based weather dashboard that fetches data from OpenWeatherMap and stores it in a local PostgreSQL database. The app renders historical temperature/humidity charts and a 12-hour forecast.

## Contents

- `app.py` - Flask web app (entry point)
- `weather_fetch.py` - small script to fetch a single city's current weather and insert into the database (handy to seed data)
- `weather_dashboard.py` - standalone script to plot DB data with matplotlib
- `sql/create_tables.sql` - helper SQL to create the role, database, and tables
- `requirements.txt` - pinned Python dependencies
- `templates/` and `static/` - Flask template and generated images

## Prerequisites

- Python 3.8+ installed
- PostgreSQL server installed and running on the host (default expects localhost:5432)
- Access to a PostgreSQL superuser account (to create the database/role) — typically the `postgres` OS user

## Quick start (copyable commands)

1) Create the database role, database and tables

From the project root run the SQL script as the `postgres` OS user:

```bash
sudo -u postgres psql -f sql/create_tables.sql
```

That script will:
- create role `weather_user` with password `weather_pass` (if missing)
- create database `weather_db` owned by `weather_user` (if missing)
- create the tables `weather` and `hourly_weather`

If you prefer to run commands manually, you can instead run equivalent psql commands interactively as the `postgres` user.

2) Create a Python virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3) (Optional) Seed initial weather data

The small script `weather_fetch.py` will fetch weather for the hard-coded city `Viljoenskroon` and insert it into the DB. Run it once to seed a record:

```bash
# with venv active
python weather_fetch.py
```

Expected output: a printed weather JSON summary and confirmation that the data was stored in the database.

4) Run the Flask app

```bash
# with venv active
python app.py
```

Open http://127.0.0.1:5000 in your browser. Use the search box to request weather for a city. The app will call the OpenWeatherMap API, store results in the DB, and generate `static/*.png` charts.

## Configuration notes

- API key: The code currently contains a hard-coded OpenWeatherMap API key in `app.py` and `weather_fetch.py`. For local development you can keep it, but for production move it into an environment variable. Example change in code:

```python
API_KEY = os.environ.get("OPENWEATHER_API_KEY")
```

Then run the app with:

```bash
export OPENWEATHER_API_KEY="your_key_here"
python app.py
```

- Database connection: `app.py` uses SQLAlchemy with the connection string assigned to `DB_URL`. If your Postgres host/credentials differ, update `DB_URL` at the top of `app.py` (or read it from an env var).

## Troubleshooting

- psycopg2 installation errors: If pip installing `psycopg2-binary` fails, install your system's PostgreSQL development headers first (Debian/Ubuntu: `sudo apt-get install libpq-dev`).
- API errors (401/403): Replace the hard-coded API key with your own OpenWeatherMap key.
- No data shown: Run `weather_fetch.py` to seed the DB, or search for a city in the app which will fetch and store it automatically.

## Files added by maintainers

- `requirements.txt` — dependency pins to install with pip
- `sql/create_tables.sql` — helper SQL to create DB and tables

## Next improvements (optional)

- Move API keys and DB URLs into environment variables (I can update the code for you)
- Provide a `docker-compose.yml` to run Postgres + the app together
- Add a small Makefile for common tasks

---

If you want, I can implement any of the optional improvements (move keys to env vars, create Docker Compose, or add a Makefile). Tell me which one and I'll add it.

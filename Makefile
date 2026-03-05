# Makefile for weather_project
# Usage: make <target>

VENV := venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help setup-venv install db-init seed run clean

help:
	@echo "Available targets:"
	@echo "  setup-venv   - create a python virtualenv and upgrade pip"
	@echo "  install      - install dependencies from requirements.txt (creates venv if needed)"
	@echo "  db-init      - create DB role, database and tables (runs sql/create_tables.sql as postgres user)"
	@echo "  seed         - run weather_fetch.py to seed initial weather data"
	@echo "  run          - run the Flask app (python app.py)"
	@echo "  clean        - remove virtualenv and generated static images"

setup-venv:
	@echo "Creating virtualenv in $(VENV)"
	python3 -m venv $(VENV)
	@echo "Upgrading pip..."
	. $(VENV)/bin/activate && $(PIP) install --upgrade pip

install: setup-venv
	@echo "Installing requirements"
	. $(VENV)/bin/activate && $(PIP) install -r requirements.txt

db-init:
	@echo "Initializing Postgres DB (requires sudo privileges to run psql as postgres user)"
	@echo "Running: sudo -u postgres psql -f sql/create_tables.sql"
	sudo -u postgres psql -f sql/create_tables.sql

seed: install
	@echo "Seeding DB with a sample city (weather_fetch.py)"
	. $(VENV)/bin/activate && $(PY) weather_fetch.py

run: install
	@echo "Starting Flask app (debug mode)"
	. $(VENV)/bin/activate && $(PY) app.py

clean:
	@echo "Removing virtualenv and static images"
	-rm -rf $(VENV)
	-rm -f static/*.png

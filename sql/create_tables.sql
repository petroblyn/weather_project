-- SQL helper to create the database, user and required tables for the weather_project
-- NOTE: Running the user and database creation commands requires a Postgres superuser (typically the 'postgres' OS user).

-- 1) Create role and database (run as postgres user):
-- sudo -u postgres psql -f sql/create_tables.sql

-- Create user and DB (skip if already created)
DO $$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'weather_user'
   ) THEN
      CREATE ROLE weather_user LOGIN PASSWORD 'weather_pass';
   END IF;
END$$;

DO $$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_database WHERE datname = 'weather_db'
   ) THEN
      CREATE DATABASE weather_db OWNER weather_user;
   END IF;
END$$;

\connect weather_db

-- Create tables
CREATE TABLE IF NOT EXISTS weather (
    id SERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    temperature REAL,
    humidity REAL,
    condition TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hourly_weather (
    id SERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    hour TIMESTAMP WITH TIME ZONE,
    temperature REAL,
    condition TEXT
);

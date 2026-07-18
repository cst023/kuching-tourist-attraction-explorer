"""
Imports the cleaned Kuching attractions GeoJSON into a PostGIS table.

Usage:
    pip install psycopg2-binary
    python import_to_postgis.py
"""

import json
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()
DATABASE_URL = os.environ.get("DB_URL")

INPUT_FILE = "kuching_tourist_attractions.geojson"


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attractions (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            photo_url TEXT,
            geom GEOMETRY(Point, 4326) NOT NULL
        );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_attractions_geom ON attractions USING GIST (geom);")

    inserted = 0
    for feat in data["features"]:
        props = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]

        cur.execute(
            """
            INSERT INTO attractions (name, category, description, photo_url, geom)
            VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            """,
            (
                props.get("name"),
                props.get("category"),
                props.get("description", ""),
                props.get("photo_url", ""),
                lon,
                lat,
            ),
        )
        inserted += 1

    conn.commit()
    print(f"Inserted {inserted} rows into 'attractions'.")

    cur.execute("SELECT name, category, ST_AsText(geom) FROM attractions LIMIT 5;")
    print("\nSample rows:")
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()

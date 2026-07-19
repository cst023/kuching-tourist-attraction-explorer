"""
FastAPI backend for Kuching Tourist Attraction Explorer.

Endpoints:
    GET /attractions                            -> all attractions (GeoJSON)
    GET /attractions?category=Nature             -> filter by category
    GET /attractions?search=waterfront            -> search by name/description
    GET /attractions/nearby?lat=&lng=&radius_km=  -> attractions within radius (default 2km)

Run locally:
    pip install -r requirements.txt
    uvicorn main:app --reload

"""

from dotenv import load_dotenv
import os
from typing import Optional

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  
DATABASE_URL = os.environ.get("DB_URL")

app = FastAPI(title="Kuching Tourist Attraction Explorer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def rows_to_geojson(rows):
    """Convert DB rows (with geom as GeoJSON text) into a FeatureCollection.
    Includes distance_m in properties when present (used by /attractions/nearby)."""
    import json

    features = []
    for row in rows:
        props = {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "description": row["description"],
            "photo_url": row["photo_url"],
        }
        if "distance_m" in row.keys() and row["distance_m"] is not None:
            props["distance_m"] = round(row["distance_m"])

        features.append({
            "type": "Feature",
            "geometry": json.loads(row["geom_json"]),
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


@app.get("/")
def root():
    return {"status": "ok", "message": "Kuching Tourist Attraction Explorer API"}


@app.get("/attractions")
def get_attractions(
    category: Optional[str] = Query(None, description="Filter by category, e.g. Nature"),
    search: Optional[str] = Query(None, description="Search by name or description"),
):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = "SELECT id, name, category, description, photo_url, ST_AsGeoJSON(geom) AS geom_json FROM attractions WHERE 1=1"
    params = []

    if category:
        query += " AND category = %s"
        params.append(category)

    if search:
        query += " AND (name ILIKE %s OR description ILIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term])

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows_to_geojson(rows)


@app.get("/attractions/nearby")
def get_nearby_attractions(
    lat: float = Query(..., description="Latitude of the reference attraction"),
    lng: float = Query(..., description="Longitude of the reference attraction"),
    radius_km: float = Query(2.0, description="Search radius in kilometers"),
    exclude_id: Optional[int] = Query(None, description="Attraction id to exclude from results (usually the selected one itself)"),
):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
        SELECT id, name, category, description, photo_url, ST_AsGeoJSON(geom) AS geom_json,
               ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS distance_m
        FROM attractions
        WHERE ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s
        )
    """
    params = [lng, lat, lng, lat, radius_km * 1000]

    if exclude_id is not None:
        query += " AND id != %s"
        params.append(exclude_id)

    query += " ORDER BY distance_m ASC"

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows_to_geojson(rows)


@app.get("/categories")
def get_categories():
    """Handy for populating the frontend's filter dropdown dynamically."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT category FROM attractions ORDER BY category;")
    categories = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return {"categories": categories}

"""
FastAPI backend for Kuching Tourist Attraction Explorer.

Endpoints:
    GET /attractions                          -> all attractions (GeoJSON)
    GET /attractions?category=Nature           -> filter by category
    GET /attractions?search=waterfront          -> search by name/description

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
    """Convert DB rows (with geom as GeoJSON text) into a FeatureCollection."""
    import json

    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "geometry": json.loads(row["geom_json"]),
            "properties": {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "description": row["description"],
                "photo_url": row["photo_url"],
            },
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

# Kuching Tourist Attraction Explorer

An interactive web map for exploring tourist attractions in Kuching, Sarawak. Users can browse attractions on a map, search by name/description, and filter by category.

## Features
- Interactive map (Leaflet + OpenStreetMap) with attractions plotted as color-coded markers by category
- Click a marker to view details: photo, name, category, description, and nearby attractions within 2km
- Search attractions by name or description
- Filter attractions by category

## Architecture

```
     OpenStreetMap data
            |
            |  QGIS: prepare and clean data
            v
     Cleaned GeoJSON
            |
            |  import script
            v
     PostgreSQL + PostGIS  (Spatial database)
            |
            |  
            v
     FastAPI backend  
            |
            |  
            v
     Leaflet frontend 

```

**Data pipeline:** Raw tourism location points were queried from OpenStreetMap via Overpass Turbo, then processed and cleaned in QGIS. The cleaned dataset (20 locations) was imported into a PostGIS-enabled PostgreSQL database.

**Backend:** FastAPI serves attraction location data as GeoJSON, with endpoints for text search and filter by category.

**Frontend:** Vanilla HTML/CSS/JS with Leaflet.js, calling the backend API to render markers, handle search/filter, and display attraction details.

## Tech Stack
| Layer | Technology |
|---|---|
| Data sourcing & cleaning | OpenStreetMap (Overpass Turbo), QGIS |
| Database | PostgreSQL + PostGIS |
| Backend API | FastAPI, psycopg2 |
| Frontend | HTML, CSS, JavaScript, Leaflet.js |
| Hosting | GitHub Pages (frontend), Render (backend + database) |


## Running Locally

**Backend**
```bash
pip install -r requirements.txt
# set DATABASE_URL to your PostgreSQL/PostGIS connection string
uvicorn main:app --reload
```

**Frontend**
Open `index.html` directly in a browser, or serve it locally:
```bash
python3 -m http.server 5500
```
Update `API_BASE` in `script.js` to point to your local backend if testing locally.

## Screenshots
#### Map view
![Map view](<image/map view.png>)
 
#### Map view with location detail
![Map view with location detail](<image/map view with location detail.png>)


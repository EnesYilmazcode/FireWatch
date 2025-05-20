# scripts/01_create_grid.py
import geopandas as gpd
from shapely.geometry import box, Polygon
import numpy as np
import os

# --- Configuration ---
OUTPUT_DIR = "C:/Users/galax/OneDrive/Desktop/FireWatch/data/grid"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "usa_grid_10km.geojson")
RESOLUTION_KM = 10
# Approximate bounds for CONUS (Contiguous US)
# You can get more precise bounds from a US shapefile
CONUS_BOUNDS = (-125, 24, -66, 50) # (minx, miny, maxx, maxy)

def generate_grid(bounds, resolution_km=10):
    xmin, ymin, xmax, ymax = bounds
    # Rough approximation: 1 degree of latitude ~ 111 km.
    # 1 degree of longitude varies, ~111km * cos(latitude).
    # For simplicity, we use 111km for both, but acknowledge it's an approximation.
    # A more robust method would use an equal-area projection.
    step_approx_deg = resolution_km / 111.0
    
    polygons = []
    grid_ids = []
    current_id = 0
    
    # Create a list of x and y coordinates for the grid
    x_coords = np.arange(xmin, xmax, step_approx_deg)
    y_coords = np.arange(ymin, ymax, step_approx_deg)

    for i in range(len(x_coords)):
        for j in range(len(y_coords)):
            x0, y0 = x_coords[i], y_coords[j]
            x1, y1 = x0 + step_approx_deg, y0 + step_approx_deg
            polygons.append(box(x0, y0, x1, y1))
            grid_ids.append(current_id)
            current_id += 1
    
    grid = gpd.GeoDataFrame({'grid_id': grid_ids, 'geometry': polygons}, crs="EPSG:4326")
    return grid

def filter_grid_to_usa(grid_gdf):
    # Load US states shapefile
    world = gpd.read_file("data/shapefiles/ne_110m_admin_0_countries.shp")
    usa = world[world["ADMIN"] == "United States of America"]
    
    # Ensure CRS match
    if grid_gdf.crs != usa.crs:
        usa = usa.to_crs(grid_gdf.crs)
    
    # Filter grid cells whose centroids are within the USA polygon
    grid_centroids = grid_gdf.copy()
    grid_centroids['geometry'] = grid_centroids.geometry.centroid
    
    joined_centroids = gpd.sjoin(grid_centroids, usa, how='inner', predicate='within')
    valid_grid_ids = joined_centroids['grid_id'].unique()
    
    filtered_grid = grid_gdf[grid_gdf['grid_id'].isin(valid_grid_ids)].reset_index(drop=True)
    
    return filtered_grid


print(f"Generating {RESOLUTION_KM}km grid for CONUS bounds: {CONUS_BOUNDS}...")
initial_grid = generate_grid(CONUS_BOUNDS, RESOLUTION_KM)
print(f"Initial grid cells: {len(initial_grid)}")

print("Filtering grid to USA boundaries...")
usa_grid = filter_grid_to_usa(initial_grid)
print(f"Filtered grid cells within USA: {len(usa_grid)}")

# Add centroid coordinates
usa_grid['centroid_lon'] = usa_grid.geometry.centroid.x
usa_grid['centroid_lat'] = usa_grid.geometry.centroid.y

usa_grid.to_file(OUTPUT_PATH, driver="GeoJSON")
print(f"Saved grid to {OUTPUT_PATH}")
print(f"Grid info:\n{usa_grid.head()}")
import requests
import pandas as pd
from io import StringIO
import folium
import datetime # To get today's date
import os       # To create directories if they don't exist
from dotenv import load_dotenv  

load_dotenv()

# === CONFIG ===
API_KEY = os.getenv("API_KEY")
SOURCE = "VIIRS_SNPP_NRT"  # This is the <SOURCE> parameter for FIRMS
DAY_RANGE = 1              # For "last 24h", use 1 day
ACQ_DATE = datetime.date.today().strftime('%Y-%m-%d') # Date in YYYY-MM-DD format
print(f"ACQ_DATE: {ACQ_DATE}")

# BBOX: West, South, East, North (which is Xmin, Ymin, Xmax, Ymax)
BBOX = "-125,24,-66,49"

# Corrected URL structure for FIRMS area CSV API
URL = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{API_KEY}/{SOURCE}/{BBOX}/{DAY_RANGE}/{ACQ_DATE}"

OUTPUT_CSV_DIR = "data"
OUTPUT_VIS_DIR = "visualizations"
OUTPUT_CSV = os.path.join(OUTPUT_CSV_DIR, "firms_viirs_active_fires.csv")
MAP_OUTPUT = os.path.join(OUTPUT_VIS_DIR, "firms_map.html")

# Create output directories if they don't exist
os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
os.makedirs(OUTPUT_VIS_DIR, exist_ok=True)

# === FETCH CSV ===
print(f"ℹ️ Fetching data from: {URL}") # Good to print the URL for debugging
response = requests.get(URL)

if response.status_code != 200:
    print(f"❌ Error from API (HTTP {response.status_code}): {response.text}")
    # Save the error response for inspection if it's an HTTP error
    with open(OUTPUT_CSV, 'w') as f:
        f.write(f"HTTP Error {response.status_code}:\n{response.text}")
    print(f"⚠️ API HTTP error response saved to {OUTPUT_CSV}")
    raise Exception("Failed to fetch FIRMS data due to HTTP error.")

# Check if the response text itself indicates an API call error
# (even if status_code was 200, the content can be an error message)
response_text_lower = response.text.lower()
if "invalid api key" in response_text_lower or \
   "invalid area request" in response_text_lower or \
   "invalid api call" in response_text_lower or \
   "no fire data found for the specified criteria" in response_text_lower: # FIRMS specific message
    print(f"❌ Error message in API response content: {response.text.strip()}")
    # Save the error response for inspection
    with open(OUTPUT_CSV, 'w') as f:
        f.write(response.text)
    print(f"⚠️ API content error response saved to {OUTPUT_CSV}")
    if "no fire data found" not in response_text_lower: # Don't raise exception if it's just no data
         raise Exception(f"API call was invalid or returned an error: {response.text.strip()}")
    else:
        # Handle "no fire data found" gracefully by creating an empty DataFrame
        print("ℹ️ No fire data found for the specified criteria. Proceeding with empty dataset.")
        df = pd.DataFrame(columns=['latitude', 'longitude', 'brightness', 'scan', 'track', 'acq_date', 'acq_time', 'satellite', 'confidence', 'version', 'bright_t31', 'frp', 'daynight']) # Use known columns or make more generic
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"✅ Saved empty fire records (no fires found) to {OUTPUT_CSV}")
else:
    try:
        df = pd.read_csv(StringIO(response.text))
        if df.empty:
            print("ℹ️ Successfully fetched data, but it's empty (no fires detected).")
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"✅ Saved {len(df)} fire records to {OUTPUT_CSV}")
    except pd.errors.EmptyDataError:
        print("❌ API returned 200 OK, but the CSV content was empty or unparseable (not an error message).")
        print(f"Raw response text: \n{response.text}")
        with open(OUTPUT_CSV, 'w') as f: # Save the problematic content
            f.write(response.text)
        print(f"⚠️ Problematic API response saved to {OUTPUT_CSV}")
        # Create an empty DataFrame to allow script to continue if desired, or raise error
        df = pd.DataFrame(columns=['latitude', 'longitude', 'brightness', 'acq_date'])
        # raise Exception("Failed to parse CSV data, content was empty or malformed.")
    except Exception as e:
        print(f"❌ An unexpected error occurred while parsing CSV: {e}")
        print(f"Raw response text: \n{response.text}")
        with open(OUTPUT_CSV, 'w') as f: # Save the problematic content
            f.write(response.text)
        print(f"⚠️ Problematic API response saved to {OUTPUT_CSV}")
        raise


# === GENERATE MAP ===
# Ensure df exists and is not empty, and has the required columns
if 'df' in locals() and not df.empty and 'latitude' in df.columns and 'longitude' in df.columns:
    # Ensure latitude and longitude are numeric, drop rows where conversion fails
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df.dropna(subset=['latitude', 'longitude'], inplace=True)

    if not df.empty: # Check again after coercing and dropping NaNs
        m = folium.Map(location=[37.0, -95.0], zoom_start=4) # Continental US view
        for _, row in df.iterrows():
            popup_text = []
            if 'brightness' in row and pd.notna(row['brightness']):
                popup_text.append(f"Brightness: {row['brightness']}")
            if 'acq_date' in row and pd.notna(row['acq_date']):
                popup_text.append(f"Date: {row['acq_date']}")
            if 'acq_time' in row and pd.notna(row['acq_time']):
                 popup_text.append(f"Time: {str(row['acq_time']).zfill(4)}") # Ensure 4 digits for time
            if 'confidence' in row and pd.notna(row['confidence']):
                popup_text.append(f"Confidence: {row['confidence']}")
            if 'frp' in row and pd.notna(row['frp']):
                popup_text.append(f"FRP: {row['frp']}")

            folium.CircleMarker(
                location=(row['latitude'], row['longitude']),
                radius=3,
                color="red",
                fill=True,
                fill_color="darkred",
                fill_opacity=0.6,
                popup="<br>".join(popup_text) if popup_text else "Fire Hotspot"
            ).add_to(m)

        m.save(MAP_OUTPUT)
        print(f"🗺️ Map saved to {MAP_OUTPUT}")
    else:
        print("⚠️ No valid fire data with coordinates to plot after cleaning.")

elif 'df' in locals() and df.empty:
    print("⚠️ No fire data to plot (DataFrame is empty). Map not generated.")
else:
    print(f"⚠️ 'latitude' or 'longitude' columns not found in the data, or DataFrame 'df' not created due to earlier errors. Columns are: {df.columns if 'df' in locals() else 'df not defined'}. Map not generated.")
    print("Please check the content of the CSV file for the correct column names if it was created, or API error messages.")
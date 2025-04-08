import { useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import countyGeoJSON from "./data/us-counties.json";
import wildfireData from "./data/national-wildfire-risk.json";

const getColor = (risk) => {
  if (risk > 80) return "#800026";
  if (risk > 60) return "#BD0026";
  if (risk > 40) return "#E31A1C";
  if (risk > 20) return "#FD8D3C";
  return "#FFEDA0";
};

const fipsToStateAbbr = {
  "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
  "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
  "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
  "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
  "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
  "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
  "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
  "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
  "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
  "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
  "56": "WY"
};

function App() {
  const [riskData, setRiskData] = useState({});

  useEffect(() => {
    setRiskData(wildfireData);
  }, []);

  const onEachFeature = (feature, layer) => {
    const county = feature.properties.NAME;
    const fips = feature.properties.STATEFP;
    const stateAbbr = fipsToStateAbbr[fips];
    const name = `${county} County, ${stateAbbr}`;
  
    const risk = riskData[name] || 0;
  
    layer.setStyle({
      fillColor: getColor(risk),
      fillOpacity: 0.7,
      weight: 1,
      color: "#999",
    });
  
    layer.bindTooltip(
      `<strong>${name}</strong><br/><span style="color:black;">Risk: ${risk}%</span>`,
      {
        sticky: true,
        direction: "top",
        offset: [0, -10],
        opacity: 0.9,
        className: "custom-tooltip",
      }
    );
  };
  
  
  
  return (
    <div style={{ height: "100vh", width: "100vw", position: "relative" }}>
      <MapContainer
        center={[37.5, -119.5]}
        zoom={6}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        <GeoJSON data={countyGeoJSON} onEachFeature={onEachFeature} />
      </MapContainer>

      <div
        style={{
          position: "absolute",
          bottom: "40px",
          left: "40px",
          background: "white",
          padding: "15px",
          borderRadius: "10px",
          boxShadow: "0 0 12px rgba(0,0,0,0.4)",
          fontSize: "1rem",
          lineHeight: "1.8",
          zIndex: 1000,
          color: "black", // Set the default text color to black
        }}
      >
        <strong style={{ fontSize: "1.2rem", marginBottom: "8px", display: "block" }}>Wildfire Risk</strong>
        <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
          <span style={{ background: "#FFEDA0", display: "inline-block", width: "20px", height: "20px", marginRight: "8px", border: "1px solid #ccc" }} />
          <span>0–20% (Low)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
          <span style={{ background: "#FD8D3C", display: "inline-block", width: "20px", height: "20px", marginRight: "8px", border: "1px solid #ccc" }} />
          <span>21–40% (Moderate)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
          <span style={{ background: "#E31A1C", display: "inline-block", width: "20px", height: "20px", marginRight: "8px", border: "1px solid #ccc" }} />
          <span>41–60% (High)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
          <span style={{ background: "#BD0026", display: "inline-block", width: "20px", height: "20px", marginRight: "8px", border: "1px solid #ccc" }} />
          <span>61–80% (Very High)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center" }}>
          <span style={{ background: "#800026", display: "inline-block", width: "20px", height: "20px", marginRight: "8px", border: "1px solid #ccc" }} />
          <span>81–100% (Extreme)</span>
        </div>
      </div>
    </div>
  );
}

export default App;
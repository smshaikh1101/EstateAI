function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2-lat1) * Math.PI / 180;
  const dLon = (lon2-lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  return 2 * R * Math.asin(Math.sqrt(a));
}

function langPrefix() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  const maybeLang = parts[0] || "";
  if (maybeLang.length === 2) return "/" + maybeLang;
  return "";
}

async function loadNearby() {
  const status = document.getElementById("status");
  const results = document.getElementById("results");
  results.innerHTML = "";
  status.innerText = "Requesting your location...";

  if (!navigator.geolocation) {
    status.innerText = "Geolocation not supported.";
    return;
  }

  navigator.geolocation.getCurrentPosition(async (pos) => {
    const myLat = pos.coords.latitude;
    const myLon = pos.coords.longitude;

    status.innerText = "Loading properties...";
    const resp = await fetch("/api/properties-geo/");
    const data = await resp.json();
    const props = data.properties || [];

    const withDistance = props.map(p => ({
      ...p,
      distance_km: haversineKm(myLat, myLon, p.lat, p.lon)
    })).sort((a,b) => a.distance_km - b.distance_km);

    status.innerText = `Found ${withDistance.length} properties with location.`;

    const prefix = langPrefix();
    withDistance.slice(0, 50).forEach(p => {
      const a = document.createElement("a");
      a.className = "list-group-item list-group-item-action";
      a.href = `${prefix}/properties/${p.id}/`;
      a.innerHTML = `
        <div class="d-flex justify-content-between">
          <strong>${p.title}</strong>
          <span>${p.distance_km.toFixed(2)} km</span>
        </div>
        <div class="text-muted">${p.district}${p.taluka ? " / " + p.taluka : ""} — ₹ ${p.price_inr}</div>
      `;
      results.appendChild(a);
    });

  }, (err) => {
    status.innerText = err.message;
  }, { enableHighAccuracy: true, timeout: 10000 });
}

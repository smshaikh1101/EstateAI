let watchId = null;
let points = [];

function toMeters(lat, lon, refLat, refLon) {
  const R = 6371000;
  const x = (lon - refLon) * Math.cos((lat + refLat) * 0.5 * Math.PI / 180) * Math.PI/180 * R;
  const y = (lat - refLat) * Math.PI/180 * R;
  return [x, y];
}

function polygonAreaMeters2(pointsLatLon) {
  if (pointsLatLon.length < 3) return 0;
  const ref = pointsLatLon[0];
  const xy = pointsLatLon.map(p => toMeters(p.lat, p.lon, ref.lat, ref.lon));
  let sum = 0;
  for (let i = 0; i < xy.length; i++) {
    const [x1, y1] = xy[i];
    const [x2, y2] = xy[(i + 1) % xy.length];
    sum += (x1 * y2 - x2 * y1);
  }
  return Math.abs(sum) / 2;
}

function render() {
  document.getElementById("count").innerText = points.length;
  const area = polygonAreaMeters2(points);
  document.getElementById("area").innerText = area.toFixed(2);
  document.getElementById("log").innerText = JSON.stringify(points, null, 2);
}

function startTrack() {
  if (!navigator.geolocation) {
    alert("Geolocation not supported");
    return;
  }
  if (watchId !== null) return;

  watchId = navigator.geolocation.watchPosition(
    (pos) => {
      points.push({ lat: pos.coords.latitude, lon: pos.coords.longitude, t: Date.now() });
      render();
    },
    (err) => alert(err.message),
    { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
  );
}

function stopTrack() {
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }
}

function resetTrack() {
  stopTrack();
  points = [];
  render();
}

render();

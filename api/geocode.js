// Vercel serverless proxy for the Mapbox Geocoding v6 API.
//
// Why a proxy? The repo is a static HTML site with no build step, so there
// is no clean way to inject a Mapbox token into client code at deploy time.
// Holding the token server-side here keeps it out of the browser bundle and
// out of the public GitHub history.
//
// Required env var (set in the Vercel project settings):
//   MAPBOX_TOKEN  — Mapbox secret or public token with Geocoding scope.
//
// Forward: GET /api/geocode?q=<address>
// Reverse: GET /api/geocode?lat=<lat>&lng=<lng>   (Connecticut only; returns
//          the neighborhood / town containing the point, never a street
//          address, so a device location can be labelled without exposing it)
// Response: { features: [{ name, full_address, coordinates: [lng, lat], feature_type }, ...] }

const CT_BBOX = "-73.7277,40.9509,-71.7869,42.0506";
const CT_PROXIMITY = "-72.7,41.6";
const [CT_W, CT_S, CT_E, CT_N] = CT_BBOX.split(",").map(Number);

function mapFeatures(data) {
  return (data.features || []).map(f => {
    const props = f.properties || {};
    const coords = f.geometry && f.geometry.coordinates;
    return {
      name: props.name || props.full_address || "",
      full_address: props.full_address || props.place_formatted || props.name || "",
      coordinates: Array.isArray(coords) ? [coords[0], coords[1]] : null,
      feature_type: props.feature_type || null,
    };
  }).filter(f => f.coordinates);
}

module.exports = async function handler(req, res) {
  const token = process.env.MAPBOX_TOKEN;
  if (!token) {
    res.status(500).json({ error: "MAPBOX_TOKEN env var not configured on this deployment." });
    return;
  }

  let url;
  const hasPoint = req.query.lat != null && req.query.lng != null;
  if (hasPoint) {
    const lat = Number(req.query.lat), lng = Number(req.query.lng);
    if (!isFinite(lat) || !isFinite(lng)) { res.status(400).json({ error: "bad lat/lng" }); return; }
    if (lng < CT_W || lng > CT_E || lat < CT_S || lat > CT_N) {
      res.status(400).json({ error: "outside Connecticut" });
      return;
    }
    const params = new URLSearchParams({
      longitude: String(lng),
      latitude: String(lat),
      access_token: token,
      country: "us",
      types: "neighborhood,locality,place",
      limit: "1",
      language: "en",
    });
    url = `https://api.mapbox.com/search/geocode/v6/reverse?${params.toString()}`;
  } else {
    const q = (req.query.q || "").toString().trim();
    if (!q) { res.status(400).json({ error: "missing q" }); return; }
    if (q.length < 3) { res.status(200).json({ features: [] }); return; }
    const params = new URLSearchParams({
      q,
      access_token: token,
      country: "us",
      types: "address,street,place,postcode,locality,neighborhood",
      bbox: CT_BBOX,
      proximity: CT_PROXIMITY,
      autocomplete: "true",
      limit: "5",
      language: "en",
    });
    url = `https://api.mapbox.com/search/geocode/v6/forward?${params.toString()}`;
  }

  try {
    const r = await fetch(url);
    if (!r.ok) {
      const detail = await r.text().catch(() => "");
      res.status(r.status).json({ error: `mapbox ${r.status}`, detail: detail.slice(0, 200) });
      return;
    }
    const data = await r.json();
    res.setHeader("Cache-Control", "private, no-store");
    res.status(200).json({ features: mapFeatures(data) });
  } catch (e) {
    res.status(502).json({ error: "fetch failed" });
  }
};

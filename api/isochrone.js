// Vercel serverless proxy for the Mapbox Isochrone API.
//
// Same reason as api/geocode.js: the site is static with no build step, so
// the Mapbox token stays server-side here instead of in the browser.
//
// Required env var (set in the Vercel project settings):
//   MAPBOX_TOKEN  — Mapbox token with access to the Isochrone API.
//
// GET /api/isochrone?lng=<lng>&lat=<lat>   (Connecticut only)
// Response: Mapbox's GeoJSON FeatureCollection, one polygon per contour,
//           with properties.contour = 15 | 30 | 60 (minutes by car).
//
// The "driving" profile (no live traffic) is used so results are stable
// and cacheable; the drive times are Mapbox's road-network estimates, not
// the OpenTripPlanner model behind the index itself.

const CT_BBOX = "-73.7277,40.9509,-71.7869,42.0506";
const [CT_W, CT_S, CT_E, CT_N] = CT_BBOX.split(",").map(Number);
const CONTOURS = "15,30,60";

module.exports = async function handler(req, res) {
  const token = process.env.MAPBOX_TOKEN;
  if (!token) {
    res.status(500).json({ error: "MAPBOX_TOKEN env var not configured on this deployment." });
    return;
  }

  const lat = Number(req.query.lat), lng = Number(req.query.lng);
  if (!isFinite(lat) || !isFinite(lng)) { res.status(400).json({ error: "bad lat/lng" }); return; }
  if (lng < CT_W || lng > CT_E || lat < CT_S || lat > CT_N) {
    res.status(400).json({ error: "outside Connecticut" });
    return;
  }

  // Five decimals (about a meter) so repeat requests for the same address
  // share one upstream call and one CDN cache entry.
  const coords = `${lng.toFixed(5)},${lat.toFixed(5)}`;
  const params = new URLSearchParams({
    contours_minutes: CONTOURS,
    polygons: "true",
    denoise: "1",
    access_token: token,
  });
  const url = `https://api.mapbox.com/isochrone/v1/mapbox/driving/${coords}?${params.toString()}`;

  try {
    const r = await fetch(url);
    if (!r.ok) {
      const detail = await r.text().catch(() => "");
      res.status(r.status).json({ error: `mapbox ${r.status}`, detail: detail.slice(0, 200) });
      return;
    }
    const data = await r.json();
    res.setHeader("Cache-Control", "public, s-maxage=86400, stale-while-revalidate=604800");
    res.status(200).json(data);
  } catch (e) {
    res.status(502).json({ error: "fetch failed" });
  }
};

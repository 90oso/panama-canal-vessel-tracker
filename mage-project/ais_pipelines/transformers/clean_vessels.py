if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer

@transformer
def clean_vessels(raw_vessels, *args, **kwargs):
    clean = []
    for v in raw_vessels:
        try:
            lat = float(v["latitude"])
            lon = float(v["longitude"])
        except (TypeError, ValueError):
            continue

        clean.append({
            "mmsi": int(v["mmsi"]),
            "name": (v.get("name") or "UNKNOWN").strip(),
            "ship_type": v.get("typeSpecific") or "Unknown",
            "lat": lat,
            "lon": lon,
            "speed": float(v["speed"]) if v.get("speed") not in (None, "") else None,
            "course": float(v["course"]) if v.get("course") not in (None, "") else None,
            "heading": float(v["heading"]) if v.get("heading") not in (None, "") else None,
        })
    return clean
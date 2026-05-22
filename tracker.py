import os
import csv
import requests
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
RAPIDAPI_KEY   = os.environ["RAPIDAPI_KEY"]
ORIGIN         = "ADL"
DESTINATION    = "DPS"
CURRENCY       = "AUD"
ADULTS         = 2
CHILDREN       = 1
CSV_FILE       = "flight_log.csv"

OUTBOUND_DATES = [
    "2027-04-03",
    "2027-04-10",
    "2027-04-17",
    "2027-04-24",
]
RETURN_DATES = [
    "2027-04-17",
    "2027-04-24",
    "2027-05-01",
]

ALERT_THRESHOLD_PP = 450   # AUD per person

HEADERS = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": "sky-scrapper.p.rapidapi.com",
}

# ── Airport lookup ────────────────────────────────────────────────────────────
def lookup_airport(query: str):
    """Return (skyId, entityId) for an airport IATA code."""
    url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport"
    try:
        resp = requests.get(url, headers=HEADERS,
                            params={"query": query, "locale": "en-AU"}, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("data", [])
        if not results:
            print(f"  ✗ No airport found for '{query}'")
            return None, None
        r = results[0]
        sky_id    = r.get("skyId") or r.get("iataCode")
        entity_id = (r.get("entityId")
                     or r.get("presentation", {}).get("entityId")
                     or r.get("navigation", {}).get("entityId"))
        print(f"  ✓ {query} → skyId={sky_id}  entityId={entity_id}")
        return sky_id, entity_id
    except requests.RequestException as e:
        print(f"  ✗ Airport lookup error: {e}")
        return None, None


# ── Flight search ─────────────────────────────────────────────────────────────
def search_flights(depart_date, return_date,
                   origin_sky, origin_entity,
                   dest_sky, dest_entity):
    url = "https://sky-scrapper.p.rapidapi.com/api/v2/flights/searchFlights"
    params = {
        "originSkyId":         origin_sky,
        "destinationSkyId":    dest_sky,
        "originEntityId":      origin_entity,
        "destinationEntityId": dest_entity,
        "date":                depart_date,
        "returnDate":          return_date,
        "adults":              str(ADULTS),
        "children":            str(CHILDREN),
        "currency":            CURRENCY,
        "countryCode":         "AU",
        "market":              "en-AU",
        "cabinClass":          "economy",
        "sortBy":              "best",
    }
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  ✗ API error for {depart_date}→{return_date}: {e}")
        return None


def extract_cheapest(data):
    try:
        itineraries = data["data"]["itineraries"]
        if not itineraries:
            return None
        prices = [i["price"]["raw"] for i in itineraries if "price" in i]
        return min(prices) if prices else None
    except (KeyError, TypeError):
        return None


# ── CSV helpers ───────────────────────────────────────────────────────────────
FIELDNAMES = ["timestamp", "outbound", "return", "total_aud", "per_person_aud", "alert"]

def append_rows(rows):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    pax = ADULTS + CHILDREN
    new_rows = []
    alerts = []

    print(f"Flight tracker — {now}")
    print(f"Route: {ORIGIN} → {DESTINATION} | {ADULTS} adults + {CHILDREN} child | {CURRENCY}\n")

    print("Looking up airport IDs...")
    origin_sky, origin_entity = lookup_airport(ORIGIN)
    dest_sky, dest_entity     = lookup_airport(DESTINATION)
    print()

    if not origin_sky or not dest_sky:
        print("✗ Could not resolve airports — aborting.")
        return

    for out in OUTBOUND_DATES:
        for ret in RETURN_DATES:
            if ret <= out:
                continue

            print(f"  Checking {out} → {ret} ...", end=" ", flush=True)
            data = search_flights(out, ret, origin_sky, origin_entity, dest_sky, dest_entity)
            if data is None:
                continue

            total = extract_cheapest(data)
            if total is None:
                print("no results")
                continue

            per_person = round(total / pax, 2)
            is_alert   = per_person < ALERT_THRESHOLD_PP
            flag       = "YES" if is_alert else ""

            print(f"${total:.0f} total  (${per_person:.0f}/person) {flag}")

            new_rows.append({
                "timestamp":      now,
                "outbound":       out,
                "return":         ret,
                "total_aud":      f"{total:.2f}",
                "per_person_aud": f"{per_person:.2f}",
                "alert":          flag,
            })

            if is_alert:
                alerts.append(
                    f"  🔔 CHEAP FARE: {out} out / {ret} return — "
                    f"${total:.0f} total (${per_person:.0f}/person)"
                )

    if new_rows:
        append_rows(new_rows)
        print(f"\n✓ Logged {len(new_rows)} price points to {CSV_FILE}")
    else:
        print("\n⚠ No prices retrieved — check API key and quota.")

    if alerts:
        print("\n" + "="*55)
        print("PRICE ALERTS — fares below threshold!")
        for a in alerts:
            print(a)
        print(f"  Threshold: ${ALERT_THRESHOLD_PP}/person")
        print("="*55)


if __name__ == "__main__":
    main()

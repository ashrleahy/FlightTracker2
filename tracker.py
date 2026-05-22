import os
import csv
import requests
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
RAPIDAPI_KEY   = os.environ["RAPIDAPI_KEY"]
CURRENCY       = "AUD"
ADULTS         = 2
CHILDREN       = 1
CSV_FILE       = "flight_log.csv"

# Adelaide Airport (ADL) and Denpasar/Bali (DPS)
# Entity IDs confirmed from Sky Scrapper API docs
ORIGIN_SKY        = "ADL"
ORIGIN_ENTITY     = "95673402"   # Adelaide Airport
DEST_SKY          = "DPS"
DEST_ENTITY       = "95673625"   # Denpasar Ngurah Rai

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

# ── Airport lookup (used once to verify entity IDs) ───────────────────────────
def verify_airports():
    """Print entity IDs for ADL and DPS so we can confirm they're correct."""
    url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport"
    for query, label in [("Adelaide airport", "ADL"), ("Denpasar airport", "DPS")]:
        try:
            resp = requests.get(url, headers=HEADERS,
                                params={"query": query}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("data", [])
            for r in results[:2]:
                sky    = r.get("skyId")
                entity = (r.get("entityId")
                          or (r.get("navigation") or {}).get("entityId"))
                name   = (r.get("presentation") or {}).get("title", "")
                print(f"  [{label}] {name}: skyId={sky}  entityId={entity}")
        except Exception as e:
            print(f"  Lookup error for {label}: {e}")


# ── Flight search ─────────────────────────────────────────────────────────────
def search_flights(depart_date, return_date):
    url = "https://sky-scrapper.p.rapidapi.com/api/v2/flights/searchFlights"
    params = {
        "originSkyId":         ORIGIN_SKY,
        "destinationSkyId":    DEST_SKY,
        "originEntityId":      ORIGIN_ENTITY,
        "destinationEntityId": DEST_ENTITY,
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
        result = resp.json()
        # Print top-level keys so we can debug response structure if needed
        print(f"    [debug] response keys: {list((result.get('data') or {}).keys())[:5]}")
        return result
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
    print(f"Route: ADL → DPS | {ADULTS} adults + {CHILDREN} child | {CURRENCY}\n")

    print("Verifying airport entity IDs...")
    verify_airports()
    print()

    for out in OUTBOUND_DATES:
        for ret in RETURN_DATES:
            if ret <= out:
                continue

            print(f"  Checking {out} → {ret} ...", end=" ", flush=True)
            data = search_flights(out, ret)
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

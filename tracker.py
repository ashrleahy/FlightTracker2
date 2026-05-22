import os
import csv
import time
import requests
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
RAPIDAPI_KEY   = os.environ["RAPIDAPI_KEY"]
CURRENCY       = "AUD"
ADULTS         = 2
CHILDREN       = 1
CSV_FILE       = "flight_log.csv"

# Confirmed entity IDs from Sky Scrapper searchAirport endpoint
ORIGIN_SKY    = "ADL"
ORIGIN_ENTITY = "104120231"   # Adelaide Airport ✓
DEST_SKY      = "DPS"
DEST_ENTITY   = "95673809"    # Bali (Denpasar) ✓

OUTBOUND_DATES = [
    "2027-04-03",
    "2027-04-10",
    "2027-04-24",
]
RETURN_DATE = "2027-04-24"

ALERT_THRESHOLD_PP = 450   # AUD per person

HEADERS = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": "sky-scrapper.p.rapidapi.com",
}

DELAY_BETWEEN_CALLS = 3   # seconds between requests

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
        return resp.json()
    except requests.RequestException as e:
        print(f"  ✗ {e}")
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
    print(f"Route: {ORIGIN_SKY} ({ORIGIN_ENTITY}) → {DEST_SKY} ({DEST_ENTITY})")
    print(f"Pax: {ADULTS} adults + {CHILDREN} child | {CURRENCY}\n")

    for out in OUTBOUND_DATES:
        print(f"  Checking {out} → {RETURN_DATE} ...", end=" ", flush=True)
        data = search_flights(out, RETURN_DATE)
        time.sleep(DELAY_BETWEEN_CALLS)

        if data is None:
            continue

        total = extract_cheapest(data)
        if total is None:
            top_keys = list((data.get("data") or {}).keys())
            print(f"no results (keys: {top_keys})")
            continue

        per_person = round(total / pax, 2)
        is_alert   = per_person < ALERT_THRESHOLD_PP
        flag       = "YES" if is_alert else ""

        print(f"${total:.0f} total  (${per_person:.0f}/person) {flag}")

        new_rows.append({
            "timestamp":      now,
            "outbound":       out,
            "return":         RETURN_DATE,
            "total_aud":      f"{total:.2f}",
            "per_person_aud": f"{per_person:.2f}",
            "alert":          flag,
        })

        if is_alert:
            alerts.append(
                f"  🔔 CHEAP FARE: {out} out / {RETURN_DATE} return — "
                f"${total:.0f} total (${per_person:.0f}/person)"
            )

    if new_rows:
        append_rows(new_rows)
        print(f"\n✓ Logged {len(new_rows)} price points to {CSV_FILE}")
    else:
        print("\n⚠ No prices retrieved.")

    if alerts:
        print("\n" + "="*55)
        print("PRICE ALERTS — fares below threshold!")
        for a in alerts:
            print(a)
        print(f"  Threshold: ${ALERT_THRESHOLD_PP}/person")
        print("="*55)


if __name__ == "__main__":
    main()

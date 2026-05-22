import os
import csv
import requests
from datetime import datetime, date, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
RAPIDAPI_KEY   = os.environ["RAPIDAPI_KEY"]
ORIGIN         = "ADL"          # Adelaide
DESTINATION    = "DPS"          # Bali (Denpasar)
CURRENCY       = "AUD"
ADULTS         = 2
CHILDREN       = 1              # 9-year-old (counts as full fare on Jetstar intl)
CSV_FILE       = "flight_log.csv"

# Dates to track — edit these to suit your travel window
# Format: "YYYY-MM-DD"
OUTBOUND_DATES = [
    "2027-04-03",   # week before Easter
    "2027-04-10",   # Easter school holidays start
    "2027-04-17",   # mid-school-holidays
    "2027-04-24",   # post-Easter
]
RETURN_DATES = [
    "2027-04-17",   # 2 weeks after earliest outbound
    "2027-04-24",
    "2027-05-01",
]

# Alert threshold — script will flag if price per person drops below this
ALERT_THRESHOLD_PP = 450        # AUD per person return

# ── API call ──────────────────────────────────────────────────────────────────
def search_flights(depart_date: str, return_date: str) -> dict | None:
    """Query Sky Scrapper on RapidAPI for ADL→DPS return fares."""
    url = "https://sky-scrapper.p.rapidapi.com/api/v2/flights/searchFlights"
    params = {
        "originSkyId":        ORIGIN,
        "destinationSkyId":   DESTINATION,
        "originEntityId":     "27544008",   # Adelaide Airport entity ID
        "destinationEntityId":"27537542",   # Denpasar (Bali) entity ID
        "date":               depart_date,
        "returnDate":         return_date,
        "adults":             str(ADULTS),
        "children":           str(CHILDREN),
        "currency":           CURRENCY,
        "countryCode":        "AU",
        "market":             "en-AU",
        "cabinClass":         "economy",
        "sortBy":             "best",
    }
    headers = {
        "x-rapidapi-key":  RAPIDAPI_KEY,
        "x-rapidapi-host": "sky-scrapper.p.rapidapi.com",
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  ✗ API error for {depart_date} → {return_date}: {e}")
        return None


def extract_cheapest(data: dict) -> float | None:
    """Pull the lowest total price from the API response."""
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

def load_csv() -> list[dict]:
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, newline="") as f:
        return list(csv.DictReader(f))


def append_rows(rows: list[dict]):
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

    for out in OUTBOUND_DATES:
        for ret in RETURN_DATES:
            # Skip nonsensical combos where return is before outbound
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

            row = {
                "timestamp":      now,
                "outbound":       out,
                "return":         ret,
                "total_aud":      f"{total:.2f}",
                "per_person_aud": f"{per_person:.2f}",
                "alert":          flag,
            }
            new_rows.append(row)

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

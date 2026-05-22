import os
import csv
import time
from datetime import datetime, date
from apify_client import ApifyClient

# ── Config ────────────────────────────────────────────────────────────────────
APIFY_TOKEN  = os.environ["APIFY_TOKEN"]
ACTOR_ID     = "makework36/flight-price-scraper"

ORIGIN       = "ADL"
DESTINATION  = "DPS"
CURRENCY     = "AUD"
ADULTS       = 3
CABIN        = "ECONOMY"
TOTAL_PAX    = 3
CSV_FILE     = "flight_log.csv"

OUTBOUND_DATES = [
    "2027-04-01", "2027-04-02", "2027-04-03",
    "2027-04-04", "2027-04-05",
]
RETURN_DATES = [
    "2027-04-16", "2027-04-17", "2027-04-18", "2027-04-19",
]
MIN_TRIP_DAYS  = 14

ALERT_THRESHOLD_PP = 450   # AUD per person
MAX_PRICE_PP       = 1500  # AUD per person
MAX_STOPS          = 1
DELAY_BETWEEN_CALLS = 5

# ── CSV ───────────────────────────────────────────────────────────────────────
FIELDNAMES = ["timestamp", "outbound", "return", "trip_days", "airline",
              "duration", "stops", "total_aud", "per_person_aud",
              "cheapest_source", "book_link", "alert"]

def append_rows(rows):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    now    = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    client = ApifyClient(APIFY_TOKEN)
    new_rows = []
    alerts   = []

    # Build valid date combos (min 14 days apart)
    combos = [
        (out, ret)
        for out in OUTBOUND_DATES
        for ret in RETURN_DATES
        if (date.fromisoformat(ret) - date.fromisoformat(out)).days >= MIN_TRIP_DAYS
    ]

    print(f"Flight tracker — {now}")
    print(f"Route: {ORIGIN} → {DESTINATION} | {ADULTS} passengers | {CURRENCY}")
    print(f"Checking {len(combos)} date combos | max {MAX_STOPS} stop(s) | max ${MAX_PRICE_PP}/person\n")

    for out, ret in combos:
        trip_days = (date.fromisoformat(ret) - date.fromisoformat(out)).days
        print(f"  {out} → {ret} ({trip_days}d) ...", end=" ", flush=True)

        run_input = {
            "origin":      ORIGIN,
            "destination": DESTINATION,
            "departDate":  out,
            "returnDate":  ret,
            "adults":      ADULTS,
            "cabinClass":  CABIN,
            "currency":    CURRENCY,
            "maxFlights":  20,
        }

        try:
            run   = client.actor(ACTOR_ID).call(run_input=run_input)
            items = list(client.dataset(run.default_dataset_id).iterate_items())
        except Exception as e:
            print(f"error — {e}")
            time.sleep(DELAY_BETWEEN_CALLS)
            continue

        if not items:
            print("no results")
            time.sleep(DELAY_BETWEEN_CALLS)
            continue

        filtered = [
            i for i in items
            if i.get("stops", 99) <= MAX_STOPS
            and i.get("bestPrice") is not None
            and (i.get("bestPrice") / TOTAL_PAX) <= MAX_PRICE_PP
        ]

        if not filtered:
            print(f"no results after filtering ({len(items)} raw)")
            time.sleep(DELAY_BETWEEN_CALLS)
            continue

        cheapest        = min(filtered, key=lambda x: x.get("bestPrice", float("inf")))
        best_price      = cheapest.get("bestPrice")
        airline         = cheapest.get("airline", "unknown")
        duration        = cheapest.get("duration", "")
        stops           = cheapest.get("stops", "")
        cheapest_source = list(cheapest.get("prices", {}).keys())[0] if cheapest.get("prices") else "unknown"
        book_link       = (cheapest.get("links") or {}).get("googleFlights", "")

        per_person = round(best_price / TOTAL_PAX, 2)
        is_alert   = per_person < ALERT_THRESHOLD_PP
        flag       = "YES" if is_alert else ""

        print(f"{airline} | {duration} | {stops} stop(s) | ${best_price:.0f} total (${per_person:.0f}/person) {flag}")

        new_rows.append({
            "timestamp":       now,
            "outbound":        out,
            "return":          ret,
            "trip_days":       trip_days,
            "airline":         airline,
            "duration":        duration,
            "stops":           stops,
            "total_aud":       f"{best_price:.2f}",
            "per_person_aud":  f"{per_person:.2f}",
            "cheapest_source": cheapest_source,
            "book_link":       book_link,
            "alert":           flag,
        })

        if is_alert:
            alerts.append(
                f"  🔔 {airline} | {out} → {ret} ({trip_days}d) | "
                f"${best_price:.0f} total (${per_person:.0f}/person)"
            )

        time.sleep(DELAY_BETWEEN_CALLS)

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

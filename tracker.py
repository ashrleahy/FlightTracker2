import os
import csv
import time
from datetime import datetime
from apify_client import ApifyClient

# ── Config ────────────────────────────────────────────────────────────────────
APIFY_TOKEN  = os.environ["APIFY_TOKEN"]
ACTOR_ID     = "makework36/flight-price-scraper"

ORIGIN       = "ADL"
DESTINATION  = "DPS"
CURRENCY     = "AUD"
ADULTS       = 2
CABIN        = "ECONOMY"
CSV_FILE     = "flight_log.csv"

# Note: Apify actor handles children differently — we'll track 2 adults
# and note the child separately since the API uses adults count only
# Total pax for per-person calc = 3
TOTAL_PAX    = 3

OUTBOUND_DATES = [
    "2027-04-03",
    "2027-04-10",
    "2027-04-24",
]
RETURN_DATE = "2027-04-24"

ALERT_THRESHOLD_PP = 450   # AUD per person

DELAY_BETWEEN_CALLS = 5    # seconds between actor runs

# ── CSV helpers ───────────────────────────────────────────────────────────────
FIELDNAMES = ["timestamp", "outbound", "return", "total_aud", "per_person_aud",
              "best_price", "cheapest_source", "alert"]

def append_rows(rows):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    now     = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    client  = ApifyClient(APIFY_TOKEN)
    new_rows = []
    alerts   = []

    print(f"Flight tracker — {now}")
    print(f"Route: {ORIGIN} → {DESTINATION} | {ADULTS} adults + 1 child | {CURRENCY}\n")

    for out in OUTBOUND_DATES:
        print(f"  Checking {out} → {RETURN_DATE} ...", end=" ", flush=True)

        run_input = {
            "origin":      ORIGIN,
            "destination": DESTINATION,
            "departDate":  out,
            "returnDate":  RETURN_DATE,
            "adults":      ADULTS,
            "cabinClass":  CABIN,
            "currency":    CURRENCY,
            "maxFlights":  10,
        }

        try:
            run = client.actor(ACTOR_ID).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        except Exception as e:
            print(f"error — {e}")
            time.sleep(DELAY_BETWEEN_CALLS)
            continue

        if not items:
            print("no results")
            time.sleep(DELAY_BETWEEN_CALLS)
            continue

        # Find cheapest flight across all results
        cheapest = min(items, key=lambda x: x.get("bestPrice", float("inf")))
        best_price      = cheapest.get("bestPrice")
        cheapest_source = cheapest.get("cheapestSource", "unknown")

        if best_price is None:
            print("no price data")
            time.sleep(DELAY_BETWEEN_CALLS)
            continue

        # bestPrice is for ADULTS only — scale to total pax
        per_person = round(best_price / ADULTS * TOTAL_PAX / TOTAL_PAX, 2)
        # Actually bestPrice is per-person already on some sources, let's store raw + per_pax
        total      = round(best_price * ADULTS, 2)   # approximate total for 2 adults
        per_person = round(total / TOTAL_PAX, 2)

        is_alert = per_person < ALERT_THRESHOLD_PP
        flag     = "YES" if is_alert else ""

        print(f"${total:.0f} total  (${per_person:.0f}/person)  via {cheapest_source} {flag}")

        new_rows.append({
            "timestamp":       now,
            "outbound":        out,
            "return":          RETURN_DATE,
            "total_aud":       f"{total:.2f}",
            "per_person_aud":  f"{per_person:.2f}",
            "best_price":      f"{best_price:.2f}",
            "cheapest_source": cheapest_source,
            "alert":           flag,
        })

        if is_alert:
            alerts.append(
                f"  🔔 CHEAP FARE: {out} out / {RETURN_DATE} return — "
                f"${total:.0f} total (${per_person:.0f}/person) via {cheapest_source}"
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

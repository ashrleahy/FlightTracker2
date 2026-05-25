import os
import csv
import time
from datetime import datetime, date
from apify_client import ApifyClient

# ── Config ────────────────────────────────────────────────────────────────────
APIFY_TOKEN  = os.environ["APIFY_TOKEN"]
ACTOR_ID     = "makework36/flight-price-scraper"

ORIGIN       = "ADL"
DESTINATION  = "NAN"   # Nadi, Fiji
CURRENCY     = "AUD"
ADULTS       = 1
CABIN        = "ECONOMY"
CSV_FILE     = "fiji_log.csv"

COMBOS = [
    ("2027-07-03", "2027-07-18", "Fiji July"),
]

ALERT_THRESHOLD = 600    # AUD per adult — alert if cheaper
MAX_PRICE       = 3000
MAX_STOPS       = 1
SKIP_SOURCES    = {"cached"}
DELAY_BETWEEN_CALLS = 5

# ── Search link ───────────────────────────────────────────────────────────────
def search_link(out, ret):
    return (
        f"https://www.google.com/travel/flights?q=Flights+to+NAN+from+ADL"
        f"+on+{out}+returning+{ret}&curr=AUD"
    )

# ── CSV ───────────────────────────────────────────────────────────────────────
FIELDNAMES = ["timestamp", "route", "outbound", "return", "trip_days",
              "airline", "duration", "stops", "price_aud", "source",
              "search_link", "alert"]

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

    print(f"Fiji flight tracker — {now}")
    print(f"Route: {ORIGIN} → {DESTINATION} | 1 adult | {CURRENCY}\n")

    for out, ret, label in COMBOS:
        trip_days = (date.fromisoformat(ret) - date.fromisoformat(out)).days
        print(f"  [{label}] {out} → {ret} ({trip_days}d) ...", end=" ", flush=True)

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

        # Debug raw results
        print(f"\n    Raw results ({len(items)}):")
        for i in items:
            sources = set(i.get("prices", {}).keys())
            print(f"      {i.get('airline','?')} | {i.get('stops','?')} stops | "
                  f"${i.get('bestPrice','?')} | {i.get('duration','?')} | src: {sources}")

        filtered = [
            i for i in items
            if set(i.get("prices", {}).keys()) > SKIP_SOURCES
            and i.get("stops", 99) <= MAX_STOPS
            and i.get("bestPrice") is not None
            and i.get("bestPrice") <= MAX_PRICE
        ]

        if not filtered:
            print(f"    → no results after filtering ({len(items)} raw)")
            time.sleep(DELAY_BETWEEN_CALLS)
            continue

        cheapest   = min(filtered, key=lambda x: x.get("bestPrice", float("inf")))
        price      = cheapest.get("bestPrice")
        airline    = cheapest.get("airline", "unknown")
        duration   = cheapest.get("duration", "")
        stops      = cheapest.get("stops", "")
        sources    = ", ".join(cheapest.get("prices", {}).keys())
        is_alert   = price < ALERT_THRESHOLD
        flag       = "YES" if is_alert else ""

        print(f"    → {airline} | {duration} | {stops} stop(s) | ${price:.0f} {flag}")

        new_rows.append({
            "timestamp":   now,
            "route":       f"{ORIGIN}→{DESTINATION}",
            "outbound":    out,
            "return":      ret,
            "trip_days":   trip_days,
            "airline":     airline,
            "duration":    duration,
            "stops":       stops,
            "price_aud":   f"{price:.2f}",
            "source":      sources,
            "search_link": search_link(out, ret),
            "alert":       flag,
        })

        if is_alert:
            alerts.append(f"  🔔 [{label}] {airline} | {out} → {ret} | ${price:.0f}/adult")

        time.sleep(DELAY_BETWEEN_CALLS)

    if new_rows:
        append_rows(new_rows)
        print(f"\n✓ Logged {len(new_rows)} price points to {CSV_FILE}")
    else:
        print("\n⚠ No prices retrieved.")

    if alerts:
        print("\n" + "="*55)
        print("PRICE ALERTS!")
        for a in alerts:
            print(a)
        print(f"  Threshold: ${ALERT_THRESHOLD}/adult")
        print("="*55)

if __name__ == "__main__":
    main()

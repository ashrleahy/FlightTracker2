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
ADULTS       = 1
CABIN        = "ECONOMY"
CSV_FILE     = "flight_log.csv"

# 1st preference: 18 Apr out, 2 May return
# 2nd preference: 16 Apr out, 1 May return
COMBOS = [
    ("2027-04-18", "2027-05-02", "1st preference"),
    ("2027-04-16", "2027-05-01", "2nd preference"),
]

ALERT_THRESHOLD = 500    # AUD per adult — alert if cheaper
MAX_PRICE       = 1500   # AUD per adult — filter garbage
MAX_STOPS       = 1
SKIP_SOURCES    = {"cached"}
DELAY_BETWEEN_CALLS = 5

# ── Jetstar deep link ─────────────────────────────────────────────────────────
def jetstar_link(out: str, ret: str) -> str:
    d_out = datetime.strptime(out, "%Y-%m-%d").strftime("%d%m%y")
    d_ret = datetime.strptime(ret, "%Y-%m-%d").strftime("%d%m%y")
    return (
        f"https://www.jetstar.com/au/en/flights?origin={ORIGIN}"
        f"&destination={DESTINATION}"
        f"&departure-date={d_out}&return-date={d_ret}"
        f"&adult=1&child=0&infant=0&trip-type=R&cabin-class=E"
    )

# ── CSV ───────────────────────────────────────────────────────────────────────
FIELDNAMES = ["timestamp", "preference", "outbound", "return", "trip_days",
              "airline", "duration", "stops", "price_aud", "source",
              "jetstar_link", "alert"]

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

    print(f"Flight tracker — {now}")
    print(f"Route: {ORIGIN} → {DESTINATION} | 1 adult | {CURRENCY}\n")

    for out, ret, pref in COMBOS:
        trip_days = (date.fromisoformat(ret) - date.fromisoformat(out)).days
        print(f"  [{pref}] {out} → {ret} ({trip_days}d) ...", end=" ", flush=True)

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

        filtered = []
        for i in items:
            sources = set(i.get("prices", {}).keys())
            if sources <= SKIP_SOURCES:
                continue
            if i.get("stops", 99) > MAX_STOPS:
                continue
            if i.get("bestPrice") is None:
                continue
            if i.get("bestPrice") > MAX_PRICE:
                continue
            filtered.append(i)

        if not filtered:
            print(f"no results after filtering ({len(items)} raw)")
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

        print(f"{airline} | {duration} | {stops} stop(s) | ${price:.0f} {flag}")

        new_rows.append({
            "timestamp":    now,
            "preference":   pref,
            "outbound":     out,
            "return":       ret,
            "trip_days":    trip_days,
            "airline":      airline,
            "duration":     duration,
            "stops":        stops,
            "price_aud":    f"{price:.2f}",
            "source":       sources,
            "jetstar_link": jetstar_link(out, ret),
            "alert":        flag,
        })

        if is_alert:
            alerts.append(
                f"  🔔 [{pref}] {airline} | {out} → {ret} | ${price:.0f}/adult"
            )

        time.sleep(DELAY_BETWEEN_CALLS)

    if new_rows:
        append_rows(new_rows)
        print(f"\n✓ Logged {len(new_rows)} price points to {CSV_FILE}")
    else:
        print("\n⚠ No prices retrieved — all filtered out (cached only).")

    if alerts:
        print("\n" + "="*55)
        print("PRICE ALERTS — fares below threshold!")
        for a in alerts:
            print(a)
        print(f"  Threshold: ${ALERT_THRESHOLD}/adult")
        print("="*55)

if __name__ == "__main__":
    main()

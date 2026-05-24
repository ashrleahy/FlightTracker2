import os
import csv
import time
from datetime import datetime
from apify_client import ApifyClient

# ── Config ────────────────────────────────────────────────────────────────────
APIFY_TOKEN  = os.environ["APIFY_TOKEN"]
ACTOR_ID     = "solidcode/booking-scraper"
CSV_FILE     = "hotel_log.csv"

ADULTS   = 2
CHILDREN = 1
CHILD_AGES = [9]
ROOMS    = 1
CURRENCY = "AUD"

# ── Hotels to track ───────────────────────────────────────────────────────────
HOTELS = [
    {
        "name":     "Andaz Bali",
        "location": "Sanur",
        "url":      "https://www.booking.com/hotel/id/andaz-bali-a-concept-by-hyatt.en-gb.html",
        "checkin":  "2027-04-18",
        "checkout": "2027-04-21",
        "nights":   3,
    },
    {
        "name":     "Villa Tokay",
        "location": "Gili Air",
        "url":      "https://www.booking.com/hotel/id/villa-tokay.en-gb.html",
        "checkin":  "2027-04-21",
        "checkout": "2027-04-27",
        "nights":   6,
    },
    {
        "name":     "BASK Gili Meno",
        "location": "Gili Meno",
        "url":      "https://www.booking.com/hotel/id/bask-gili-meno.en-gb.html",
        "checkin":  "2027-04-27",
        "checkout": "2027-05-02",
        "nights":   5,
    },
]

DELAY_BETWEEN_CALLS = 10   # booking.com is slower than flights

# ── CSV ───────────────────────────────────────────────────────────────────────
FIELDNAMES = ["timestamp", "hotel", "location", "checkin", "checkout",
              "nights", "price_total", "price_per_night", "rating",
              "availability", "booking_url", "alert"]

ALERT_THRESHOLDS = {
    "Andaz Bali":    800,    # AUD per night alert threshold
    "Villa Tokay":   400,
    "BASK Gili Meno": 500,
}

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

    print(f"Hotel tracker — {now}")
    print(f"Guests: {ADULTS} adults + {CHILDREN} child (age {CHILD_AGES[0]}) | {CURRENCY}\n")

    for hotel in HOTELS:
        name     = hotel["name"]
        checkin  = hotel["checkin"]
        checkout = hotel["checkout"]
        nights   = hotel["nights"]

        print(f"  [{name}] {checkin} → {checkout} ({nights} nights) ...", end=" ", flush=True)

        run_input = {
            "urls":          [hotel["url"]],
            "checkinDate":   checkin,
            "checkoutDate":  checkout,
            "adults":        ADULTS,
            "children":      CHILDREN,
            "childrenAges":  CHILD_AGES,
            "rooms":         ROOMS,
            "currency":      CURRENCY,
            "language":      "en-gb",
            "maxResults":    5,
            "includeRoomDetails": False,
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

        # Debug — show raw fields on first run
        print(f"\n    Raw keys: {list(items[0].keys())[:12]}")

        # Find the matching hotel (URL-based search returns 1 result usually)
        result      = items[0]
        price_total = result.get("price") or result.get("priceTotal") or result.get("totalPrice")
        price_night = result.get("pricePerNight") or result.get("price_per_night")
        rating      = result.get("rating") or result.get("reviewScore") or result.get("score")
        avail       = result.get("available", True)
        book_url    = result.get("url") or result.get("bookingUrl") or hotel["url"]

        # Calculate per night if not provided
        if price_total and not price_night and nights:
            price_night = round(price_total / nights, 2)
        elif price_night and not price_total and nights:
            price_total = round(price_night * nights, 2)

        threshold = ALERT_THRESHOLDS.get(name, 9999)
        is_alert  = price_night and price_night < threshold
        flag      = "YES" if is_alert else ""

        if price_night:
            print(f"${price_night:.0f}/night | ${price_total:.0f} total | rating: {rating} {flag}")
        else:
            print(f"no price (raw: {result.get('price')}, {result.get('priceTotal')})")

        new_rows.append({
            "timestamp":      now,
            "hotel":          name,
            "location":       hotel["location"],
            "checkin":        checkin,
            "checkout":       checkout,
            "nights":         nights,
            "price_total":    f"{price_total:.2f}" if price_total else "",
            "price_per_night": f"{price_night:.2f}" if price_night else "",
            "rating":         rating or "",
            "availability":   "yes" if avail else "no",
            "booking_url":    book_url,
            "alert":          flag,
        })

        time.sleep(DELAY_BETWEEN_CALLS)

    if new_rows:
        append_rows(new_rows)
        print(f"\n✓ Logged {len(new_rows)} hotel prices to {CSV_FILE}")
    else:
        print("\n⚠ No hotel prices retrieved.")

if __name__ == "__main__":
    main()

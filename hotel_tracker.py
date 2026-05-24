import os
import csv
import time
from datetime import datetime
from apify_client import ApifyClient

# ── Config ────────────────────────────────────────────────────────────────────
APIFY_TOKEN  = os.environ["APIFY_TOKEN"]
ACTOR_ID     = "solidcode/booking-scraper"
CSV_FILE     = "hotel_log.csv"
CURRENCY     = "AUD"

# Full Booking.com URLs with dates and guests baked in
HOTELS = [
    {
        "name":     "Andaz Bali",
        "location": "Sanur",
        "checkin":  "2027-04-18",
        "checkout": "2027-04-21",
        "nights":   3,
        "url": "https://www.booking.com/hotel/id/andaz-bali.en-gb.html?aid=304142&label=gen173nr-10CAEoggI46AdIM1gEaA-IAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4AoyMztAGwAIB0gIkYjk2NzkzMzEtZGFiYi00NzdjLTk5NTYtOGUyNTVmN2E3Njgx2AIB4AIB&sid=d6ebb216969785e7ce53124a7d1e4c68&age=9&all_sr_blocks=636811611_249878706_2_2_0&checkin=2027-04-18&checkout=2027-04-21&dest_id=6368116&dest_type=hotel&dist=0&group_adults=2&group_children=1&hapos=1&highlighted_blocks=636811611_249878706_2_2_0&hpos=1&matching_block_id=636811611_249878706_2_2_0&no_rooms=1&req_adults=2&req_age=9&req_children=1&room1=A%2CA%2C9&sb_price_type=total&sr_order=popularity&sr_pri_blocks=636811611_249878706_2_2_0__2027921293&srepoch=1779666480&srpvid=947ba755fed200d2&type=total&ucfs=1&",
    },
    {
        "name":     "Villa Tokay",
        "location": "Gili Air",
        "checkin":  "2027-04-21",
        "checkout": "2027-04-27",
        "nights":   6,
        "url": "https://www.booking.com/hotel/id/villa-tokay.en-gb.html?aid=304142&label=gen173nr-10CAEoggI46AdIM1gEaA-IAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4AoyMztAGwAIB0gIkYjk2NzkzMzEtZGFiYi00NzdjLTk5NTYtOGUyNTVmN2E3Njgx2AIB4AIB&sid=d6ebb216969785e7ce53124a7d1e4c68&age=9&all_sr_blocks=893104901_378080555_2_1_66520453480448_1346341&checkin=2027-04-21&checkout=2027-04-27&dest_id=900048668&dest_type=city&dist=0&group_adults=2&group_children=1&hapos=12&highlighted_blocks=893104901_378080555_2_1_66520453480448_1346341&hpos=12&matching_block_id=893104901_378080555_2_1_66520453480448_1346341&no_rooms=1&req_adults=2&req_age=9&req_children=1&room1=A%2CA%2C9&sb_price_type=total&sr_order=popularity&sr_pri_blocks=893104901_378080555_2_1_66520453480448_1346341_3584250000&srepoch=1779664477&srpvid=2eefa365955d0202&type=total&ucfs=1&",
    },
    {
        "name":     "BASK Gili Meno",
        "location": "Gili Meno",
        "checkin":  "2027-04-27",
        "checkout": "2027-05-01",
        "nights":   4,
        "url": "https://www.booking.com/hotel/id/bask-gili-meno.en-gb.html?aid=304142&label=gen173nr-10CAEoggI46AdIM1gEaA-IAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4AoyMztAGwAIB0gIkYjk2NzkzMzEtZGFiYi00NzdjLTk5NTYtOGUyNTVmN2E3Njgx2AIB4AIB&sid=d6ebb216969785e7ce53124a7d1e4c68&age=9&all_sr_blocks=1021977803_430867179_4_2_0_819470&checkin=2027-04-27&checkout=2027-05-01&dest_id=10219778&dest_type=hotel&dist=0&group_adults=2&group_children=1&hapos=1&highlighted_blocks=1021977803_430867179_4_2_0_819470&hpos=1&matching_block_id=1021977803_430867179_4_2_0_819470&no_rooms=1&req_adults=2&req_age=9&req_children=1&room1=A%2CA%2C9&sb_price_type=total&sr_order=popularity&sr_pri_blocks=1021977803_430867179_4_2_0_819470_2957100000&srepoch=1779666546&srpvid=4e6fa7733373018c&type=total&ucfs=1&",
    },
]

ALERT_THRESHOLDS = {
    "Andaz Bali":     800,
    "Villa Tokay":    400,
    "BASK Gili Meno": 500,
}

DELAY_BETWEEN_CALLS = 10

# ── CSV ───────────────────────────────────────────────────────────────────────
FIELDNAMES = ["timestamp", "hotel", "location", "checkin", "checkout",
              "nights", "price_total", "price_per_night", "rating",
              "availability", "booking_url", "alert"]

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
    print(f"2 adults + 1 child (age 9) | {CURRENCY}\n")

    for hotel in HOTELS:
        name    = hotel["name"]
        nights  = hotel["nights"]

        print(f"  [{name}] {hotel['checkin']} → {hotel['checkout']} ({nights} nights) ...", end=" ", flush=True)

        run_input = {
            "startUrls": [{"url": hotel["url"]}],
            "currency":  CURRENCY,
            "language":  "en-gb",
            "maxResults": 3,
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

        result      = items[0]
        price_total = result.get("price")
        rating      = result.get("rating")
        avail       = result.get("available", True)
        book_url    = result.get("bookingUrl") or hotel["url"]

        price_night = round(float(price_total) / nights, 2) if price_total else None

        threshold = ALERT_THRESHOLDS.get(name, 9999)
        is_alert  = price_night and float(price_night) < threshold
        flag      = "YES" if is_alert else ""

        if price_night:
            print(f"${price_night:.0f}/night | ${price_total:.0f} total | rating: {rating} {flag}")
        else:
            print(f"no price yet (rating: {rating})")

        new_rows.append({
            "timestamp":       now,
            "hotel":           name,
            "location":        hotel["location"],
            "checkin":         hotel["checkin"],
            "checkout":        hotel["checkout"],
            "nights":          nights,
            "price_total":     f"{float(price_total):.2f}" if price_total else "",
            "price_per_night": f"{price_night:.2f}" if price_night else "",
            "rating":          rating or "",
            "availability":    "yes" if avail else "no",
            "booking_url":     book_url,
            "alert":           flag,
        })

        time.sleep(DELAY_BETWEEN_CALLS)

    if new_rows:
        append_rows(new_rows)
        print(f"\n✓ Logged {len(new_rows)} hotel prices to {CSV_FILE}")
    else:
        print("\n⚠ No results retrieved.")

if __name__ == "__main__":
    main()

import os
import csv
import time
import re
import requests
from datetime import datetime
from apify_client import ApifyClient

# ── Config ────────────────────────────────────────────────────────────────────
APIFY_TOKEN  = os.environ["APIFY_TOKEN"]
ACTOR_ID     = "solidcode/booking-scraper"
CSV_FILE     = "hotel_log.csv"
CURRENCY     = "AUD"

# Exchange rate IDR → AUD (approximate, updated periodically)
# 1 AUD ≈ 10,500 IDR as of May 2026
IDR_TO_AUD = 12667

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

# ── Extract price from URL ────────────────────────────────────────────────────
def extract_price_from_url(url: str, nights: int) -> tuple[float | None, float | None]:
    """Extract IDR price from sr_pri_blocks URL param and convert to AUD."""
    match = re.search(r'sr_pri_blocks=[^&]*?_(\d{6,})(?:&|$)', url)
    if not match:
        return None, None
    idr_total = int(match.group(1)) // 100  # IDR hundredths
    if idr_total == 0:
        return None, None
    aud_total = round(idr_total / IDR_TO_AUD, 2)
    aud_night = round(aud_total / nights, 2)
    return aud_total, aud_night

# ── Get live IDR→AUD rate ─────────────────────────────────────────────────────
def get_idr_aud_rate() -> float:
    try:
        r = requests.get(
            "https://api.frankfurter.app/latest?from=IDR&to=AUD",
            timeout=5
        )
        rate = r.json()["rates"]["AUD"]
        print(f"  Live IDR→AUD rate: {rate:.8f} (1 IDR = {rate:.8f} AUD)")
        return 1 / rate  # we need IDR per AUD
    except Exception:
        print(f"  Could not fetch live rate, using fallback: {IDR_TO_AUD}")
        return IDR_TO_AUD

# ── CSV ───────────────────────────────────────────────────────────────────────
FIELDNAMES = ["timestamp", "hotel", "location", "checkin", "checkout",
              "nights", "price_total_aud", "price_per_night_aud", "rating",
              "price_source", "booking_url", "alert"]

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

    # Get live exchange rate
    idr_per_aud = get_idr_aud_rate()
    print()

    for hotel in HOTELS:
        name   = hotel["name"]
        nights = hotel["nights"]

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

        result  = items[0]
        rating  = result.get("rating")
        returned_url = result.get("url") or hotel["url"]

        # Try actor price field first, fall back to URL extraction
        price_total = result.get("price")
        price_source = "api"

        if price_total:
            price_night = round(float(price_total) / nights, 2)
        else:
            # Extract from URL param (IDR → AUD)
            price_total, price_night = extract_price_from_url(hotel["url"], nights)
            if price_total:
                # Recalculate with live rate
                match = re.search(r'sr_pri_blocks=[^&]*?_(\d{6,})(?:&|$)', hotel["url"])
                if match:
                    idr_total   = int(match.group(1)) // 100  # value is in IDR hundredths
                    price_total = round(idr_total / idr_per_aud, 2)
                    price_night = round(price_total / nights, 2)
                price_source = "url-idr"

        threshold = ALERT_THRESHOLDS.get(name, 9999)
        is_alert  = price_night and float(price_night) < threshold
        flag      = "YES" if is_alert else ""

        if price_night:
            print(f"${price_night:.0f}/night | ${price_total:.0f} total | rating: {rating} | src: {price_source} {flag}")
        else:
            print(f"no price (rating: {rating})")

        new_rows.append({
            "timestamp":          now,
            "hotel":              name,
            "location":           hotel["location"],
            "checkin":            hotel["checkin"],
            "checkout":           hotel["checkout"],
            "nights":             nights,
            "price_total_aud":    f"{float(price_total):.2f}" if price_total else "",
            "price_per_night_aud": f"{float(price_night):.2f}" if price_night else "",
            "rating":             rating or "",
            "price_source":       price_source if price_total else "none",
            "booking_url":        returned_url,
            "alert":              flag,
        })

        time.sleep(DELAY_BETWEEN_CALLS)

    if new_rows:
        append_rows(new_rows)
        print(f"\n✓ Logged {len(new_rows)} hotel prices to {CSV_FILE}")
    else:
        print("\n⚠ No results retrieved.")

if __name__ == "__main__":
    main()

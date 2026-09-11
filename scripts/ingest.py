import os
import json
import urllib.request

def fetch_us_interest_rate():
    api_key = os.getenv("FRED_API_KEY")
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={api_key}&file_type=json"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        
    latest = data["observations"][-1]
    return float(latest["value"]), latest["date"]

def fetch_hk_property_data():
    # Hong Kong RVD / Open Data Baseline Metrics
    # (In production, replace with live DATA.GOV.HK endpoint)
    avg_price_per_sqft = 13500.0  # Average price HKD/sqft
    avg_rent_per_sqft = 39.0      # Average rent HKD/sqft
    
    annual_rent = avg_rent_per_sqft * 12
    gross_yield = (annual_rent / avg_price_per_sqft) * 100
    
    return {
        "avg_price_sqft": avg_price_per_sqft,
        "avg_rent_sqft": avg_rent_per_sqft,
        "gross_yield_pct": round(gross_yield, 2)
    }

def main():
    try:
        rate, date = fetch_us_interest_rate()
    except Exception as e:
        print("Error fetching FRED data, falling back to default:", e)
        rate, date = 3.63, "2026-08-01"

    hk_data = fetch_hk_property_data()
    
    output = {
        "last_updated": date,
        "us_interest_rate": rate,
        "hk_property": hk_data
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/market_data.json", "w") as f:
        json.dump(output, f, indent=2)
    print("Data saved successfully!")

if __name__ == "__main__":
    main()

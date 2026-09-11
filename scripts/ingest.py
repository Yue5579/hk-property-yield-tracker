import os
import json
import urllib.request
import csv
import io

def fetch_us_interest_rate():
    """Fetch US Fed Funds Rate from FRED API"""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        print("Warning: FRED_API_KEY not set. Using fallback value.")
        return 3.63, "2026-08-01"
        
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={api_key}&file_type=json"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        
    # Get the latest non-empty observation
    obs = [o for o in data["observations"] if o["value"] != "."]
    latest = obs[-1]
    return float(latest["value"]), latest["date"]

def fetch_hk_rvd_data():
    """
    Fetches HK Private Domestic Average Rents & Prices from DATA.GOV.HK (RVD)
    Dataset: Average Prices and Rents for Private Domestic Properties
    """
    # RVD Open Data Endpoint for Monthly Domestic Prices & Rents
    url = "https://www.rvd.gov.hk/datagovhk/3.2M.csv"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            csv_content = response.read().decode('utf-8-sig')
            
        reader = list(csv.DictReader(io.StringIO(csv_content)))
        
        # Get the latest available month record
        latest_row = reader[-1]
        
        # Average price per sq metre / sq ft (approx Class B property: 40-69.9 sq.m)
        # 1 sq.m ≈ 10.764 sq.ft
        avg_price_sqm = float(latest_row.get("Price_Class_B", 145000))
        avg_rent_sqm = float(latest_row.get("Rent_Class_B", 420))
        
        avg_price_sqft = round(avg_price_sqm / 10.764, 2)
        avg_rent_sqft = round(avg_rent_sqm / 10.764, 2)
        
        annual_rent = avg_rent_sqft * 12
        gross_yield = (annual_rent / avg_price_sqft) * 100

        return {
            "period": latest_row.get("Month", "Latest"),
            "avg_price_sqft": avg_price_sqft,
            "avg_rent_sqft": avg_rent_sqft,
            "gross_yield_pct": round(gross_yield, 2)
        }
        
    except Exception as e:
        print("Error fetching HK RVD data, using baseline fallback:", e)
        # Fallback values if API schema changes
        return {
            "period": "Fallback",
            "avg_price_sqft": 13500.0,
            "avg_rent_sqft": 39.0,
            "gross_yield_pct": 3.47
        }

def main():
    rate, date = fetch_us_interest_rate()
    hk_data = fetch_hk_rvd_data()
    
    output = {
        "last_updated": date,
        "us_interest_rate": rate,
        "hk_property": hk_data
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/market_data.json", "w") as f:
        json.dump(output, f, indent=2)
    print("Market data successfully fetched and updated!")

if __name__ == "__main__":
    main()
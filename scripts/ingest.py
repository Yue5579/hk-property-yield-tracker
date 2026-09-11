import os
import json
import urllib.request
import csv
import io

def fetch_us_interest_history():
    """Fetch monthly historical US Fed Funds Rates from FRED API"""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        print("FRED_API_KEY not found. Using fallback history.")
        return {"2024-01": 5.33, "2024-06": 5.33, "2025-01": 4.50, "2025-06": 4.00, "2026-01": 3.75, "2026-08": 3.63}

    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={api_key}&file_type=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        rates = {}
        for obs in data.get("observations", []):
            if obs["value"] != ".":
                # Convert '2024-01-01' to '2024-01'
                month_key = obs["date"][:7]
                rates[month_key] = float(obs["value"])
        return rates
    except Exception as e:
        print("Error fetching FRED historical data:", e)
        return {}

def fetch_hk_rvd_history():
    """Fetch monthly historical HK RVD Price & Rent data"""
    url = "https://www.rvd.gov.hk/datagovhk/3.2M.csv"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    history = {}
    try:
        with urllib.request.urlopen(req) as response:
            csv_content = response.read().decode('utf-8-sig')
            
        reader = list(csv.DictReader(io.StringIO(csv_content)))
        
        for row in reader:
            month_raw = row.get("Month", "")  # Expected format e.g. "202401" or "2024/01" or "2024-01"
            if not month_raw:
                continue
            
            # Format month as YYYY-MM
            cleaned_month = month_raw.replace("/", "").replace("-", "")
            if len(cleaned_month) == 6:
                month_key = f"{cleaned_month[:4]}-{cleaned_month[4:]}"
            else:
                month_key = month_raw

            try:
                price_sqm = float(row.get("Price_Class_B", 0))
                rent_sqm = float(row.get("Rent_Class_B", 0))
                
                if price_sqm > 0 and rent_sqm > 0:
                    price_sqft = round(price_sqm / 10.764, 2)
                    rent_sqft = round(rent_sqm / 10.764, 2)
                    gross_yield = round(((rent_sqft * 12) / price_sqft) * 100, 2)

                    history[month_key] = {
                        "price_sqft": price_sqft,
                        "rent_sqft": rent_sqft,
                        "gross_yield_pct": gross_yield
                    }
            except ValueError:
                continue
                
        return history
    except Exception as e:
        print("Error fetching HK RVD historical data:", e)
        return {}

def main():
    fed_rates = fetch_us_interest_history()
    hk_history = fetch_hk_rvd_history()
    
    # Merge datasets on matching YYYY-MM
    combined = []
    for month in sorted(hk_history.keys()):
        hk_item = hk_history[month]
        us_rate = fed_rates.get(month, None)
        
        combined.append({
            "month": month,
            "avg_price_sqft": hk_item["price_sqft"],
            "avg_rent_sqft": hk_item["rent_sqft"],
            "gross_yield_pct": hk_item["gross_yield_pct"],
            "us_fed_rate": us_rate
        })
    
    # Store latest 24 months for cleaner frontend visualization
    recent_trend = combined[-24:] if len(combined) >= 24 else combined

    output = {
        "last_updated": recent_trend[-1]["month"] if recent_trend else "N/A",
        "trend": recent_trend
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/market_data.json", "w") as f:
        json.dump(output, f, indent=2)
    print("Historical trend data successfully generated!")

if __name__ == "__main__":
    main()
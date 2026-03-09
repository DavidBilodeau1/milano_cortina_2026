#!/usr/bin/env python3
"""Test script to verify Paralympics API connectivity and data structure."""

import asyncio
import aiohttp
import json
from typing import Any


# API Configuration
OLYMPICS_BASE_URL = "https://www.olympics.com/wmr-owg2026/competition/api"
PARALYMPICS_BASE_URL = "https://www.olympics.com/wmr-para-owg2026/competition/api"
API_ENDPOINT = "medals"
LOCALE = "ENG"  # Can be ENG or FRA


async def test_api(base_url: str, event_name: str) -> dict[str, Any] | None:
    """Test API connectivity and return data."""
    url = f"{base_url}/{LOCALE}/{API_ENDPOINT}"
    
    headers = {
        "User-Agent": "HomeAssistant/Milano-Cortina-2026",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    connector = aiohttp.TCPConnector(force_close=True, enable_cleanup_closed=True)
    timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
    
    print(f"\n{'='*60}")
    print(f"Testing {event_name} API")
    print(f"{'='*60}")
    print(f"URL: {url}")
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                print(f"Status Code: {response.status}")
                
                if response.status != 200:
                    print(f"❌ Error: API returned status {response.status}")
                    return None
                
                data = await response.json()
                
                # Validate response structure
                if "medalStandings" not in data:
                    print("❌ Error: Invalid API response structure (missing 'medalStandings')")
                    return None
                
                print("✅ API connection successful!")
                
                # Display summary information
                medal_standings = data.get("medalStandings", {})
                event_info = medal_standings.get("eventInfo", {})
                medals_table = medal_standings.get("medalsTable", [])
                
                print(f"\nEvent Information:")
                print(f"  Total Events: {event_info.get('totalEvents', 'N/A')}")
                print(f"  Finished Events: {event_info.get('finishedEvents', 'N/A')}")
                print(f"  Last Update: {event_info.get('dateTime', 'N/A')}")
                
                print(f"\nMedal Standings:")
                print(f"  Countries with medals: {len(medals_table)}")
                
                if medals_table:
                    print(f"\n  Top 5 Countries:")
                    for i, country in enumerate(medals_table[:5], 1):
                        medals_number = country.get("medalsNumber", [])
                        total_medals = {}
                        for medal_type in medals_number:
                            if medal_type.get("type") == "Total":
                                total_medals = {
                                    "gold": medal_type.get("gold", 0),
                                    "silver": medal_type.get("silver", 0),
                                    "bronze": medal_type.get("bronze", 0),
                                    "total": medal_type.get("total", 0),
                                }
                                break
                        
                        print(f"    {i}. {country.get('description', 'Unknown')} ({country.get('organisation', 'N/A')})")
                        print(f"       🥇 {total_medals.get('gold', 0)} | "
                              f"🥈 {total_medals.get('silver', 0)} | "
                              f"🥉 {total_medals.get('bronze', 0)} | "
                              f"Total: {total_medals.get('total', 0)}")
                
                return data
                
    except aiohttp.ClientError as err:
        print(f"❌ Connection Error: {err}")
        return None
    except Exception as err:
        print(f"❌ Unexpected Error: {err}")
        return None


async def main():
    """Run tests for both Olympics and Paralympics APIs."""
    print("\n" + "="*60)
    print("Milano Cortina 2026 API Test Suite")
    print("="*60)
    
    # Test Olympics API
    olympics_data = await test_api(OLYMPICS_BASE_URL, "Olympics")
    
    # Test Paralympics API
    paralympics_data = await test_api(PARALYMPICS_BASE_URL, "Paralympics")
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"Olympics API:    {'✅ PASS' if olympics_data else '❌ FAIL'}")
    print(f"Paralympics API: {'✅ PASS' if paralympics_data else '❌ FAIL'}")
    
    # Save sample data to files for inspection
    if olympics_data:
        with open("olympics_sample_data.json", "w") as f:
            json.dump(olympics_data, f, indent=2)
        print(f"\n📄 Olympics sample data saved to: olympics_sample_data.json")
    
    if paralympics_data:
        with open("paralympics_sample_data.json", "w") as f:
            json.dump(paralympics_data, f, indent=2)
        print(f"📄 Paralympics sample data saved to: paralympics_sample_data.json")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())


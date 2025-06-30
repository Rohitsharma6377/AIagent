import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

async def get_daily_trends(geo='US'):
    """
    Scrapes the daily trending topics from Google Trends.

    Args:
        geo (str): The two-letter country code for the trends region (e.g., 'US', 'IN').

    Returns:
        list: A list of trending topic strings, or an empty list if scraping fails.
    """
    print(f"Fetching daily trends from Google Trends for region: {geo}...")
    trends_list = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to the daily trends page
            url = f"https://trends.google.com/trends/trendingsearches/daily?geo={geo}"
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # This is the critical part: Wait for the specific element that holds the trend data.
            trends_container_selector = 'md-list.feed-list'
            await page.wait_for_selector(trends_container_selector, timeout=20000)
            
            # Extract the text from each trend item
            trend_elements = await page.query_selector_all('div.feed-item-header > a')
            
            if not trend_elements:
                print("Could not find trend elements. The page structure might have changed.")
                
            for element in trend_elements:
                trend_text = await element.inner_text()
                if trend_text:
                    trends_list.append(trend_text.strip())
            
            if trends_list:
                print(f"Successfully fetched {len(trends_list)} trends.")
            else:
                print("Failed to fetch trends. The list was empty.")

        except PlaywrightTimeoutError:
            print(f"Timeout while waiting for trends page to load for geo={geo}. The page may be slow, require a captcha, or has changed.")
            await page.screenshot(path=f'trends_timeout_error_{geo}.png')
            print(f"A screenshot 'trends_timeout_error_{geo}.png' has been saved for debugging.")
        except Exception as e:
            print(f"An error occurred while scraping Google Trends for geo={geo}: {e}")
            await page.screenshot(path=f'trends_general_error_{geo}.png')
            print(f"A screenshot 'trends_general_error_{geo}.png' has been saved for debugging.")
        finally:
            await browser.close()
            
    return trends_list

if __name__ == '__main__':
    # For direct testing of this module
    async def test_trends():
        print("--- Testing Google Trends Scraper ---")
        
        print("\n[1] Fetching for United States (US)...")
        us_trends = await get_daily_trends(geo='US')
        if us_trends:
            print("\nTop 5 US Trends:")
            for i, trend in enumerate(us_trends[:5]):
                print(f"  {i+1}. {trend}")
        else:
            print("  No trends found for US.")
        
        print("\n[2] Fetching for India (IN)...")
        in_trends = await get_daily_trends(geo='IN')
        if in_trends:
            print("\nTop 5 India Trends:")
            for i, trend in enumerate(in_trends[:5]):
                print(f"  {i+1}. {trend}")
        else:
            print("  No trends found for IN.")

    asyncio.run(test_trends()) 
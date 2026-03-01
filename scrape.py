from playwright.sync_api import sync_playwright

def main():
    # The 10 URLs we need to visit
    seeds = range(66, 76)
    urls = [f"https://sanand0.github.io/tdsdata/js_table/?seed={seed}" for seed in seeds]
    
    total_sum = 0

    print("Starting Playwright Scraper...")
    
    # Start the browser
    with sync_playwright() as p:
        # headless=True means the browser runs invisibly in the background
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in urls:
            print(f"Visiting {url}...")
            page.goto(url)
            
            # CRITICAL: Wait for the dynamic table to actually appear on the page
            page.wait_for_selector("table")
            
            # Find all table data cells (<td>) and get their text
            cells = page.locator("td").all_inner_texts()
            
            # Loop through every cell, turn it into a number, and add it to our total
            for cell in cells:
                text = cell.strip()
                if text.isdigit(): # Make sure it's actually a number
                    total_sum += int(text)
                    
        browser.close()
        
    # Print the final total so the auto-grader can find it in the logs!
    print(f"GRAND TOTAL SUM: {total_sum}")

if __name__ == "__main__":
    main()

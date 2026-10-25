**Swiggy & Zomato Menu Data Crawler**

**Description:**
Python scripts that extract a restaurant's menu from Swiggy or Zomato and save it to an Excel spreadsheet, along with the restaurant's name, address, rating and FSSAI license number.

Both scripts read the structured menu data the sites themselves load, instead of scraping CSS class names. The class names change with every site release, which is what broke the old script.

**Setup:**
```
pip install -r requirements.txt
```
The Swiggy script also needs Google Chrome installed. Selenium 4.6+ downloads the matching ChromeDriver automatically, so you don't have to configure a driver path.

**Run it from GitHub (nothing to install):**
1. Open the repo's **Actions** tab → **Scrape menu** → **Run workflow**.
2. Paste a Zomato restaurant URL and click **Run workflow**.
3. When the run finishes (about a minute), open it and download **menu-spreadsheets** under Artifacts.

Swiggy blocks requests from cloud servers, GitHub's included, so for Swiggy save the menu JSON from your browser (see below), upload it to the `swiggy-json/` folder on GitHub (**Add file → Upload files**), and the workflow runs on its own. You can fork the repo to get your own copy of the workflow.

**Usage:**

Zomato (no browser needed):
```
python zomato_scraper.py https://www.zomato.com/bangalore/<restaurant-slug>/order
```
Any Zomato restaurant URL works (`/info`, `/menu`, `/order` or the bare restaurant URL).

Swiggy (opens a Chrome window):
```
python swiggy_scraper.py https://www.swiggy.com/city/bangalore/<restaurant-slug>-rest<id>
```
Swiggy runs a bot check and shows menus by delivery location. If it asks for a location or shows a check, complete it in the Chrome window. The script waits up to 90 seconds for the menu to load. `--headless` hides the window, but Swiggy often blocks headless browsers.

Each Swiggy run also saves the raw menu response as `Swiggy_menu_response.json`. To re-process a saved response, including one copied from Chrome DevTools (Network tab → the `menu/pl?...` request → Response), run:
```
python swiggy_scraper.py --json Swiggy_menu_response.json
```

Run either script without a URL and it will ask for one.

**Output:**
`Swiggy_<Restaurant Name>_menu.xlsx` or `Zomato_<Restaurant Name>_menu.xlsx`, with:
- Restaurant details: name, address, rating, FSSAI license number, source URL
- Offers: offer, coupon code, details
- Menu items: category, sub-category, item name, description, price (₹), veg/non-veg, in stock, tags (e.g. Bestseller, NEW, item discounts, "Not eligible for coupons"), price note
- A **Nearby Outlets** sheet (Zomato): other outlets of the same chain with locality, address, delivery and dining ratings with review counts, cost for two and distance. Zomato only puts the first ~9 outlets in the page, ordered by its default location for the city, so this isn't every outlet and isn't sorted by distance from the one you scraped
- A second sheet, **Add-ons**: one row per option for sizes, variants and add-ons (milk, syrups, extra toppings...), with whether the group is required, how many options can be picked, and the extra price

Packaged goods (bottled water, coffee beans, chocolates) are listed without GST, e.g. ₹119.05 instead of ₹125. Neither site says which items these are or what rate applies, so the scripts add the lowest GST rate (5, 12, 18 or 28%) that turns the price into a whole rupee amount, and record it in the Price Note column.

Offers depend on your location and account. Zomato doesn't include restaurant offers in the page for a logged-out visitor, so the Zomato offers section is usually empty; item tags still come through.

**Note:** Please make sure your use complies with Swiggy's and Zomato's terms of service, and keep request volumes low.

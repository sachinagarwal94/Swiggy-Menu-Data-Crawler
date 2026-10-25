**Swiggy & Zomato Menu Data Crawler**

**Description:**
Python scripts that extract a restaurant's menu from Swiggy or Zomato and save it to an Excel spreadsheet, along with the restaurant's name, address, rating and FSSAI license number.

Both scripts read the structured menu data the sites themselves load, instead of scraping CSS class names. The class names change with every site release, which is what broke the old script.

**Setup:**
```
pip install -r requirements.txt
```
The Swiggy script also needs Google Chrome installed. Selenium 4.6+ downloads the matching ChromeDriver automatically, so you don't have to configure a driver path.

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

Run either script without a URL and it will ask for one.

**Output:**
`Swiggy_<Restaurant Name>_menu.xlsx` or `Zomato_<Restaurant Name>_menu.xlsx`, with:
- Restaurant details: name, address, rating, FSSAI license number, source URL
- Offers: offer, coupon code, details
- Menu items: category, sub-category, item name, description, price (₹), veg/non-veg, in stock, tags (e.g. Bestseller, NEW, item discounts, "Not eligible for coupons")

Offers depend on your location and account. Zomato doesn't include restaurant offers in the page for a logged-out visitor, so the Zomato offers section is usually empty; item tags still come through.

**Note:** Please make sure your use complies with Swiggy's and Zomato's terms of service, and keep request volumes low.

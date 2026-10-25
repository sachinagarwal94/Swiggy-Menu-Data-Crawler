import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from menu_excel import save_menu_workbook

MENU_API = '/dapi/menu/'
WAIT_SECONDS = 90


def open_browser(headless=False):
    chrome_options = Options()
    if headless:
        # Swiggy often refuses headless browsers; use only if the visible window works for you without it
        chrome_options.add_argument('--headless=new')
    # Keep network logs so we can read the menu JSON the page itself downloads
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    # Selenium 4.6+ downloads the matching chromedriver automatically (Selenium Manager)
    return webdriver.Chrome(options=chrome_options)


def capture_menu_json(driver, url):
    """Load the restaurant page and return the body of the menu API response it triggers."""
    driver.get(url)
    print('Waiting for the menu to load. If Swiggy asks for a location or a check, complete it in the browser window.')

    menu_request_ids = []
    deadline = time.time() + WAIT_SECONDS
    while time.time() < deadline:
        for entry in driver.get_log('performance'):
            message = json.loads(entry['message'])['message']
            if message.get('method') != 'Network.responseReceived':
                continue
            response = message['params']['response']
            if MENU_API in response['url'] and response['status'] == 200:
                menu_request_ids.append(message['params']['requestId'])

        # Newest response first: the page re-requests the menu after a location change
        for request_id in reversed(menu_request_ids):
            try:
                body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})['body']
                data = json.loads(body)
            except Exception:
                continue  # Body not finished downloading yet, or not JSON
            if find_cards(data, 'Restaurant'):
                return data
        time.sleep(1)

    raise RuntimeError(f'Menu data did not load within {WAIT_SECONDS} seconds.')


def find_cards(node, type_suffix):
    """Recursively collect every card whose '@type' ends with '.<type_suffix>'.

    Swiggy nests cards several levels deep and moves them around between releases,
    so matching on the card type is more stable than fixed paths or CSS class names.
    """
    found = []
    if isinstance(node, dict):
        card_type = node.get('@type', '')
        if card_type.endswith('.' + type_suffix):
            found.append(node)
        for value in node.values():
            found.extend(find_cards(value, type_suffix))
    elif isinstance(node, list):
        for value in node:
            found.extend(find_cards(value, type_suffix))
    return found


def format_price(info):
    # Swiggy prices are in paise; variant-only items carry their price in variantsV2 instead
    paise = info.get('price') or info.get('defaultPrice') or info.get('finalPrice')
    if not paise:
        return ''
    rupees = paise / 100
    return int(rupees) if rupees.is_integer() else rupees


def parse_item(item_card, category, sub_category):
    info = item_card.get('card', {}).get('info', {})
    veg = info.get('itemAttribute', {}).get('vegClassifier') or {1: 'VEG', 0: 'NONVEG'}.get(info.get('isVeg'), '')
    return {
        'Category': category,
        'Sub-category': sub_category,
        'Item Name': info.get('name', ''),
        'Description': info.get('description', ''),
        'Price': format_price(info),
        'Veg/Non-veg': veg,
        'In Stock': 'No' if info.get('inStock') == 0 else 'Yes',
        'Tags': ', '.join(item_tags(info)),
    }


def item_tags(info):
    """Item badges such as Bestseller and item-level offers such as '20% OFF'."""
    tags = [(info.get('ribbon') or {}).get('text')]
    tags += [' '.join(filter(None, (tag.get('title'), tag.get('subTitle')))) for tag in info.get('offerTags') or []]
    return [tag for tag in tags if tag]


def parse_offers(data):
    """Restaurant offers, e.g. '60% OFF UPTO ₹120' with coupon code and conditions."""
    offers = []
    for offer_group in find_cards(data, 'OfferInfoWithStyle'):
        for offer in offer_group.get('offers', []):
            info = offer.get('info', {})
            header = ' '.join(part for part in (info.get('header'), info.get('offerTag')) if part)
            if header:
                offers.append({
                    'Offer': header,
                    'Coupon Code': info.get('couponCode', ''),
                    'Details': info.get('description', ''),
                })
    return offers


def parse_menu(data, url):
    info = find_cards(data, 'Restaurant')[0].get('info', {})
    address_cards = find_cards(data, 'RestaurantAddress')
    license_cards = find_cards(data, 'RestaurantLicenseInfo')

    address = address_cards[0].get('completeAddress', '') if address_cards else ''
    if not address:
        address = ', '.join(part for part in (info.get('areaName'), info.get('city')) if part)

    license_text = ''
    if license_cards:
        text = license_cards[0].get('text', '')
        license_text = ' '.join(text) if isinstance(text, list) else text

    rating = info.get('avgRatingString') or info.get('avgRating') or ''
    if rating and info.get('totalRatingsString'):
        rating = f"{rating} ({info['totalRatingsString']})"

    restaurant = {
        'Restaurant Name': info.get('name', ''),
        'Restaurant Address': address,
        'Restaurant Rating': rating,
        'FSSAI License No.': license_text.replace('License No.', '').strip(),
        'Source URL': url,
    }

    items = []
    for category in find_cards(data, 'ItemCategory'):
        for item_card in category.get('itemCards', []):
            items.append(parse_item(item_card, category.get('title', ''), ''))
    for category in find_cards(data, 'NestedItemCategory'):
        for sub_category in category.get('categories', []):
            for item_card in sub_category.get('itemCards', []):
                items.append(parse_item(item_card, category.get('title', ''), sub_category.get('title', '')))

    if not items:
        raise RuntimeError('Restaurant found but no menu items. It may be closed or not deliver to the chosen location.')
    return restaurant, parse_offers(data), items


def crawl_menu_data(url, headless=False):
    driver = open_browser(headless)
    try:
        data = capture_menu_json(driver, url)
    finally:
        driver.quit()
    return parse_menu(data, url)


def save_menu_data(url, headless=False):
    restaurant, offers, items = crawl_menu_data(url, headless)
    return save_menu_workbook(restaurant, items, 'Swiggy', offers)


if __name__ == '__main__':
    args = [arg for arg in sys.argv[1:] if arg != '--headless']
    menu_url = args[0] if args else input('Enter the Swiggy restaurant URL: ').strip()
    save_menu_data(menu_url, headless='--headless' in sys.argv)

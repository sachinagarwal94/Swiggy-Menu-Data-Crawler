import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from menu_excel import add_missing_gst, save_menu_workbook

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
        model_prices = [model.get('price') for model in (info.get('variantsV2') or {}).get('pricingModels', [])]
        paise = min((price for price in model_prices if price), default=0)
    return paise_to_rupees(paise) if paise else ''


def paise_to_rupees(paise):
    rupees = round(paise / 100, 2)
    return int(rupees) if rupees.is_integer() else rupees


def parse_item(item_card, category, sub_category):
    info = item_card.get('card', {}).get('info', {})
    veg = info.get('itemAttribute', {}).get('vegClassifier') or veg_label(info)
    price, price_note = add_missing_gst(format_price(info))
    return {
        'Category': category,
        'Sub-category': sub_category,
        'Item Name': info.get('name', ''),
        'Description': info.get('description', ''),
        'Price': price,
        'Veg/Non-veg': veg,
        'In Stock': 'No' if info.get('inStock') == 0 else 'Yes',
        'Tags': ', '.join(item_tags(info)),
        'Price Note': price_note,
    }


def veg_label(option):
    return {1: 'VEG', 0: 'NONVEG'}.get(option.get('isVeg'), '')


def parse_addons(item_card, category):
    """One row per option: size/variant choices first, then add-on groups (extra cheese, dips...)."""
    info = item_card.get('card', {}).get('info', {})
    base = {'Category': category, 'Item Name': info.get('name', '')}
    rows = []

    # Variant groups (e.g. size, crust). Older menus use 'variants', newer ones 'variantsV2';
    # their variation prices are the extra cost in rupees
    variant_groups = ((info.get('variantsV2') or {}).get('variantGroups')
                      or (info.get('variants') or {}).get('variantGroups') or [])
    for group in variant_groups:
        for option in group.get('variations', []):
            rows.append(dict(base, **{
                'Group': group.get('name', ''),
                'Required': 'Yes',
                'Max Choices': 1,
                'Option': option.get('name', ''),
                'Extra Price': option.get('price', 0),
                'Veg/Non-veg': veg_label(option),
                'In Stock': 'No' if option.get('inStock') == 0 else 'Yes',
            }))

    # Add-on groups; choice prices are in paise like item prices
    for group in info.get('addons') or []:
        max_choices = group.get('maxAddons')
        for option in group.get('choices', []):
            rows.append(dict(base, **{
                'Group': group.get('groupName', ''),
                'Required': 'Yes' if (group.get('minAddons') or 0) > 0 else 'No',
                'Max Choices': 'Any' if max_choices == -1 else max_choices,
                'Option': option.get('name', ''),
                'Extra Price': paise_to_rupees(option.get('price') or 0),
                'Veg/Non-veg': veg_label(option),
                'In Stock': 'No' if option.get('inStock') == 0 else 'Yes',
            }))
    return rows


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

    items, addons = [], []
    for category in find_cards(data, 'ItemCategory'):
        for item_card in category.get('itemCards', []):
            items.append(parse_item(item_card, category.get('title', ''), ''))
            addons += parse_addons(item_card, category.get('title', ''))
    for category in find_cards(data, 'NestedItemCategory'):
        for sub_category in category.get('categories', []):
            for item_card in sub_category.get('itemCards', []):
                items.append(parse_item(item_card, category.get('title', ''), sub_category.get('title', '')))
                addons += parse_addons(item_card, category.get('title', ''))

    if not items:
        raise RuntimeError('Restaurant found but no menu items. It may be closed or not deliver to the chosen location.')
    return restaurant, parse_offers(data), items, addons


def crawl_menu_data(url, headless=False):
    driver = open_browser(headless)
    try:
        data = capture_menu_json(driver, url)
    finally:
        driver.quit()
    # Keep the raw response so it can be re-processed (python swiggy_scraper.py --json <file>)
    raw_file = 'Swiggy_menu_response.json'
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f'Raw menu JSON saved to {raw_file}')
    return parse_menu(data, url)


def save_menu_data(url, headless=False, json_file=None):
    if json_file:
        with open(json_file, encoding='utf-8') as f:
            restaurant, offers, items, addons = parse_menu(json.load(f), url)
    else:
        restaurant, offers, items, addons = crawl_menu_data(url, headless)
    return save_menu_workbook(restaurant, items, 'Swiggy', offers, addons)


if __name__ == '__main__':
    # Usage: swiggy_scraper.py <url> [--headless]
    #    or: swiggy_scraper.py --json <saved menu response.json> [url]
    args = sys.argv[1:]
    json_file = args.pop(args.index('--json') + 1) if '--json' in args else None
    args = [arg for arg in args if arg not in ('--json', '--headless')]
    menu_url = args[0] if args else ('' if json_file else input('Enter the Swiggy restaurant URL: ').strip())
    save_menu_data(menu_url, headless='--headless' in sys.argv, json_file=json_file)

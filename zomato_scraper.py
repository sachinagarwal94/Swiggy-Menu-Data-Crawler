import json
import re
import sys

import requests

from menu_excel import add_missing_gst, save_menu_workbook

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/130.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}

# Zomato embeds the full page state as a JSON string: window.__PRELOADED_STATE__ = JSON.parse("...");
STATE_PATTERN = re.compile(r'window\.__PRELOADED_STATE__\s*=\s*JSON\.parse\((".*?")\);', re.S)


def to_order_url(url):
    """The menu is only embedded in the /order page, so normalise .../info, .../menu etc. to .../order."""
    url = url.split('?')[0].split('#')[0].rstrip('/')
    url = re.sub(r'/(order|info|menu|reviews|photos|book)$', '', url)
    return url + '/order'


def fetch_state(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    match = STATE_PATTERN.search(response.text)
    if not match:
        raise RuntimeError('Could not find menu data on the page. Is this a Zomato restaurant URL?')
    return json.loads(json.loads(match.group(1)))


def crawl_menu_data(url):
    order_url = to_order_url(url)
    state = fetch_state(order_url)

    restaurants = state.get('pages', {}).get('restaurant', {})
    if not restaurants:
        raise RuntimeError('No restaurant found in the page data.')
    page = next(iter(restaurants.values()))
    sections = page.get('sections', {})
    basic_info = sections.get('SECTION_BASIC_INFO') or {}
    contact = sections.get('SECTION_RES_CONTACT') or {}
    menu_list = page.get('order', {}).get('menuList', {})

    ratings = (basic_info.get('rating_new') or {}).get('ratings') or {}
    delivery_rating = (ratings.get('DELIVERY') or {}).get('rating', '')
    dining_rating = (ratings.get('DINING') or {}).get('rating', '')
    rating = ', '.join(f'{label} {value}' for label, value in
                       (('Delivery', delivery_rating), ('Dining', dining_rating)) if value)

    fssai_text = (menu_list.get('fssaiInfo') or {}).get('text', '')
    restaurant = {
        'Restaurant Name': basic_info.get('name', ''),
        'Restaurant Address': contact.get('address', ''),
        'Restaurant Rating': rating,
        'FSSAI License No.': re.sub(r'^\s*Lic\.?\s*No\.?\s*', '', fssai_text),
        'Source URL': order_url,
    }

    modifier_groups = menu_list.get('modifierGroups') or {}
    items, addons = [], []
    for menu_wrapper in menu_list.get('menus', []):
        menu = menu_wrapper.get('menu', {})
        for category_wrapper in menu.get('categories', []):
            category = category_wrapper.get('category', {})
            for item_wrapper in category.get('items', []):
                item = item_wrapper.get('item', {})
                dietary = item.get('dietary_slugs') or []
                price = item.get('display_price') or item.get('min_price') or item.get('price') or ''
                price, price_note = add_missing_gst(price)
                items.append({
                    'Category': menu.get('name', ''),
                    'Sub-category': category.get('name', ''),
                    'Item Name': item.get('name', ''),
                    'Description': item.get('desc', ''),
                    'Price': price,
                    'Veg/Non-veg': ', '.join(dietary),
                    'In Stock': 'Yes' if item.get('item_state', 'available') == 'available' else 'No',
                    'Tags': ', '.join(item_tags(item)),
                    'Price Note': price_note,
                })
                addons += parse_addons(item, menu.get('name', ''), modifier_groups)

    if not items:
        raise RuntimeError('Restaurant found but no menu items. It may not deliver to this area right now.')
    offers = [parse_promo(promo) for promo in (menu_list.get('promosOnMenu') or {}).get('promos', [])]
    return restaurant, [offer for offer in offers if offer['Offer']], items, addons


def parse_addons(item, category, modifier_groups, group_ids=None, prefix=''):
    """One row per option in each customisation group (size, milk, syrups, extra toppings...).

    Options can open further groups of their own; those are listed with the option path as prefix.
    """
    rows = []
    for group_id in item.get('modifier_group_ids', []) if group_ids is None else group_ids:
        group = (modifier_groups.get(group_id) or {}).get('group', {})
        group_name = prefix + group.get('name', '')
        for option_wrapper in group.get('items', []):
            option = option_wrapper.get('item', {})
            rows.append({
                'Category': category,
                'Item Name': item.get('name', ''),
                'Group': group_name,
                'Required': 'Yes' if group.get('min', 0) > 0 else 'No',
                'Max Choices': group.get('max', ''),
                'Option': option.get('name', ''),
                'Extra Price': option.get('price', 0),
                'Veg/Non-veg': ', '.join(option.get('dietary_slugs') or []),
                'In Stock': 'Yes' if option.get('item_state', 'available') == 'available' else 'No',
            })
            if option.get('modifier_group_ids'):
                rows += parse_addons(item, category, modifier_groups, option['modifier_group_ids'],
                                     f"{group_name} > {option.get('name', '')} > ")
    return rows


def item_tags(item):
    """Item badges such as NEW, SPICY or 'Not eligible for coupons'."""
    tags = [(tag.get('title') or {}).get('text') for tag in item.get('tag_objects') or []]
    tags += [tag.get('text') for tag in item.get('tag_texts') or []]
    if item.get('is_bogo_active'):
        tags.append('Buy 1 Get 1')
    return list(dict.fromkeys(tag for tag in tags if tag))


def collect_text(node):
    """Gather the display strings of a Zomato UI object, which nests them as {'text': ...}."""
    if isinstance(node, dict):
        texts = [node['text']] if isinstance(node.get('text'), str) else []
        return texts + [t for key, value in node.items() if key != 'text' for t in collect_text(value)]
    if isinstance(node, list):
        return [t for value in node for t in collect_text(value)]
    return []


def parse_promo(promo):
    # Promos were empty on every restaurant checked while logged out, so this reads
    # their text generically rather than relying on field names we haven't seen
    texts = list(dict.fromkeys(t.strip() for t in collect_text(promo) if t.strip()))
    code = promo.get('code') or promo.get('coupon_code') or '' if isinstance(promo, dict) else ''
    return {'Offer': texts[0] if texts else '', 'Coupon Code': code, 'Details': ' | '.join(texts[1:])}


def save_menu_data(url):
    restaurant, offers, items, addons = crawl_menu_data(url)
    return save_menu_workbook(restaurant, items, 'Zomato', offers, addons)


if __name__ == '__main__':
    menu_url = sys.argv[1] if len(sys.argv) > 1 else input('Enter the Zomato restaurant URL: ').strip()
    save_menu_data(menu_url)

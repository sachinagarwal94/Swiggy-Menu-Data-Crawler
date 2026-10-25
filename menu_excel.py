import re
from openpyxl import Workbook
from openpyxl.styles import Font

RESTAURANT_HEADERS = ['Restaurant Name', 'Restaurant Address', 'Restaurant Rating', 'FSSAI License No.', 'Source URL']
MENU_HEADERS = ['Category', 'Sub-category', 'Item Name', 'Description', 'Price', 'Veg/Non-veg', 'In Stock', 'Tags',
                'Price Note']
OFFER_HEADERS = ['Offer', 'Coupon Code', 'Details']
ADDON_HEADERS = ['Category', 'Item Name', 'Group', 'Required', 'Max Choices', 'Option', 'Extra Price', 'Veg/Non-veg',
                 'In Stock']
OUTLET_HEADERS = ['Outlet Name', 'Locality', 'Address', 'Delivery Rating', 'Delivery Reviews', 'Dining Rating',
                  'Dining Reviews', 'Cost for Two', 'Distance', 'URL']
GST_RATES = (5, 12, 18, 28)


def add_missing_gst(price):
    """Return (price including GST, note) for prices listed without GST.

    Packaged goods (bottled water, coffee beans, chocolates) are listed at their pre-GST price,
    e.g. 119.05, while the customer pays a round MRP, e.g. 125. Neither site says which items
    these are or which rate applies, so we pick the lowest GST rate that turns the price into
    a whole rupee amount. Prices that are already whole rupees are left as they are.
    """
    if not isinstance(price, float) or price.is_integer() or price < 10:
        return price, ''
    for rate in GST_RATES:
        with_gst = price * (1 + rate / 100)
        if abs(with_gst - round(with_gst)) < 0.02:
            return int(round(with_gst)), f'Includes {rate}% GST added to listed ₹{price:g}'
    return price, 'Listed price, may exclude GST'


def save_menu_workbook(restaurant, items, platform, offers=(), addons=(), outlets=(), outlets_note=''):
    """Write restaurant details, offers, menu items and add-ons to <platform>_<restaurant name>_menu.xlsx."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Menu'
    bold = Font(bold=True)

    # Restaurant details block
    worksheet.append(RESTAURANT_HEADERS)
    worksheet.append([restaurant.get(h, '') for h in RESTAURANT_HEADERS])
    worksheet.append([])

    # Offers block
    worksheet.append(OFFER_HEADERS)
    header_rows = [1, worksheet.max_row]
    for offer in offers:
        worksheet.append([offer.get(h, '') for h in OFFER_HEADERS])
    if not offers:
        worksheet.append(['No offers found'])
    worksheet.append([])

    # Menu items block
    worksheet.append(MENU_HEADERS)
    header_rows.append(worksheet.max_row)
    for row in header_rows:
        for cell in worksheet[row]:
            cell.font = bold
    for item in items:
        worksheet.append([item.get(h, '') for h in MENU_HEADERS])

    for column, width in zip('ABCDEFGHI', (28, 24, 40, 60, 10, 12, 10, 30, 36)):
        worksheet.column_dimensions[column].width = width

    # Add-ons, variants and customisations: one row per option
    addon_sheet = workbook.create_sheet('Add-ons')
    addon_sheet.append(ADDON_HEADERS)
    for cell in addon_sheet[1]:
        cell.font = bold
    for addon in addons:
        addon_sheet.append([addon.get(h, '') for h in ADDON_HEADERS])
    for column, width in zip('ABCDEFGHI', (24, 40, 32, 10, 12, 36, 12, 12, 10)):
        addon_sheet.column_dimensions[column].width = width

    # Other outlets of the same chain
    if outlets or outlets_note:
        outlet_sheet = workbook.create_sheet('Nearby Outlets')
        if outlets_note:
            outlet_sheet.append([outlets_note])
        outlet_sheet.append(OUTLET_HEADERS)
        for cell in outlet_sheet[outlet_sheet.max_row]:
            cell.font = bold
        for outlet in outlets:
            outlet_sheet.append([outlet.get(h, '') for h in OUTLET_HEADERS])
        for column, width in zip('ABCDEFGHIJ', (28, 30, 60, 12, 14, 12, 14, 14, 10, 50)):
            outlet_sheet.column_dimensions[column].width = width

    # Restaurant names can contain characters that are not valid in file names
    safe_name = re.sub(r'[\\/:*?"<>|]+', '-', restaurant.get('Restaurant Name') or 'restaurant').strip()
    file_name = f"{platform}_{safe_name}_menu.xlsx"
    workbook.save(file_name)
    print(f"{len(offers)} offers, {len(items)} menu items and {len(addons)} add-on options saved to {file_name}")
    return file_name

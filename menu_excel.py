import re
from openpyxl import Workbook
from openpyxl.styles import Font

RESTAURANT_HEADERS = ['Restaurant Name', 'Restaurant Address', 'Restaurant Rating', 'FSSAI License No.', 'Source URL']
MENU_HEADERS = ['Category', 'Sub-category', 'Item Name', 'Description', 'Price', 'Veg/Non-veg', 'In Stock', 'Tags']
OFFER_HEADERS = ['Offer', 'Coupon Code', 'Details']


def save_menu_workbook(restaurant, items, platform, offers=()):
    """Write restaurant details, offers and menu items to <platform>_<restaurant name>_menu.xlsx."""
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

    for column, width in zip('ABCDEFGH', (28, 24, 40, 60, 10, 12, 10, 30)):
        worksheet.column_dimensions[column].width = width

    # Restaurant names can contain characters that are not valid in file names
    safe_name = re.sub(r'[\\/:*?"<>|]+', '-', restaurant.get('Restaurant Name') or 'restaurant').strip()
    file_name = f"{platform}_{safe_name}_menu.xlsx"
    workbook.save(file_name)
    print(f"{len(offers)} offers and {len(items)} menu items saved to {file_name}")
    return file_name

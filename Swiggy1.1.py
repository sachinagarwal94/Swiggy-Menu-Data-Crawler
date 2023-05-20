from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from openpyxl import Workbook

def crawl_menu_data(url):
    # Set up Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    service = Service('/path/to/chromedriver')  # Replace with the path to your chromedriver executable
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Navigate to the menu URL
    driver.get(url)

    # Wait for the necessary elements to load
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.RestaurantNameAddress_name__2IaTv')))

    # Get the page source
    page_source = driver.page_source

    # Close the driver
    driver.quit()

    # Parse the HTML content
    soup = BeautifulSoup(page_source, 'html.parser')

    # Extract the restaurant name
    restaurant_name = soup.select_one('.RestaurantNameAddress_name__2IaTv').get_text(strip=True)

    # Extract the restaurant address
    restaurant_address = soup.select_one('.RestaurantFooterAddress_address__37uUA').get_text(strip=True)

    # Extract the restaurant rating
    restaurant_rating = soup.select_one('.RestaurantRatings_avgRating__1TOWY').get_text(strip=True)

    # Extract the FSSAI license number
    fssai_license = soup.select_one('.RestaurantLicence_licence__Oo5_q').get_text(strip=True)

    # Extract the menu items from the recommended category
    items = []
    recommended_item_elements = soup.select('[data-testid="recommended-dish-item"]')

    for item_element in recommended_item_elements:
        item_name = item_element.select_one('.styles_itemNameText__3ZmZZ').get_text(strip=True)

        description_element = item_element.select_one('.styles_itemDesc__3vhM0')
        description = description_element.get_text(strip=True) if description_element else ''

        price_element = item_element.select_one('.styles_itemPrice__1Nrpd .rupee')
        price = price_element.get_text(strip=True) if price_element else ''

        items.append({
            'Item Name': item_name,
            'Description': description,
            'Price': price,
            'Category': 'Recommended'
        })

    # Extract the menu items from other categories
    main_container_elements = soup.find_all('div', class_='main_container__3QMrw')

    for main_container_element in main_container_elements:
        category_element = main_container_element.find_previous('div', id=lambda x: x and x.startswith('cid-'))
        category_id = category_element['id'][4:]

        item_elements = main_container_element.select('[data-testid="normal-dish-item"]')

        for item_element in item_elements:
            item_name = item_element.select_one('.styles_itemNameText__3ZmZZ').get_text(strip=True)

            description_element = item_element.select_one('.styles_itemDesc__3vhM0')
            description = description_element.get_text(strip=True) if description_element else ''

            price_element = item_element.select_one('.styles_itemPrice__1Nrpd .rupee')
            price = price_element.get_text(strip=True) if price_element else ''

            items.append({
                'Item Name': item_name,
                'Description': description,
                'Price': price,
                'Category': category_id
            })

    return restaurant_name, restaurant_address, restaurant_rating, fssai_license, items


def save_menu_data(url):
    # Extract the restaurant details and menu items
    restaurant_name, restaurant_address, restaurant_rating, fssai_license, menu_data = crawl_menu_data(url)

    # Create a new Excel workbook and add a worksheet
    workbook = Workbook()
    worksheet = workbook.active

    # Set the column headers for restaurant details
    restaurant_details_headers = ['Restaurant Name', 'Restaurant Address', 'Restaurant Rating', 'FSSAI License No.']
    worksheet.append(restaurant_details_headers)

    # Write the restaurant details to the worksheet
    restaurant_details_row = [restaurant_name, restaurant_address, restaurant_rating, fssai_license]
    worksheet.append(restaurant_details_row)

    # Set the column headers for menu items
    menu_headers = ['Item Name', 'Description', 'Price', 'Category']
    worksheet.append(menu_headers)

    # Write the menu data to the worksheet
    for item in menu_data:
        row = [item['Item Name'], item['Description'], item['Price'], item['Category']]
        worksheet.append(row)

    # Save the workbook with the restaurant name as the file name
    file_name = f"{restaurant_name}_menu.xlsx"
    workbook.save(file_name)
    print(f"Menu data saved to {file_name}")


# Example usage
url = input("Enter the menu URL: ")
save_menu_data(url)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from openpyxl import Workbook

def crawl_menu_data(url):
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode

    # Set path to chromedriver executable (Update the path based on your configuration)
    chromedriver_path = "/path/to/chromedriver"

    # Initialize Chrome driver
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)

    # Load the URL in Chrome
    driver.get(url)

    # Get the page source
    page_source = driver.page_source

    # Parse the HTML content
    soup = BeautifulSoup(page_source, 'html.parser')

    # Extract the restaurant name
    restaurant_name = soup.select_one('.RestaurantNameAddress_name__2IaTv').get_text(strip=True)

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

    # Close the Chrome driver
    driver.quit()

    return restaurant_name, items


def save_menu_data(url):
    # Extract the restaurant name and menu items
    restaurant_name, menu_data = crawl_menu_data(url)

    # Create a new Excel workbook and add a worksheet
    workbook = Workbook()
    worksheet = workbook.active

    # Set the column headers
    headers = ['Item Name', 'Description', 'Price', 'Category']
    worksheet.append(headers)

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

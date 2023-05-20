**Swiggy Menu Data Crawler**

**Description:**
The Swiggy Menu Data Crawler is a Python script that allows you to extract menu data from Swiggy, a popular food delivery platform. The script utilizes web scraping techniques using Selenium and Chrome WebDriver to navigate the Swiggy website, fetch the menu details, and save them in an Excel spreadsheet.

**Features:**
1. Automatic Chrome WebDriver Detection: The script automatically detects the Chrome WebDriver path on your system, eliminating the need for manual configuration.
2. User Input: The script prompts the user to enter the URL of the restaurant menu they want to scrape.
3. Restaurant Information: Along with the menu data, the script fetches additional information such as the restaurant name, address, rating, and FSSAI license number.
4. Extraction of Menu Items: The script extracts the menu items from both the recommended category and other categories available on the Swiggy menu page.
5. Excel Spreadsheet Generation: The script creates a new Excel workbook and adds a worksheet to store the menu data.
6. Customizable Output: The output file is saved with the restaurant name as the file name, providing a convenient way to organize and identify the data.

**Usage:**
1. Run the script in a Python environment with the required dependencies installed (Selenium, BeautifulSoup, and openpyxl).
2. When prompted, enter the URL of the Swiggy restaurant menu you want to scrape.
3. The script will initiate the web scraping process, fetch the menu data, and save it in an Excel spreadsheet.
4. Once the process is complete, the script will display the location of the generated Excel file.

**Benefits:**
1. Automated Data Extraction: The script eliminates the need for manual copying and pasting of menu data from the Swiggy website, saving time and effort.
2. Consolidated Menu Information: The script collects and organizes all the menu data in a structured Excel spreadsheet, making it easy to analyze and filter the information.
3. Customizable and Extensible: The script can be modified and extended to extract additional information from the Swiggy website, catering to specific needs or requirements.
4. Enhanced Data Analysis: The extracted menu data can be further processed, analyzed, and visualized using various data analysis tools or techniques.

**Note:** Please ensure compliance with Swiggy's terms of service and respect the website's usage policy while using this script.

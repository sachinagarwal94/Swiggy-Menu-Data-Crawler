"""Scrape one or more Swiggy / Zomato restaurant menus into Excel files.

Usage:
    python menu_scraper.py                      (asks for URLs)
    python menu_scraper.py "<url1>, <url2>, ..."

Each URL can be a Zomato restaurant link, a Swiggy restaurant link, a Swiggy menu
API link (swiggy.com/dapi/menu/...), or the path of a saved Swiggy menu .json file.
Files are saved as <Platform>_<Restaurant>_<Restaurant ID>_<date>.xlsx.
"""
import sys
import traceback

import requests

import swiggy_scraper
import zomato_scraper


def expand_short_link(target):
    """Links shared from the Zomato app look like https://zoma.to/r/20540756; follow them to the full URL."""
    if 'zoma.to/' not in target:
        return target
    url = target if target.startswith('http') else 'https://' + target
    response = requests.get(url, headers=zomato_scraper.HEADERS, timeout=30, allow_redirects=True)
    return response.url


def scrape(target):
    target = expand_short_link(target)
    if target.lower().endswith('.json'):
        return swiggy_scraper.save_menu_data('', json_file=target)
    if 'zomato.com' in target:
        return zomato_scraper.save_menu_data(target)
    if 'swiggy.com' in target:
        return swiggy_scraper.save_menu_data(target)
    raise ValueError('Not a Swiggy or Zomato link')


def main():
    raw = ' '.join(sys.argv[1:]) or input('Enter Swiggy / Zomato URLs (comma separated): ')
    targets = [part.strip() for part in raw.replace('\n', ',').split(',') if part.strip()]

    saved, failed = [], []
    for number, target in enumerate(targets, 1):
        print(f'\n[{number}/{len(targets)}] {target}')
        try:
            saved.append(scrape(target))
        except Exception as error:
            traceback.print_exc()
            failed.append((target, error))

    print(f'\nDone: {len(saved)} saved, {len(failed)} failed.')
    for file_name in saved:
        print(f'  saved   {file_name}')
    for target, error in failed:
        print(f'  failed  {target}: {error}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())

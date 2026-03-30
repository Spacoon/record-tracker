from time import sleep
from urllib.parse import urljoin
import os
import json 
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
import pandera.pandas as pa

import argparse

current_date = datetime.today().strftime('%Y-%m-%d')

class Scraper:
    def __init__(self):
        self.base_url = 'https://agrochowski.pl/pl/c/Plyty-winylowe/416'

    def scrape_all_categories(self, output_file_name='categories.parquet') -> None:
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get all categories information
        categories_items = soup.find('ul', class_='level_2').find_all('li')
        categories = []
        for category in categories_items:
            category_name = category.text.strip()
            href = category.find('a')['href']
            categories.append({
                'name': category_name,
                'url': href
            })

        df = pd.DataFrame(categories)
        df['url'] = df['url'].apply(lambda x: urljoin(self.base_url, x))
        df['scrape_date'] = current_date
        pa.DataFrameSchema(
            {
                'name': pa.Column(str),
                'url': pa.Column(str, checks=pa.Check.str_contains('agrochowski.pl/pl')),
                'scrape_date': pa.Column(datetime),
            },
            strict=True,
            coerce=True,
        ).validate(df)
        df.to_parquet(output_file_name, index=False)

    def scrape_category(self, category_data_item) -> pd.DataFrame:
        albums = []

        def scrape_page(page_idx, get_last_page_index: bool = False):
            page_albums = []

            if page_idx == 1:
                page_url = category_data_item['url']
            else:
                page_url = urljoin(category_data_item['url'] + '/', str(page_idx))

            response = requests.get(page_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # First, look for pagination to find all pages
            if get_last_page_index:
                pagination = soup.find('ul', class_='paginator')

                if pagination:
                    last_page_href = pagination.find('li', class_='last').find_previous_sibling('li').find('a')[
                        'href'].strip()
                    last_page_index = int(last_page_href.split('/')[-1])
                else:
                    last_page_index = 1

            # Extract products information
            albums_items = soup.find_all('div', class_='product-inner-wrap')
            for album in albums_items:
                title = album.find('a', class_='prodname f-row').text.strip()

                band_tag = album.find('a', class_='brand')
                band = band_tag.text.strip() if band_tag else None  # Sometimes band is not present
                price = album.find('div', class_='price f-row').find('em').text.strip()
                url = album.find('a', class_='prodname f-row')['href']

                page_albums.append({
                    'title': title,
                    'band': band,
                    'price': price,
                    'url': url,
                    'category': category_data_item['name']
                })

            if get_last_page_index:
                print(f"Scraped page {page_idx}, found {len(page_albums)} products and last page index: {last_page_index}")
                return page_albums, last_page_index
            else:
                print(f"Scraped page {page_idx}, found {len(page_albums)} products")
                return page_albums

        # Start scraping from the first page to determine the last page and gather albums data for first page
        album_listings_first_page, last_page_index = scrape_page(1, get_last_page_index=True)
        albums.extend(album_listings_first_page)
        for page_idx in range(2, last_page_index + 1):
            sleep(2)
            albums.extend(scrape_page(page_idx))

        df = pd.DataFrame(albums)
        df['url'] = df['url'].apply(lambda x: urljoin(self.base_url, x))
        df['scrape_date'] = current_date

        pa.DataFrameSchema(
            {
                'title': pa.Column(str),
                'band': pa.Column(str, nullable=True),
                'price': pa.Column(str),
                'url': pa.Column(str, checks=pa.Check.str_contains('agrochowski.pl/pl')),
                'category': pa.Column(str),
                'scrape_date': pa.Column(datetime)
            },
            strict=True,
            coerce=True,
        ).validate(df)

        return df


def main():
    parser = argparse.ArgumentParser(description='Scrape albums from agrochowski.pl')
    parser.add_argument('--categories', action='store_true', help='Scrape categories')
    parser.add_argument('--albums', action='store_true', help='Scrape albums')
    args = parser.parse_args()

    scraper = Scraper()
    # Search for categories file
    if not os.path.exists('categories.parquet'):
        print("Categories file not found")
    else:
        print("Categories file found")


    if 'categories' in args and args.categories:
        scraper.scrape_all_categories()

    if 'albums' in args and args.albums:
        # Load genres to scrape from config.json
        with open('config.json', 'r') as f:
            genres_to_scrape = json.load(f)['genres_to_scrape']

        # Filter categories
        categories_df = pd.read_parquet('categories.parquet', engine='pyarrow')
        categories_df = categories_df[categories_df['name'].isin(genres_to_scrape)]

        df = pd.DataFrame()
        # Scrape albums
        for _, row in categories_df.iterrows():
            print(f"Scraping albums for category: {row['name']}")
            category_albums = scraper.scrape_category(row)
            df = pd.concat([df, category_albums], ignore_index=True)
            print(df)

        df.to_parquet('albums.parquet', index=False)


def scrape_fresh(progress_callback=None):
    """Scrape all albums and save to data/ directory with today's date.

    Args:
        progress_callback: Optional callable(progress: float, message: str)
    Returns:
        Tuple of (output_path, DataFrame)
    """
    scraper = Scraper()

    if not os.path.exists('categories.parquet'):
        if progress_callback:
            progress_callback(0, "Scraping categories...")
        scraper.scrape_all_categories()

    with open('config.json', 'r') as f:
        genres_to_scrape = json.load(f)['genres_to_scrape']

    categories_df = pd.read_parquet('categories.parquet', engine='pyarrow')
    categories_df = categories_df[categories_df['name'].isin(genres_to_scrape)]

    all_albums = pd.DataFrame()
    total = len(categories_df)

    for idx, (_, row) in enumerate(categories_df.iterrows()):
        if progress_callback:
            progress_callback(idx / total, f"Scraping: {row['name']} ({idx + 1}/{total})")
        category_albums = scraper.scrape_category(row)
        all_albums = pd.concat([all_albums, category_albums], ignore_index=True)

    os.makedirs('data', exist_ok=True)
    today = datetime.today().strftime('%Y-%m-%d')
    output_path = os.path.join('data', f'albums_{today}.parquet')
    all_albums.to_parquet(output_path, index=False)

    if progress_callback:
        progress_callback(1.0, "Scraping complete!")

    return output_path, all_albums


if __name__ == '__main__':
    main()


    

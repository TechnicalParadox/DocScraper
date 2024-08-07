import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse, parse_qs
from tqdm import tqdm

def scrape_and_save(url, base_path=None, links_visited=None, base_url_parts=None):
    """Scrapes a webpage, including code blocks, and saves content.

    Args:
        url (str): URL of the webpage to scrape.
        base_path (str, optional): Base directory for saving files.
        links_visited (dict, optional): Dictionary to track visited links.
        base_url_parts (urllib.parse.ParseResult): Parsed base URL components.
    """

    if links_visited is None:
        links_visited = {}
    links_visited[url] = True

    if base_url_parts is None:
        base_url_parts = urlparse(url)

    try:
        print(f"Scraping: {url}")
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        parsed_url = urlparse(url)

        # Extracting Main Body Content (Including Code Blocks)
        main_content = soup.find('main')
        if not main_content:
            main_content = soup.find('div', id='main')
        if not main_content:
            main_content = soup.find('body')

        if main_content:
            # Extract text content and preserve code blocks:
            text_content = []
            for element in main_content.find_all(recursive=False):
                if element.name == 'pre':
                    text_content.append(element.text)
                else:
                    text_content.append(element.get_text(separator='\n', strip=True))
            text_content = "\n\n".join(text_content)
        else:
            print(f"WARNING: Could not find main content area for {url}")
            text_content = ""

        # Dynamically Create Save Path
        if base_path is None:
            base_path = os.path.dirname(os.path.abspath(__file__)) # Defaults to script directory.
            base_path = os.path.join(base_path, 'scraped')  # Default save directory.
        path_parts = [part for part in parsed_url.path.split('/') if part]
        save_dir = os.path.join(base_path, *path_parts)
        os.makedirs(save_dir, exist_ok=True)

        # Create Unique Filename (Including URL Parameters)
        filename = path_parts[-1] if path_parts else "index"
        query_params = parse_qs(parsed_url.query)
        if query_params:
            param_str = "_".join(f"{k}-{v[0]}" for k, v in query_params.items())
            filename += f"_{param_str}"
        filename += ".txt"
        file_path = os.path.join(save_dir, filename)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text_content)

        # Finding and Processing Links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            full_url_parts = urlparse(full_url)

            if (full_url.startswith(base_url) and
                full_url_parts.path.startswith(base_url_parts.path) and
                parsed_url.netloc in full_url and
                full_url not in links_visited):
                scrape_and_save(full_url, base_path=base_path, links_visited=links_visited, base_url_parts=base_url_parts)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {url} - {e}")

if __name__ == "__main__":
    base_url = input("Enter a website URL: ")
    links_visited = {}
    scrape_and_save(base_url, links_visited=links_visited, base_url_parts=None)

    print("\nScraping complete! URLs visited:")
    for link in links_visited:
        print(link)
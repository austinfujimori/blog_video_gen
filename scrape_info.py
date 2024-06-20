import requests
from bs4 import BeautifulSoup

def fetch_html(url):
    
    # Handling session cookies stuff for some websites
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1"
    }
    try:
        session = requests.Session()
        session.headers.update(headers)

        # Perform an initial request to set cookies
        initial_response = session.get(url)
        initial_response.raise_for_status()
        print("Initial request successful, cookies set.")

        # Perform the actual request to fetch the page content
        response = session.get(url)
        response.raise_for_status()
        print(f"Successfully fetched HTML content from {url}")  # Debug print
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Title
    title_tag = soup.find('h1')
    title = title_tag.text.strip() if title_tag else 'No Title Found'
    print(f"Parsed title: {title}")

    # Date
    date_tag = soup.find('time')
    date = date_tag.text.strip() if date_tag else 'No Date Found'
    print(f"Parsed date: {date}")

    # Author
    author_tag = soup.find(attrs={'class': 'author'})
    author = author_tag.text.strip() if author_tag else 'No Author Found'
    print(f"Parsed author: {author}")

    # Content
    content_tags = soup.find_all('p')
    content = ' '.join([p.text.strip() for p in content_tags])
    print(f"Parsed content length: {len(content)} characters")

    return {
        'title': title,
        'date': date,
        'author': author,
        'content': content
    }

def get_blog_info(url):
    html = fetch_html(url)
    if html:
        parsed_info = parse_html(html)
        print(f"Parsed blog info: {parsed_info}")
        return parsed_info
    else:
        print("Failed to retrieve HTML content.")
        return None

import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os

def ensure_cache_directory_exists(directory="bot/thumbnail_cache"):
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def is_cached(id, cache_dir="bot/thumbnail_cache"):
    cached_image_path = os.path.join(cache_dir, f"{id}.jpg")
    return os.path.exists(cached_image_path), cached_image_path

def cache_thumbnail(id, image_url, cache_dir="bot/thumbnail_cache"):
    cached_image_path = os.path.join(cache_dir, f"{id}.jpg")
    if not os.path.exists(cached_image_path):
        try:
            image_response = requests.get(image_url)
            if image_response.status_code != 200:
                raise Exception("Failed to download image")
            img = Image.open(BytesIO(image_response.content))
            img.save(cached_image_path)
            print(f"Thumbnail downloaded and cached for ID {id}.")
        except Exception as e:
            print(f"Error caching image for ID {id}: {e}")

def fetch_thumbnail_url(id):
    base_url = "https://steamcommunity.com/sharedfiles/filedetails/?id="
    url = base_url + str(id)
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Failed to fetch page")

        soup = BeautifulSoup(response.content, 'html.parser')
        image_tag = soup.find('img', id='previewImageMain') or soup.find('img', class_='workshopItemPreviewImageMain') or soup.find('img', id='previewImage')
        if not image_tag or 'src' not in image_tag.attrs:
            raise Exception("Image tag not found or src attribute missing")

        return image_tag['src']

    except Exception as e:
        print(f"Error fetching image URL for ID {id}: {e}")
        return None

def parse_file(filepath):
    sections = {}
    with open(filepath, 'r') as file:
        current_section = None
        for line in file:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                sections[current_section] = []
            elif '=' in line and current_section:
                name, id_ = line.split('=')
                sections[current_section].append((name.strip(), id_.strip()))
    return sections

def create_image_url_file(sections, output_path, cache_dir):
    with open(output_path, "w") as file:
        for section, items in sections.items():
            file.write(f"Section: {section}\n")
            for name, id_ in items:
                image_url = fetch_thumbnail_url(id_)
                if image_url:
                    cached, _ = is_cached(id_, cache_dir)
                    if not cached:
                        cache_thumbnail(id_, image_url, cache_dir)
                    file.write(f"{name}: {image_url}\n")
                else:
                    file.write(f"{name}: Error retrieving image\n")
            file.write("\n")

# Usage example
cache_directory = ensure_cache_directory_exists()
map_sections = parse_file('configs/maps.cfg')

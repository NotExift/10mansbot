from PIL import Image, ImageDraw, ImageFont
import os
import textwrap
from imagegetter import (
    ensure_cache_directory_exists,
    is_cached,
    cache_thumbnail,
    fetch_thumbnail_url,
)


def parse_file(filepath):
    sections = {}
    with open(filepath, "r") as file:
        current_section = None
        for line in file:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                sections[current_section] = []
            elif "=" in line and current_section:
                name, id_ = line.split("=")
                sections[current_section].append((name.strip(), id_.strip()))
    return sections


def create_aggregate_image(sections, cache_dir, output_path):
    thumb_max_width, thumb_max_height = 160, 60
    spacing = 10
    section_header_height = 40
    text_area_width = 100
    horizontal_padding = 20

    max_maps_in_section = max(len(items) for items in sections.values())
    section_width = thumb_max_width + spacing + text_area_width
    total_width = section_width * len(sections) + 2 * horizontal_padding
    total_height = (
        (max_maps_in_section * (thumb_max_height + spacing))
        + section_header_height
        + 60
    )

    composite_image = Image.new(
        "RGB", (total_width, total_height), color=(255, 255, 255)
    )
    draw = ImageDraw.Draw(composite_image)

    try:
        section_font = ImageFont.truetype("comicbd.ttf", 24)
        label_font = ImageFont.truetype("comic.ttf", 18)
        title_font = ImageFont.truetype("comicbd.ttf", 36)
    except IOError:
        section_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        title_font = ImageFont.load_default()  # Fallback font

    title = "Ultimate Map Bans"
    title_width = draw.textbbox((0, 0), title, font=title_font)[2]
    draw.text(
        ((total_width - title_width) // 2, 10), title, font=title_font, fill=(0, 0, 0)
    )

    x_offset = horizontal_padding
    for section, items in sections.items():
        draw.text((x_offset + 5, 60), section, font=section_font, fill=(0, 0, 0))
        y_offset = section_header_height + 65
        for name, id_ in items:
            cached, cached_image_path = is_cached(id_, cache_dir)
            if not cached:
                image_url = fetch_thumbnail_url(id_)
                if image_url:
                    cache_thumbnail(id_, image_url, cache_dir)
                cached_image_path = os.path.join(cache_dir, f"{id_}.jpg")
            if os.path.exists(cached_image_path):
                img = Image.open(cached_image_path)
                img.thumbnail((thumb_max_width, thumb_max_height))
            else:
                img = Image.new(
                    "RGB", (thumb_max_width, thumb_max_height), color=(192, 192, 192)
                )

            composite_image.paste(img, (x_offset, y_offset))
            wrapped_text = textwrap.fill(name, width=16)
            draw.text(
                (x_offset + thumb_max_width - 50, y_offset),
                wrapped_text,
                font=label_font,
                fill=(0, 0, 0),
            )
            y_offset += thumb_max_height + spacing

        x_offset += section_width

    composite_image.save(output_path)


# Usage example
cache_directory = ensure_cache_directory_exists()
map_sections = parse_file("configs/maps.cfg")
create_aggregate_image(map_sections, cache_directory, "bot/mapsimage.jpg")

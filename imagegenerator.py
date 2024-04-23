from PIL import Image, ImageDraw, ImageFont
import os

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

def create_aggregate_image(sections, cache_dir, output_path):
    thumb_max_width, thumb_max_height = 160, 60  # Maximum dimensions for thumbnails
    spacing = 10
    section_header_height = 20
    text_area_width = 100  # Space for map name

    max_maps_in_section = max(len(items) for items in sections.values())
    section_width = thumb_max_width + spacing + text_area_width
    total_width = section_width * len(sections)
    total_height = (max_maps_in_section * (thumb_max_height + spacing)) + section_header_height

    composite_image = Image.new('RGB', (total_width, total_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(composite_image)
    font = ImageFont.load_default()

    x_offset = 0
    for section, items in sections.items():
        draw.text((x_offset + 5, 5), section, font=font, fill=(0, 0, 0))

        y_offset = section_header_height + 5
        for name, id_ in items:
            image_path = os.path.join(cache_dir, f"{id_}.jpg")
            if os.path.exists(image_path):
                img = Image.open(image_path)
                # Resize while maintaining aspect ratio
                img.thumbnail((thumb_max_width, thumb_max_height))
            else:
                img = Image.new('RGB', (thumb_max_width, thumb_max_height), color=(192, 192, 192))  # Placeholder if the image is missing

            composite_image.paste(img, (x_offset, y_offset))
            draw.text((x_offset + thumb_max_width + 5, y_offset + 20), name, font=font, fill=(0, 0, 0))
            y_offset += thumb_max_height + spacing

        x_offset += section_width

    composite_image.save(output_path)
    composite_image.show()

# Example usage
cache_directory = 'thumbnail_cache'
map_sections = parse_file('maps.cfg')
create_aggregate_image(map_sections, cache_directory, 'output_landscape.jpg')

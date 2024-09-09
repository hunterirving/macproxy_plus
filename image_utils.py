import os
import io
import hashlib
import requests
from PIL import Image
import mimetypes

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cached_images")
MAX_WIDTH = 512
MAX_HEIGHT = 342
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def is_image_url(url):
    mime_type, _ = mimetypes.guess_type(url)
    return mime_type and mime_type.startswith('image/')

def optimize_image(image_data):
    img = Image.open(io.BytesIO(image_data))
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    background = Image.new('RGBA', img.size, (255, 255, 255, 255))
    img = Image.alpha_composite(background, img)
    img = img.convert('RGB')
    
    width, height = img.size
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        ratio = min(MAX_WIDTH / width, MAX_HEIGHT / height)
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    
    img = img.convert("L")
    img = img.convert("1", dither=Image.FLOYDSTEINBERG)
    
    output = io.BytesIO()
    img.save(output, format="GIF", optimize=True)
    return output.getvalue()

def fetch_and_cache_image(url, content=None):
    try:
        print(f"Processing image: {url}")
        
        file_name = hashlib.md5(url.encode()).hexdigest() + ".gif"
        file_path = os.path.join(CACHE_DIR, file_name)
        
        if not os.path.exists(file_path):
            print(f"Optimizing and caching image: {url}")
            if content is None:
                response = requests.get(url, stream=True, headers={"User-Agent": USER_AGENT})
                response.raise_for_status()
                content = response.content
            
            optimized_image = optimize_image(content)
            with open(file_path, 'wb') as f:
                f.write(optimized_image)
        else:
            print(f"Image already cached: {url}")
        
        cached_url = f"/cached_image/{file_name}"
        print(f"Cached URL: {cached_url}")
        return cached_url
    except Exception as e:
        print(f"Error processing image: {url}, Error: {str(e)}")
        return None
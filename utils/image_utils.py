
import os
import io
import hashlib
import requests
from PIL import Image
import mimetypes
from config import MAX_IMAGE_HEIGHT, MAX_IMAGE_WIDTH, RESIZE_IMAGES, CONVERT_IMAGES, CONVERT_IMAGES_TO_FILETYPE, DITHERING_ALGORITHM

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cached_images")
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def is_image_url(url):
	mime_type, _ = mimetypes.guess_type(url)
	return mime_type and mime_type.startswith('image/')

def optimize_image(image_data):
	try:
		img = Image.open(io.BytesIO(image_data))
		
		# Convert RGBA images to RGB with white background
		if img.mode == 'RGBA':
			background = Image.new('RGB', img.size, (255, 255, 255))
			background.paste(img, mask=img.split()[3])
			img = background
		elif img.mode != 'RGB':
			img = img.convert('RGB')
		
		# Resize if enabled and necessary
		if RESIZE_IMAGES:
			width, height = img.size
			if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
				ratio = min(MAX_IMAGE_WIDTH / width, MAX_IMAGE_HEIGHT / height)
				new_size = (int(width * ratio), int(height * ratio))
				img = img.resize(new_size, Image.Resampling.LANCZOS)
		
		# Convert format if enabled
		if CONVERT_IMAGES:
			if CONVERT_IMAGES_TO_FILETYPE.lower() == 'gif':
				# For black and white GIF
				img = img.convert("L")  # Convert to grayscale first
				dither_method = Image.Dither.FLOYDSTEINBERG if DITHERING_ALGORITHM.upper() == 'FLOYDSTEINBERG' else None
				img = img.convert("1", dither=dither_method)
			else:
				# For other format conversions
				img = img.convert(img.mode)
		
		output = io.BytesIO()
		save_format = CONVERT_IMAGES_TO_FILETYPE.upper() if CONVERT_IMAGES else img.format
		img.save(output, format=save_format, optimize=True)
		return output.getvalue()
		
	except Exception as e:
		print(f"Error optimizing image: {str(e)}")
		return image_data

def fetch_and_cache_image(url, content=None):
	try:
		print(f"Processing image: {url}")
		
		# Generate filename with appropriate extension
		extension = CONVERT_IMAGES_TO_FILETYPE.lower() if CONVERT_IMAGES else "gif"
		file_name = hashlib.md5(url.encode()).hexdigest() + f".{extension}"
		file_path = os.path.join(CACHE_DIR, file_name)
		
		if not os.path.exists(file_path):
			print(f"Optimizing and caching image: {url}")
			if content is None:
				response = requests.get(url, stream=True, headers={"User-Agent": USER_AGENT})
				response.raise_for_status()
				content = response.content
			
			# Only process if image conversion is enabled
			if CONVERT_IMAGES or RESIZE_IMAGES:
				optimized_image = optimize_image(content)
			else:
				optimized_image = content
				
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

# Ensure cache directory exists
if not os.path.exists(CACHE_DIR):
	os.makedirs(CACHE_DIR)

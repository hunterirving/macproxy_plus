# Standard library imports
import hashlib
import io
import mimetypes
import os
import tempfile

# Third-party imports
import requests
from PIL import Image, UnidentifiedImageError
from PILSVG import SVG


CACHE_DIR = os.path.join(os.path.dirname(__file__), "cached_images")
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def get_svg_renderer():
	# If inkscape is installed and in the path, use that, because it supports
	# more SVG functionality. Otherwise, fall back to using skia.
	renderer='skia'
	if 'PATH' in os.environ:
		paths = os.environ['PATH'].split(':')
		for path in paths:
			exp_path = os.path.expandvars(os.path.join(path, 'inkscape'))
			if os.path.exists(exp_path):
				renderer='inkscape'
				break
	return renderer

def is_image_url(url):
	mime_type, _ = mimetypes.guess_type(url)
	return mime_type and mime_type.startswith('image/')

def optimize_image(image_data, resize=True, max_width=512, max_height=342, 
				  convert=True, convert_to='gif', dithering='FLOYDSTEINBERG'):
	try:

		# Try to open the image directly using PIL
		# If this fails, assume we have an SVG, and try to open it using PILSVG.
		try:
			img = Image.open(io.BytesIO(image_data))
		except UnidentifiedImageError:
			# PILSVG doesn't support loading an image directly from a
			# byte stream, only from a file on disk. So create a temp file,
			# save the image data there, and then pass the path to PILSVG.
			with tempfile.NamedTemporaryFile(delete=False) as fp:
				try:
					fp.write(image_data)
					fp.close()
					img = SVG(fp.name).im(renderer=get_svg_renderer())
				finally:
					fp.close()
					os.unlink(fp.name)

		# Convert RGBA images to RGB with white background
		if img.mode == 'RGBA':
			background = Image.new('RGB', img.size, (255, 255, 255))
			background.paste(img, mask=img.split()[3])
			img = background
		elif img.mode != 'RGB':
			img = img.convert('RGB')
		
		# Resize if enabled and necessary
		if resize and max_width and max_height:
			width, height = img.size
			if width > max_width or height > max_height:
				ratio = min(max_width / width, max_height / height)
				new_size = (int(width * ratio), int(height * ratio))
				img = img.resize(new_size, Image.Resampling.LANCZOS)
		
		# Convert format if enabled
		if convert and convert_to:
			if convert_to.lower() == 'gif':
				# For black and white GIF
				img = img.convert("L")  # Convert to grayscale first
				dither_method = Image.Dither.FLOYDSTEINBERG if dithering and dithering.upper() == 'FLOYDSTEINBERG' else None
				img = img.convert("1", dither=dither_method)
			else:
				# For other format conversions
				img = img.convert(img.mode)
		
		output = io.BytesIO()
		save_format = convert_to.upper() if convert and convert_to else img.format
		img.save(output, format=save_format, optimize=True)
		return output.getvalue()
		
	except Exception as e:
		print(f"Error optimizing image: {str(e)}")
		return image_data

def fetch_and_cache_image(url, content=None, resize=True, max_width=512, max_height=342,
						 convert=True, convert_to='gif', dithering='FLOYDSTEINBERG',
						 hash_url=True):
	try:
		print(f"Processing image: {url}")
		
		# Generate filename with appropriate extension
		extension = convert_to.lower() if convert and convert_to else "gif"
		if hash_url:
			file_name = hashlib.md5(url.encode()).hexdigest() + f".{extension}"
		else:
			file_name = url + f".{extension}"
		file_path = os.path.join(CACHE_DIR, file_name)
		
		if not os.path.exists(file_path):
			print(f"Optimizing and caching image: {url}")
			if content is None:
				response = requests.get(url, stream=True, headers={"User-Agent": USER_AGENT})
				response.raise_for_status()
				content = response.content
			
			# Only process if image conversion or resizing is enabled
			if convert or resize:
				optimized_image = optimize_image(
					content,
					resize=resize,
					max_width=max_width,
					max_height=max_height,
					convert=convert,
					convert_to=convert_to,
					dithering=dithering
				)
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

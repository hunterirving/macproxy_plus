import os
import requests
import argparse
from flask import Flask, request, session, g, abort, Response, send_from_directory
from utils.html_utils import transcode_html, transcode_content
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import io
from PIL import Image
import hashlib
import shutil
import mimetypes
from utils.image_utils import is_image_url, fetch_and_cache_image, CACHE_DIR

def load_preset():
	"""
	Load preset configuration and override default settings if a preset is specified
	"""
	if not hasattr(config, 'PRESET') or not config.PRESET:
		return

	preset_name = config.PRESET
	preset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'presets', preset_name)
	preset_file = os.path.join(preset_dir, f"{preset_name}.py")

	if not os.path.exists(preset_dir):
		print(f"Error: Preset directory not found: {preset_dir}")
		print(f"Make sure the preset '{preset_name}' exists in the presets directory")
		quit()

	if not os.path.exists(preset_file):
		print(f"Error: Preset file not found: {preset_file}")
		print(f"Make sure {preset_name}.py exists in the {preset_name} directory")
		quit()

	try:
		# Import the preset module
		import importlib.util
		spec = importlib.util.spec_from_file_location(preset_name, preset_file)
		preset_module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(preset_module)

		# List of variables that can be overridden by presets
		override_vars = [
			'SIMPLIFY_HTML',
			'TAGS_TO_STRIP',
			'TAGS_TO_UNWRAP',
			'ATTRIBUTES_TO_STRIP',
			'CAN_RENDER_INLINE_IMAGES',
			'RESIZE_IMAGES',
			'MAX_IMAGE_WIDTH',
			'MAX_IMAGE_HEIGHT',
			'CONVERT_IMAGES',
			'CONVERT_IMAGES_TO_FILETYPE',
			'DITHERING_ALGORITHM',
			'WEB_SIMULATOR_PROMPT_ADDENDUM',
			'CONVERT_CHARACTERS',
			'CONVERSION_TABLE'
		]

		changes_made = False
		# Override config variables with preset values
		for var in override_vars:
			if hasattr(preset_module, var):
				preset_value = getattr(preset_module, var)
				if not hasattr(config, var) or getattr(config, var) != preset_value:
					changes_made = True
					old_value = getattr(config, var) if hasattr(config, var) else None
					setattr(config, var, preset_value)
					
					# Format the values for printing
					def format_value(val):
						if isinstance(val, (list, dict)):
							return str(val)
						elif isinstance(val, str):
							return f"'{val}'"
						else:
							return str(val)
					if old_value is None:
						val = str(format_value(preset_value)).replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
						truncated = val[:100] + ('...' if len(val) > 100 else '')
						print(f"Preset '{preset_name}' set {var} to {truncated}")
					else:
						old_val = str(format_value(old_value)).replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
						new_val = str(format_value(preset_value)).replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
						old_truncated = old_val[:100] + ('...' if len(old_val) > 100 else '')
						new_truncated = new_val[:100] + ('...' if len(new_val) > 100 else '')
						print(f"Preset '{preset_name}' changed {var} from {old_truncated} to {new_truncated}")
		if changes_made:
			print(f"Successfully loaded preset: {preset_name}")
		else:
			print(f"Loaded preset '{preset_name}' (no changes were necessary)")

	except Exception as e:
		print(f"Error loading preset '{preset_name}': {str(e)}")
		quit()

os.environ['FLASK_ENV'] = 'development'
app = Flask(__name__)
session = requests.Session()

HTTP_ERRORS = (403, 404, 500, 503, 504)
ERROR_HEADER = "[[Macproxy Encountered an Error]]"

# Global variable to store the override extension
override_extension = None

# User-Agent string
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

# Call this function every time the proxy starts
def clear_image_cache():
	if os.path.exists(CACHE_DIR):
		shutil.rmtree(CACHE_DIR)
	os.makedirs(CACHE_DIR, exist_ok=True)

clear_image_cache()

# Try to import config.py first
try:
	import config
except ModuleNotFoundError:
	print("config.py not found, exiting.")
	quit()

# Load preset immediately after config import
load_preset()

# Now get the settings we need after preset has potentially modified them
ENABLED_EXTENSIONS = config.ENABLED_EXTENSIONS

# Load extensions
extensions = {}
domain_to_extension = {}
print('Enabled Extensions: ')
for ext in ENABLED_EXTENSIONS:
	print(ext)
	module = __import__(f"extensions.{ext}.{ext}", fromlist=[''])
	extensions[ext] = module
	domain_to_extension[module.DOMAIN] = module

@app.route("/cached_image/<path:filename>")
def serve_cached_image(filename):
	return send_from_directory(CACHE_DIR, filename, mimetype='image/gif')

def handle_image_request(url):
	# Pass config values to fetch_and_cache_image
	cached_url = fetch_and_cache_image(
		url,
		resize=config.RESIZE_IMAGES,
		max_width=config.MAX_IMAGE_WIDTH,
		max_height=config.MAX_IMAGE_HEIGHT,
		convert=config.CONVERT_IMAGES,
		convert_to=config.CONVERT_IMAGES_TO_FILETYPE,
		dithering=config.DITHERING_ALGORITHM
	)
	if cached_url:
		return send_from_directory(CACHE_DIR, os.path.basename(cached_url), mimetype='image/gif')
	else:
		return abort(404, "Image not found or could not be processed")

@app.route("/", defaults={"path": "/"}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def handle_request(path):
	global override_extension
	parsed_url = urlparse(request.url)
	scheme = parsed_url.scheme
	host = parsed_url.netloc.split(':')[0]  # Remove port if present
	
	if override_extension:
		print(f'Current override extension: {override_extension}')

	override_response = handle_override_extension(scheme)
	if override_response is not None:
		return process_response(override_response, request.url)

	matching_extension = find_matching_extension(host)
	if matching_extension:
		response = handle_matching_extension(matching_extension)
		return process_response(response, request.url)
	
	# Only handle image requests here if we're not using an extension
	if is_image_url(request.url) and not (override_extension or matching_extension):
		return handle_image_request(request.url)

	return handle_default_request()

def handle_override_extension(scheme):
	global override_extension
	if override_extension:
		extension_name = override_extension.split('.')[-1]
		if extension_name in extensions:
			if scheme in ['http', 'https', 'ftp']:
				response = extensions[extension_name].handle_request(request)
				check_override_status(extension_name)
				return process_response(response, request.url)
			else:
				print(f"Warning: Unsupported scheme '{scheme}' for override extension.")
		else:
			print(f"Warning: Override extension '{extension_name}' not found. Resetting override.")
			override_extension = None
	return None  # Return None if no override is active

def check_override_status(extension_name):
	global override_extension
	if hasattr(extensions[extension_name], 'get_override_status') and not extensions[extension_name].get_override_status():
		override_extension = None
		print("Override disabled")

def find_matching_extension(host):
	for domain, extension in domain_to_extension.items():
		if host.endswith(domain):
			return extension
	return None

def handle_matching_extension(matching_extension):
	global override_extension
	print(f"Handling request with matching extension: {matching_extension.__name__}")
	response = matching_extension.handle_request(request)
	
	if hasattr(matching_extension, 'get_override_status') and matching_extension.get_override_status():
		override_extension = matching_extension.__name__
		print(f"Override enabled for {override_extension}")
	
	return response

def process_response(response, url):
	print(f"Processing response for URL: {url}")

	if isinstance(response, tuple):
		if len(response) == 3:
			content, status_code, headers = response
		elif len(response) == 2:
			content, status_code = response
			headers = {}
		else:
			content = response[0]
			status_code = 200
			headers = {}
	elif isinstance(response, Response):
		return response
	else:
		content = response
		status_code = 200
		headers = {}

	content_type = headers.get('Content-Type', '').lower()
	print(f"Content-Type: {content_type}")

	if content_type.startswith('image/'):
		# For image content, use the fetch_and_cache_image function with config values
		cached_url = fetch_and_cache_image(
			url,
			content,
			resize=config.RESIZE_IMAGES,
			max_width=config.MAX_IMAGE_WIDTH,
			max_height=config.MAX_IMAGE_HEIGHT,
			convert=config.CONVERT_IMAGES,
			convert_to=config.CONVERT_IMAGES_TO_FILETYPE,
			dithering=config.DITHERING_ALGORITHM
		)
		if cached_url:
			return send_from_directory(CACHE_DIR, os.path.basename(cached_url), mimetype='image/gif')
		else:
			return abort(404, "Image could not be processed")

	# Handle CSS and JavaScript
	if content_type in ['text/css', 'text/javascript', 'application/javascript', 'application/x-javascript']:
		content = transcode_content(content)
		response = Response(content, status_code)
		response.headers['Content-Type'] = content_type
		return response

	# List of content types that should not be transcoded
	non_transcode_types = [
		'application/octet-stream',
		'application/pdf',
		'application/zip',
		'application/x-zip-compressed',
		'application/x-rar-compressed',
		'application/x-tar',
		'application/x-gzip',
		'application/x-bzip2',
		'application/x-7z-compressed',
		'application/vnd.openxmlformats-officedocument',
		'application/vnd.ms-excel',
		'application/vnd.ms-powerpoint',
		'application/msword',
		'audio/',
		'video/',
		'text/plain'
	]

	# Check if content type is in the list of non-transcode types
	should_transcode = not any(content_type.startswith(t) for t in non_transcode_types)

	if should_transcode:
		print("Transcoding content")
		if isinstance(content, bytes):
			content = content.decode('utf-8', errors='replace')
		content = transcode_html(
			content,
			url,
			whitelisted_domains=config.WHITELISTED_DOMAINS,
			simplify_html=config.SIMPLIFY_HTML,
			tags_to_unwrap=config.TAGS_TO_UNWRAP,
			tags_to_strip=config.TAGS_TO_STRIP,
			attributes_to_strip=config.ATTRIBUTES_TO_STRIP,
			convert_characters=config.CONVERT_CHARACTERS,
			conversion_table=config.CONVERSION_TABLE
		)
	else:
		print(f"Content type {content_type} should not be transcoded, passing through unchanged")

	response = Response(content, status_code)
	for key, value in headers.items():
		if key.lower() not in ['content-encoding', 'content-length']:
			response.headers[key] = value

	print("Finished processing response")
	return response

def handle_default_request():
	url = request.url.replace("https://", "http://", 1)
	headers = prepare_headers()
	
	print(f"Handling default request for URL: {url}")
	
	try:
		resp = send_request(url, headers)
		content = resp.content
		status_code = resp.status_code
		headers = dict(resp.headers)
		return process_response((content, status_code, headers), url)
	except Exception as e:
		print(f"Error in handle_default_request: {str(e)}")
		return abort(500, ERROR_HEADER + str(e))

def prepare_headers():
	headers = {
		"Accept": request.headers.get("Accept"),
		"Accept-Language": request.headers.get("Accept-Language"),
		"Referer": request.headers.get("Referer"),
		"User-Agent": USER_AGENT,
	}
	return headers

def send_request(url, headers):
	print(f"Sending request to: {url}")
	if request.method == "POST":
		return session.post(url, data=request.form, headers=headers, allow_redirects=True)
	else:
		return session.get(url, params=request.args, headers=headers)

@app.after_request
def apply_caching(resp):
	try:
		resp.headers["Content-Type"] = g.content_type
	except:
		pass
	return resp

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Macproxy command line arguments")
	parser.add_argument(
		"--port",
		type=int,
		default=5001,
		action="store",
		help="Port number the web server will run on",
	)
	parser.add_argument(
		"--user-agent",
		type=str,
		default=USER_AGENT,
		action="store",
		help="Spoof as a particular web browser, e.g. \"Mozilla/5.0\"",
	)
	parser.add_argument(
		"--html-formatter",
		type=str,
		choices=["minimal", "html", "html5"],
		default="html5",
		action="store",
		help="The BeautifulSoup html formatter that Macproxy will use",
	)
	arguments = parser.parse_args()
	app.run(host="0.0.0.0", port=arguments.port, debug=False)

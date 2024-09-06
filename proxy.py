import os
import requests
import argparse
from flask import Flask, request, session, g, abort, Response
from html_utils import transcode_html
from urllib.parse import urlparse, urljoin

os.environ['FLASK_ENV'] = 'development'
app = Flask(__name__)
session = requests.Session()

HTTP_ERRORS = (403, 404, 500, 503, 504)
ERROR_HEADER = "[[Macproxy Encountered an Error]]"

# Global variable to store the override extension
override_extension = None

# Try to import config.py from the extensions folder and enable extensions
try:
	import extensions.config as config
	ENABLED_EXTENSIONS = config.ENABLED_EXTENSIONS
except ModuleNotFoundError:
	print("config.py not found in extensions folder, running without extensions")
	ENABLED_EXTENSIONS = []

# Load extensions
extensions = {}
domain_to_extension = {}
print('Enabled Extensions: ')
for ext in ENABLED_EXTENSIONS:
	print(ext)
	module = __import__(f"extensions.{ext}.{ext}", fromlist=[''])
	extensions[ext] = module
	domain_to_extension[module.DOMAIN] = module

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
		return override_response

	matching_extension = find_matching_extension(host)
	if matching_extension:
		return handle_matching_extension(matching_extension)

	return handle_default_request()

def handle_override_extension(scheme):
	global override_extension
	if override_extension:
		extension_name = override_extension.split('.')[-1]
		if extension_name in extensions:
			if scheme in ['http', 'https', 'ftp']:
				response = extensions[extension_name].handle_request(request)
				check_override_status(extension_name)
				return process_response(response)
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
	response = matching_extension.handle_request(request)
	
	if hasattr(matching_extension, 'get_override_status') and matching_extension.get_override_status():
		override_extension = matching_extension.__name__
		print(f"Override enabled for {override_extension}")
	
	return process_response(response)

def process_response(response):
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

	# Transcode content unless it's explicitly text/plain
	if not content_type.startswith('text/plain'):
		if isinstance(content, str):
			content = transcode_html(content, app.config["DISABLE_CHAR_CONVERSION"])
		elif isinstance(content, bytes):
			content = transcode_html(content.decode('utf-8', errors='replace'), app.config["DISABLE_CHAR_CONVERSION"])
	else:
		# For text/plain, ensure content is in bytes
		if isinstance(content, str):
			content = content.encode('utf-8')

	response = Response(content, status_code)
	for key, value in headers.items():
		response.headers[key] = value

	return response

def handle_default_request():
	url = request.url.replace("https://", "http://", 1)
	headers = prepare_headers()
	
	try:
		resp = send_request(url, headers)
	except Exception as e:
		return abort(500, ERROR_HEADER + str(e))

	return process_default_response(resp)

def prepare_headers():
	headers = {
		"Accept": request.headers.get("Accept"),
		"Accept-Language": request.headers.get("Accept-Language"),
		"Referer": request.headers.get("Referer"),
		"User-Agent": request.headers.get("User-Agent"),
	}
	if app.config["USER_AGENT"]:
		headers["User-Agent"] = app.config["USER_AGENT"]
	return headers

def send_request(url, headers):
	if request.method == "POST":
		return session.post(url, data=request.form, headers=headers, allow_redirects=True)
	else:
		return session.get(url, params=request.args, headers=headers)

def process_default_response(resp):
	if resp.status_code in HTTP_ERRORS:
		return abort(resp.status_code)
	
	if "content-type" in resp.headers.keys():
		g.content_type = resp.headers["Content-Type"]
	
	if resp.headers["Content-Type"].startswith("text/html"):
		transcoded_content = transcode_html(
			resp.text,
			app.config["DISABLE_CHAR_CONVERSION"],
		)
		return transcoded_content, resp.status_code
	
	return resp.content, resp.status_code

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
		default="",
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
	parser.add_argument(
		"--disable-char-conversion",
		action="store_true",
		help="Disable the conversion of common typographic characters to ASCII",
	)
	arguments = parser.parse_args()
	app.config["USER_AGENT"] = arguments.user_agent
	app.config["DISABLE_CHAR_CONVERSION"] = arguments.disable_char_conversion
	app.run(host="0.0.0.0", port=arguments.port, debug=False)
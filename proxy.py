import os
import requests
import argparse
from flask import Flask, request, session, g, abort, Response
from html_utils import transcode_html
from urllib.parse import urlparse

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
	host = parsed_url.netloc.split(':')[0]  # Remove port if present
	
	print(f'Current override extension: {override_extension}')

	# Check if we're in override mode
	if override_extension:
		# Extract just the extension name from the full module path
		extension_name = override_extension.split('.')[-1]
		if extension_name in extensions:
			response = extensions[extension_name].handle_request(request)
			# Check if the override has been disabled
			if hasattr(extensions[extension_name], 'get_override_status') and not extensions[extension_name].get_override_status():
				override_extension = None
				print("Override disabled")
			
			# Apply transcode_html to the response if it's HTML
			if isinstance(response, str) and response.strip().startswith('<!DOCTYPE html>'):
				response = transcode_html(response, app.config["DISABLE_CHAR_CONVERSION"])
			return response
		else:
			print(f"Warning: Override extension '{extension_name}' not found. Resetting override.")
			override_extension = None

	# Check if the host matches any of our extensions
	matching_extension = None
	for domain, extension in domain_to_extension.items():
		if host.endswith(domain):
			matching_extension = extension
			break
	
	if matching_extension:
		response = matching_extension.handle_request(request)
		
		# Check if the extension wants to override
		if hasattr(matching_extension, 'get_override_status') and matching_extension.get_override_status():
			override_extension = matching_extension.__name__
			print(f"Override enabled for {override_extension}")
		
		if isinstance(response, tuple):
			content, status_code = response
		elif isinstance(response, Response):
			return response  # If it's already a Response object, return it directly
		else:
			content, status_code = response, 200  # Assume 200 if no status code provided
		
		if isinstance(content, str):  # Assuming HTML content is returned as a string
			content = transcode_html(
				content,
				app.config["DISABLE_CHAR_CONVERSION"],
			)
		return content, status_code

	url = request.url.replace("https://", "http://", 1)
	headers = {
		"Accept": request.headers.get("Accept"),
		"Accept-Language": request.headers.get("Accept-Language"),
		"Referer": request.headers.get("Referer"),
		"User-Agent": request.headers.get("User-Agent"),
	}
	if app.config["USER_AGENT"]:
		headers["User-Agent"] = app.config["USER_AGENT"]
	try:
		if request.method == "POST":
			resp = session.post(url, data=request.form, headers=headers, allow_redirects=True)
		else:
			resp = session.get(url, params=request.args, headers=headers)
	except Exception as e:
		return abort(500, ERROR_HEADER + str(e))

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
	app.run(host="0.0.0.0", port=arguments.port)
import os
import requests
import argparse
from flask import Flask, request, session, g, abort
from html_utils import transcode_html

app = Flask(__name__)
session = requests.Session()

HTTP_ERRORS = (403, 404, 500, 503, 504)
ERROR_HEADER = "[[Macproxy Encountered an Error]]"

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
for ext in ENABLED_EXTENSIONS:
	module = __import__(f"extensions.{ext}.{ext}", fromlist=[''])
	extensions[ext] = module
	domain_to_extension[module.DOMAIN] = module

@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def handle_request(path):
	host = request.host.split(':')[0]  # Remove port if present
	extension = domain_to_extension.get(host)

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
		# If an extension is present, process the content with the extension first
		if extension:
			processed_content = extension.process_html(resp.text, request.path)
		else:
			processed_content = resp.text

		# Transcode HTML after extension processing
		transcoded_content = transcode_html(
			processed_content,
			app.config["HTML_FORMATTER"],
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
	app.config["HTML_FORMATTER"] = arguments.html_formatter
	app.config["DISABLE_CHAR_CONVERSION"] = arguments.disable_char_conversion
	app.run(host="0.0.0.0", port=arguments.port)

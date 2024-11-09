from flask import request, render_template_string
from urllib.parse import urlparse, urlunparse, urljoin
import requests
from bs4 import BeautifulSoup
import datetime
import calendar
import re
import os
import time

DOMAIN = "web.archive.org"
TARGET_DATE = "19960101"
date_update_message = ""
last_timestamp = None
last_request_time = 0
REQUEST_DELAY = 0.5  # Minimum time between requests in seconds

# Import USER_AGENT from proxy
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

# Create a session object for persistent connections
session = requests.Session()
session.headers.update({'User-Agent': USER_AGENT})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
	<title>WayBack Machine</title>
</head>
<body>
	<center>{% if not override_active %}<br>{% endif %}
		<font size="7"><h4>WayBack<br>Machine</h4></font>
		<form method="post">
			{% if override_active %}
				<select name="month">
					{% for month in months %}
						<option value="{{ month }}" {% if month == selected_month %}selected{% endif %}>{{ month }}</option>
					{% endfor %}
				</select>
				<select name="day">
					{% for day in range(1, 32) %}
						<option value="{{ day }}" {% if day == selected_day %}selected{% endif %}>{{ day }}</option>
					{% endfor %}
				</select>
				<select name="year">
					{% for year in range(1996, current_year + 1) %}
						<option value="{{ year }}" {% if year == selected_year %}selected{% endif %}>{{ year }}</option>
					{% endfor %}
				</select>
				<br>
				<input type="submit" name="action" value="set date">
				<input type="submit" name="action" value="disable">
			{% else %}
				<input type="submit" name="action" value="enable">
			{% endif %}
		</form>
		<p>
			{% if override_active %}
				<b>WayBack Machine enabled!</b>{% if date_update_message %} (date updated to <b>{{ date_update_message }}</b>){% endif %}<br>
				Enter a URL in the address bar, or click <b>disable</b> to quit.
			{% else %}
				WayBack Machine disabled.<br>
				Click <b>enable</b> to begin.
			{% endif %}
		</p>
	</center>
</body>
</html>
"""

override_active = False
current_date = datetime.datetime.now()
selected_month = current_date.strftime("%b").upper()
selected_day = current_date.day
selected_year = 1996
current_year = current_date.year
months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

def get_override_status():
	global override_active
	return override_active

def rate_limit_request():
	"""Implement rate limiting between requests"""
	global last_request_time
	current_time = time.time()
	time_since_last_request = current_time - last_request_time
	if time_since_last_request < REQUEST_DELAY:
		time.sleep(REQUEST_DELAY - time_since_last_request)
	last_request_time = time.time()

def extract_timestamp_from_url(url):
	"""Extract timestamp from a Wayback Machine URL"""
	match = re.search(r'/web/(\d{14})/', url)
	return match.group(1) if match else None

def construct_wayback_url(url, timestamp):
	"""Construct a Wayback Machine URL with the given timestamp"""
	return f"https://web.archive.org/web/{timestamp}/{url}"

def make_archive_request(url, use_last_timestamp=True):
	"""Make a request to the archive with rate limiting"""
	global last_timestamp
	
	rate_limit_request()
	
	try:
		if use_last_timestamp and last_timestamp and '/web/' not in url:
			wayback_url = construct_wayback_url(url, last_timestamp)
		else:
			wayback_url = construct_wayback_url(url, TARGET_DATE+"000000")
		
		print(f'Requesting: {wayback_url}')
		response = session.get(wayback_url, timeout=10)
		
		# Extract and save timestamp from successful response
		if response.status_code == 200 and not last_timestamp:
			timestamp = extract_timestamp_from_url(response.url)
			if timestamp:
				last_timestamp = timestamp
				print(f'Found timestamp: {last_timestamp}')
		
		return response
	except Exception as e:
		print(f"Request failed: {str(e)}")
		raise

def extract_original_url(url, base_url):
	"""Extract original URL from Wayback Machine URL format"""
	try:
		if '_static/' in url:
			return None
			
		parsed_url = urlparse(url)
		parsed_base = urlparse(base_url)

		if parsed_url.scheme and parsed_url.netloc and DOMAIN not in parsed_url.netloc:
			return url

		timestamp_pattern = r'/web/\d{14}(?:im_|js_|cs_|fw_)?/'
		if re.search(timestamp_pattern, url):
			match = re.search(r'/web/\d{14}(?:im_|js_|cs_|fw_)?/(?:https?://)?(.+)', url)
			if match:
				actual_url = match.group(1)
				return f'http://{actual_url}' if not actual_url.startswith(('http://', 'https://')) else actual_url

		base_match = re.search(r'/web/\d{14}(?:im_|js_|cs_|fw_)?/(?:https?://)?([^/]+)(/.+)?', parsed_base.path)
		if base_match:
			base_domain = base_match.group(1)
			if url.startswith('/'):
				return f'http://{base_domain}{url}'
			elif not url.startswith(('http://', 'https://')):
				return f'http://{base_domain}/{url}'

		if not url.startswith(('http://', 'https://')):
			if url.startswith('//'):
				return f'http:{url}'
			elif url.startswith('/'):
				base_domain = parsed_base.netloc.split(':')[0]
				return f'http://{base_domain}{url}'
			else:
				base_domain = parsed_base.netloc.split(':')[0]
				base_path = os.path.dirname(parsed_base.path)
				return f'http://{base_domain}{base_path}/{url}'

		return url
	except Exception as e:
		print(f"Error in extract_original_url: {url} - {str(e)}")
		return url

def process_html_content(content, base_url):
	try:
		soup = BeautifulSoup(content, 'html.parser')
		
		# Remove Wayback Machine's injected elements
		for element in soup.select('script[src*="/_static/"], script[src*="archive.org"], \
								 link[href*="/_static/"], div[id*="wm-"], div[class*="wm-"], \
								 style[id*="wm-"], div[id*="donato"], div[id*="playback"]'):
			element.decompose()

		# Process all URLs in the document
		for tag in soup.find_all(['a', 'img', 'script', 'link', 'iframe', 'frame']):
			for attr in ['href', 'src']:
				if tag.get(attr):
					new_url = extract_original_url(tag[attr], base_url)
					if new_url:
						tag[attr] = new_url
					else:
						del tag[attr]

		return str(soup)
	except Exception as e:
		print(f"Error in process_html_content: {str(e)}")
		return f"<html><body><p>Error processing content: {str(e)}</p></body></html>"

def handle_request(req):
	global override_active, selected_month, selected_day, selected_year, TARGET_DATE, date_update_message, last_timestamp

	parsed_url = urlparse(req.url)
	is_wayback_domain = parsed_url.netloc == DOMAIN

	if is_wayback_domain:
		if req.method == 'POST':
			action = req.form.get('action')
			if action == 'enable':
				override_active = True
				date_update_message = ""
			elif action == 'disable':
				override_active = False
				date_update_message = ""
				last_timestamp = None  # Reset timestamp when disabled
			elif action == 'set date':
				override_active = True
				last_timestamp = None  # Reset timestamp when date changes
				
				selected_month = req.form.get('month')
				selected_day = int(req.form.get('day'))
				selected_year = int(req.form.get('year'))

				_, last_day = calendar.monthrange(selected_year, months.index(selected_month) + 1)
				if selected_day > last_day:
					selected_day = last_day

				selected_date = datetime.datetime(selected_year, months.index(selected_month) + 1, selected_day)
				current_date = datetime.datetime.now()

				if selected_year == current_year and selected_date > current_date:
					selected_date = current_date
					
				selected_year = selected_date.year
				selected_month = months[selected_date.month - 1]
				selected_day = selected_date.day

				month_num = str(selected_date.month).zfill(2)
				TARGET_DATE = f"{selected_year}{month_num}{str(selected_day).zfill(2)}"
				
				date_update_message = f"{selected_month} {selected_day}, {selected_year}"

		return render_template_string(HTML_TEMPLATE, 
								   override_active=override_active,
								   months=months,
								   selected_month=selected_month,
								   selected_day=selected_day,
								   selected_year=selected_year,
								   current_year=current_year,
								   date_update_message=date_update_message), 200

	try:
		url = req.url
		print(f'Handling request for: {url}')
		
		response = make_archive_request(url)
		
		if response.status_code != 200:
			raise Exception(f"Failed to fetch content: HTTP {response.status_code}")
			
		content = response.content
		if not content:
			raise Exception("Empty response received from archive")
		
		content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
		print(f"Content-Type: {content_type}")
		
		if content_type.startswith('image/'):
			return content, response.status_code, {'Content-Type': content_type}

		if content_type.startswith('text/html'):
			content = content.decode('utf-8', errors='replace')
			processed_content = process_html_content(content, url)
			return processed_content, response.status_code, {'Content-Type': 'text/html'}
		
		elif content_type.startswith('text/') or content_type in ['application/javascript', 'application/json']:
			decoded_content = content.decode('utf-8', errors='replace')
			return decoded_content, response.status_code, {'Content-Type': content_type}
		
		else:
			return content, response.status_code, {'Content-Type': content_type}
	
	except Exception as e:
		print(f"Error occurred: {str(e)}")
		return f"<html><body><p>Error fetching archived page: {str(e)}</p></body></html>", 500, {'Content-Type': 'text/html'}
from flask import request, render_template_string
from urllib.parse import urlparse, urlunparse, urljoin
from waybackpy import WaybackMachineCDXServerAPI
import requests
from bs4 import BeautifulSoup
import datetime
import calendar
import re
import mimetypes
import os

DOMAIN = "web.archive.org"
TARGET_DATE = "19960101"
date_update_message = ""

# Global resource cache
resource_cache = {}

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

def make_api_request(url, headers=None):
	cache_key = url
	if cache_key in resource_cache:
		return resource_cache[cache_key]
	
	if headers is None:
		headers = {}
	
	response = requests.get(url, headers=headers)
	resource_cache[cache_key] = response
	return response

def get_cached_snapshot(url, target_date):
	try:
		user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
		cdx_api = WaybackMachineCDXServerAPI(url, user_agent)
		target_datetime = datetime.datetime.strptime(target_date, "%Y%m%d")
		
		snapshots = cdx_api.snapshots()
		snapshot = next((s for s in snapshots if datetime.datetime.strptime(s.timestamp, "%Y%m%d%H%M%S") >= target_datetime), None)
		
		if snapshot:
			return snapshot.archive_url
		return None
	except Exception as e:
		print(f"Cache error for {url}: {str(e)}")
		return None

def extract_original_url(url, base_url):
	"""Extract original URL from Wayback Machine URL format"""
	try:
		# Skip _static resources entirely
		if '_static/' in url:
			return None
			
		# Parse the URL and base_url
		parsed_url = urlparse(url)
		parsed_base = urlparse(base_url)

		# If the URL is already a full URL and not a Wayback Machine URL, return it
		if parsed_url.scheme and parsed_url.netloc and DOMAIN not in parsed_url.netloc:
			return url

		# Handle Wayback Machine timestamp format (web/YYYYMMDDHHMMSS)
		timestamp_pattern = r'/web/\d{14}(?:im_|js_|cs_|fw_)?/'
		if re.search(timestamp_pattern, url):
			# Extract the actual URL part after the timestamp
			match = re.search(r'/web/\d{14}(?:im_|js_|cs_|fw_)?/(?:https?://)?(.+)', url)
			if match:
				actual_url = match.group(1)
				return f'http://{actual_url}' if not actual_url.startswith(('http://', 'https://')) else actual_url

		# If it's a Wayback Machine URL in the base, extract the original domain
		base_match = re.search(r'/web/\d{14}(?:im_|js_|cs_|fw_)?/(?:https?://)?([^/]+)(/.+)?', parsed_base.path)
		if base_match:
			base_domain = base_match.group(1)
			# Handle relative URLs
			if url.startswith('/'):
				return f'http://{base_domain}{url}'
			elif not url.startswith(('http://', 'https://')):
				return f'http://{base_domain}/{url}'

		# For relative URLs without Wayback Machine formatting
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
		
		# Remove Wayback Machine's injected elements first
		for script in soup.find_all('script'):
			if script.get('src'):
				if any(x in script['src'] for x in ['/_static/', 'archive.org', 'wombat.js', 'bundle-playback.js', 'ruffle.js']):
					script.decompose()
			elif script.string and 'archive.org' in script.string:
				script.decompose()

		# Remove Wayback Machine styles
		for link in soup.find_all('link', rel='stylesheet'):
			if '/_static/' in link.get('href', ''):
				link.decompose()

		# Remove WayBack Machine toolbar and related elements
		for element in soup.find_all(class_=lambda x: x and ('wb-' in x or 'wm-' in x)):
			element.decompose()
		
		# Process frames and iframes
		for frame in soup.find_all(['frame', 'iframe']):
			if frame.get('src'):
				new_src = extract_original_url(frame['src'], base_url)
				if new_src:
					frame['src'] = new_src
				else:
					frame.decompose()
		
		# Process all links
		for a in soup.find_all('a', href=True):
			new_href = extract_original_url(a['href'], base_url)
			if new_href:
				a['href'] = new_href
			else:
				del a['href']
		
		# Process all images, scripts, and other resources
		for tag in soup.find_all(['img', 'script', 'link'], src=True):
			new_src = extract_original_url(tag['src'], base_url)
			if new_src:
				tag['src'] = new_src
			else:
				del tag['src']
		
		# Process remaining href attributes
		for tag in soup.find_all(href=True):
			new_href = extract_original_url(tag['href'], base_url)
			if new_href:
				tag['href'] = new_href
			else:
				del tag['href']
		
		# Handle background images in style attributes
		for tag in soup.find_all(style=True):
			style = tag['style']
			urls = re.findall(r'url\([\'"]?([^\'" \)]+)', style)
			for url in urls:
				new_url = extract_original_url(url, base_url)
				if new_url:
					style = style.replace(url, new_url)
			tag['style'] = style

		return str(soup)
		
	except Exception as e:
		print(f"Error in process_html_content: {str(e)}")
		return f"<html><body><p>Error processing content: {str(e)}</p></body></html>"
def handle_request(req):
	global override_active, selected_month, selected_day, selected_year, TARGET_DATE, date_update_message

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
			elif action == 'set date':
				override_active = True
				
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
		
		archive_url = get_cached_snapshot(url, TARGET_DATE)
		if not archive_url:
			raise Exception("No snapshot found after the target date")
			
		print(f'Found snapshot: {archive_url}')
		
		headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
		response = make_api_request(archive_url, headers=headers)
		
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
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
last_request_time = 0
REQUEST_DELAY = 0.2  # Minimum time between requests in seconds

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

def find_closest_snapshot(url):
	"""Use Wayback CDX API to find closest available snapshot"""
	try:
		cdx_url = f"https://web.archive.org/cdx/search/cdx"
		params = {
			'url': url,
			'matchType': 'prefix',
			'limit': -1,  # Get all results
			'from': TARGET_DATE,  # Start from our target date
			'output': 'json',
			'sort': 'closest',
			'filter': '!statuscode:[500 TO 599]'  # Exclude server errors
		}
		
		response = session.get(cdx_url, params=params, timeout=10)
		if response.status_code == 200:
			data = response.json()
			if len(data) > 1:  # First row is header
				# Sort snapshots to prefer earlier dates
				snapshots = data[1:]  # Skip header row
				target_timestamp = int(TARGET_DATE + "000000")
				
				# Sort by absolute difference from target date, but prefer later dates
				snapshots.sort(key=lambda x: (
					abs(int(x[1]) - target_timestamp),  # Primary sort: absolute distance from target
					-int(x[1])  # Secondary sort: reverse timestamp (prefer earlier dates)
				))
				
				for snapshot in snapshots:
					timestamp = snapshot[1]
					return timestamp
					
	except Exception as e:
		print(f"Error finding snapshot: {str(e)}")
	return TARGET_DATE + "000000"  # Return target date if no snapshot found

def make_archive_request(url, follow_redirects=True, original_timestamp=None):
	"""Make a request to the archive with rate limiting and redirect handling"""
	rate_limit_request()
	
	try:
		# Simply use original_timestamp if provided, otherwise find closest snapshot
		timestamp_to_use = original_timestamp if original_timestamp else find_closest_snapshot(url)
		
		wayback_url = construct_wayback_url(url, timestamp_to_use)
		print(f'Requesting: {wayback_url}')
		response = session.get(wayback_url, timeout=10)
		
		# Handle Wayback Machine redirects
		if response.status_code == 200 and follow_redirects:
			content = response.text
			
			# Check if this is a Wayback Machine redirect page
			if 'Got an HTTP' in content and 'Redirecting to...' in content:
				redirect_match = re.search(r'Redirecting to\.\.\.\s*\n\s*(.*?)\s*$', content, re.MULTILINE)
				if redirect_match:
					redirect_url = redirect_match.group(1).strip()
					print(f'Following Wayback redirect to: {redirect_url}')
					
					# Make a new request to the redirect URL, maintaining original timestamp
					return make_archive_request(
						redirect_url,
						follow_redirects=True,
						original_timestamp=timestamp_to_use
					)
			
			# Also check for JavaScript redirects
			if 'window.location.replace' in content:
				redirect_match = re.search(r'window\.location\.replace\(["\'](.+?)["\']\)', content)
				if redirect_match:
					redirect_url = redirect_match.group(1).strip()
					print(f'Following JS redirect to: {redirect_url}')
					
					# Make a new request to the redirect URL, maintaining original timestamp
					return make_archive_request(
						redirect_url,
						follow_redirects=True,
						original_timestamp=timestamp_to_use
					)
		
		return response
		
	except Exception as e:
		print(f"Request failed: {str(e)}")
		raise

def extract_original_url(url, base_url):
    """Extract original URL from Wayback Machine URL format"""
    try:
        if '_static/' in url:
            return None

        # If it's already a full URL without web.archive.org, return it
        parsed_url = urlparse(url)
        if parsed_url.scheme and parsed_url.netloc and DOMAIN not in parsed_url.netloc:
            return url

        # Get the base domain from the base_url
        base_match = re.search(r'/web/\d{14}(?:im_|js_|cs_|fw_|oe_)?/(?:https?://)?([^/]+)/?', base_url)
        base_domain = base_match.group(1) if base_match else None

        # If the URL contains a Wayback Machine timestamp pattern
        timestamp_pattern = r'/web/\d{14}(?:im_|js_|cs_|fw_|oe_)?/'
        if re.search(timestamp_pattern, url):
            match = re.search(r'/web/\d{14}(?:im_|js_|cs_|fw_|oe_)?/(?:https?://)?(.+)', url)
            if match:
                actual_url = match.group(1)
                return f'http://{actual_url}' if not actual_url.startswith(('http://', 'https://')) else actual_url

        # Handle relative URLs
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                return f'http:{url}'
            elif url.startswith('/'):
                # Use the base domain if we found one
                if base_domain:
                    return f'http://{base_domain}{url}'
            else:
                if base_domain:
                    # Handle relative paths without leading slash
                    base_path = os.path.dirname(parsed_url.path)
                    if base_path and base_path != '/':
                        return f'http://{base_domain}{base_path}/{url}'
                    else:
                        return f'http://{base_domain}/{url}'

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

		# Process regular URL attributes
		url_attributes = ['href', 'src', 'background', 'data', 'poster', 'action']
		
		# URL pattern for CSS url() functions
		url_pattern = r'url\([\'"]?(\/web\/\d{14}(?:im_|js_|cs_|fw_)?\/(?:https?:\/\/)?[^)]+)[\'"]?\)'

		for tag in soup.find_all():
			# Handle regular attributes
			for attr in url_attributes:
				if tag.has_attr(attr):
					original_url = tag[attr]
					new_url = extract_original_url(original_url, base_url)
					if new_url:
						tag[attr] = new_url
					else:
						del tag[attr]

			# Handle inline styles
			if tag.has_attr('style'):
				style_content = tag['style']
				tag['style'] = re.sub(url_pattern, 
					lambda m: f'url("{extract_original_url(m.group(1), base_url)}")', 
					style_content)

		# Process <style> tags
		for style_tag in soup.find_all('style'):
			if style_tag.string:
				style_tag.string = re.sub(url_pattern,
					lambda m: f'url("{extract_original_url(m.group(1), base_url)}")',
					style_tag.string)

		return str(soup)
	except Exception as e:
		print(f"Error in process_html_content: {str(e)}")
		return content

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
		
		response = make_archive_request(url)
		
		content = response.content
		if not content:
			raise Exception("Empty response received from archive")
		
		content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
		print(f"Content-Type: {content_type}")
		
		# Even if it's a 404, process and return the content as it might be an archived 404 page
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
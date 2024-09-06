from flask import request, render_template_string
from urllib.parse import urlparse, urlunparse
from waybackpy import WaybackMachineCDXServerAPI
import requests
from bs4 import BeautifulSoup
import datetime
import calendar
import re

DOMAIN = "web.archive.org"
TARGET_DATE = "19960101"
date_update_message = ""

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

def transform_url(url):
	# If the URL is relative (doesn't start with a scheme or '/'), leave it as is
	if not re.match(r'^[a-zA-Z]+://|^/', url):
		return url

	# Parse the URL
	parsed = urlparse(url)

	# Regular expression to match Wayback Machine URL pattern
	wayback_pattern = r'^/web/(\d{14})/(.+)'

	# Case 1: URL starts with "/web/" followed by 14 digits
	if parsed.path.startswith('/web/'):
		match = re.match(wayback_pattern, parsed.path)
		if match:
			original_url = match.group(2)
			return convert_ftp_to_http(original_url)

	# Case 2: Full Wayback Machine URL
	if parsed.netloc == DOMAIN:
		match = re.match(wayback_pattern, parsed.path)
		if match:
			original_url = match.group(2)
			# Ensure the URL has a scheme
			if not re.match(r'^[a-zA-Z]+://', original_url):
				original_url = 'http://' + original_url
			return convert_ftp_to_http(original_url)

	# If it's not a Wayback Machine URL, still convert FTP to HTTP
	return convert_ftp_to_http(url)

def convert_ftp_to_http(url):
	parsed = urlparse(url)
	if parsed.scheme == 'ftp':
		# Change the scheme to 'http' and reconstruct the URL
		new_parsed = parsed._replace(scheme='http')
		return urlunparse(new_parsed)
	return url

def process_html_content(content):
	soup = BeautifulSoup(content, 'html.parser')
	
	# Process all links
	for a in soup.find_all('a', href=True):
		a['href'] = transform_url(a['href'])
	
	# Process all images, scripts, and other resources
	for tag in soup.find_all(['img', 'script', 'link'], src=True):
		tag['src'] = transform_url(tag['src'])
	for tag in soup.find_all('link', href=True):
		tag['href'] = transform_url(tag['href'])
	
	return str(soup)

def extract_original_url(wayback_url):
	parsed = urlparse(wayback_url)
	if parsed.netloc == DOMAIN and '/web/' in parsed.path:
		path_parts = parsed.path.split('/', 3)
		if len(path_parts) >= 4:
			return 'http://' + path_parts[3]
	return wayback_url

def handle_request(req):
	global override_active, selected_month, selected_day, selected_year, TARGET_DATE, current_year, date_update_message

	parsed_url = urlparse(req.url)
	is_wayback_domain = parsed_url.netloc == DOMAIN

	if is_wayback_domain:
		if req.method == 'POST':
			action = req.form.get('action')
			if action == 'enable':
				override_active = True
				date_update_message = ""  # Clear the message when enabling
			elif action == 'disable':
				override_active = False
				date_update_message = ""  # Clear the message when disabling
			elif action == 'set date':
				# Always enable override when setting date
				override_active = True

				selected_month = req.form.get('month')
				selected_day = int(req.form.get('day'))
				selected_year = int(req.form.get('year'))

				# Clamp the day to the correct range for the selected month and year
				_, last_day = calendar.monthrange(selected_year, months.index(selected_month) + 1)
				if selected_day > last_day:
					selected_day = last_day

				# Create a datetime object for the selected date and current date
				selected_date = datetime.datetime(selected_year, months.index(selected_month) + 1, selected_day)
				current_date = datetime.datetime.now()

				# If the selected year is the current year, clamp the date to today or earlier
				if selected_year == current_year and selected_date > current_date:
					selected_date = current_date
					
				# Update selected values
				selected_year = selected_date.year
				selected_month = months[selected_date.month - 1]
				selected_day = selected_date.day

				# Update TARGET_DATE
				month_num = str(selected_date.month).zfill(2)
				TARGET_DATE = f"{selected_year}{month_num}{str(selected_day).zfill(2)}"
				
				# Update the date_update_message
				date_update_message = f"{selected_month} {selected_day}, {selected_year}"

		return render_template_string(HTML_TEMPLATE, 
									  override_active=override_active,
									  months=months,
									  selected_month=selected_month,
									  selected_day=selected_day,
									  selected_year=selected_year,
									  current_year=current_year,
									  date_update_message=date_update_message), 200

	# If we're here, override is active and we're handling a non-wayback domain
	try:
		print('Handling request for:', req.url)
		
		url = req.url
		
		user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
		cdx_api = WaybackMachineCDXServerAPI(url, user_agent)
		
		target_date = datetime.datetime.strptime(TARGET_DATE, "%Y%m%d")
		
		print(f'Searching for first snapshot after {target_date} for {url}')
		
		# Get an iterator of all snapshots
		snapshots = cdx_api.snapshots()
		
		# Find the first snapshot after the target date
		snapshot = next((s for s in snapshots if datetime.datetime.strptime(s.timestamp, "%Y%m%d%H%M%S") > target_date), None)
		
		if snapshot is None:
			raise Exception("No snapshot found after the target date")
		
		print('Snapshot found:', snapshot.archive_url)
		
		# Fetch the content of the archived page
		response = requests.get(snapshot.archive_url, headers={'User-Agent': user_agent})
		content = response.text
		print("Content fetched, length:", len(content))
		
		# Process the content based on the protocol
		if parsed_url.scheme in ['http', 'https']:
			processed_content = process_html_content(content)
		elif parsed_url.scheme == 'ftp':
			processed_content = content  # For FTP, we don't need to process the content
		else:
			raise Exception(f"Unsupported protocol: {parsed_url.scheme}")
		
		# Return the processed content and status code
		return processed_content, response.status_code, {'Content-Type': 'text/plain' if parsed_url.scheme == 'ftp' else 'text/html'}
	
	except Exception as e:
		print("Error occurred:", str(e))
		error_message = f"Error fetching archived page: {str(e)}"
		return f"<html><body><p>{error_message}</p></body></html>", 500, {'Content-Type': 'text/html'}
	
	except Exception as e:
		print("Error occurred:", str(e))
		error_message = f"Error fetching archived page: {str(e)}"
		return f"<html><body><p>{error_message}</p></body></html>", 500, {'Content-Type': 'text/html'}
from flask import request, render_template_string
from urllib.parse import urlparse, urljoin
from waybackpy import WaybackMachineCDXServerAPI
import requests
from bs4 import BeautifulSoup
import datetime
import calendar

DOMAIN = "web.archive.org"
TARGET_DATE = "19960101"

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
				<table>
					<tr>
						<td>
							<select name="month">
								{% for month in months %}
									<option value="{{ month }}" {% if month == selected_month %}selected{% endif %}>{{ month }}</option>
								{% endfor %}
							</select>
						</td>
						<td>
							<select name="day">
								{% for day in range(1, 32) %}
									<option value="{{ day }}" {% if day == selected_day %}selected{% endif %}>{{ day }}</option>
								{% endfor %}
							</select>
						</td>
						<td>
							<select name="year">
								{% for year in range(1996, current_year + 1) %}
									<option value="{{ year }}" {% if year == selected_year %}selected{% endif %}>{{ year }}</option>
								{% endfor %}
							</select>
						</td>
					</tr>
				</table>
				<input type="submit" name="action" value="set date">
				<input type="submit" name="action" value="disable">
			{% else %}
				<input type="submit" name="action" value="enable">
			{% endif %}
		</form>
		<p>
			{% if override_active %}
				<b>wayback machine enabled!</b><br>
				enter a URL in the address bar, or click <b>disable</b> to quit.
			{% else %}
				wayback machine disabled.<br>
				click <b>enable</b> to begin.
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
	parsed = urlparse(url)
	if parsed.netloc == DOMAIN and '/web/' in parsed.path:
		# Extract the original URL from the Wayback Machine URL
		path_parts = parsed.path.split('/', 3)
		if len(path_parts) >= 4:
			original_url = path_parts[3]
			if not original_url.startswith(('http://', 'https://')):
				original_url = 'http://' + original_url
			if parsed.query:
				original_url += f'?{parsed.query}'
			return original_url
	return url

def process_html_content(content, base_url):
	soup = BeautifulSoup(content, 'html.parser')
	
	# Process all links
	for a in soup.find_all('a', href=True):
		a['href'] = transform_url(urljoin(base_url, a['href']))
	
	# Process all images, scripts, and other resources
	for tag in soup.find_all(['img', 'script', 'link'], src=True):
		tag['src'] = transform_url(urljoin(base_url, tag['src']))
	for tag in soup.find_all('link', href=True):
		tag['href'] = transform_url(urljoin(base_url, tag['href']))
	
	return str(soup)

def handle_request(req):
	global override_active, selected_month, selected_day, selected_year, TARGET_DATE, current_year

	parsed_url = urlparse(req.url)
	is_wayback_domain = parsed_url.netloc == DOMAIN

	if is_wayback_domain:
		if req.method == 'POST':
			action = req.form.get('action')
			if action == 'enable':
				override_active = True
			elif action == 'disable':
				override_active = False
			elif action == 'set date':
				selected_month = req.form.get('month')
				selected_day = int(req.form.get('day'))
				selected_year = int(req.form.get('year'))

				# Clamp the day to the correct range for the selected month and year
				_, last_day = calendar.monthrange(selected_year, months.index(selected_month) + 1)
				if selected_year == current_year:
					last_day = min(last_day, current_date.day)
				if selected_day > last_day:
					selected_day = last_day
					print(f"Day clamped to {selected_day} for {selected_month} {selected_year}")

				# Update TARGET_DATE
				month_num = str(months.index(selected_month) + 1).zfill(2)
				TARGET_DATE = f"{selected_year}{month_num}{str(selected_day).zfill(2)}"
				print(f"TARGET_DATE updated to: {TARGET_DATE}")

		return render_template_string(HTML_TEMPLATE, 
									  override_active=override_active,
									  months=months,
									  selected_month=selected_month,
									  selected_day=selected_day,
									  selected_year=selected_year,
									  current_year=current_year), 200

	# If we're here, override is active and we're handling a non-wayback domain
	try:
		print('Handling request for:', req.url)
		
		url = req.url if req.url.startswith('http') else f'http://{req.url}'
		
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
		
		# Process the HTML content
		processed_content = process_html_content(content, url)
		
		# Return the processed content and status code
		return processed_content, response.status_code, {'Content-Type': 'text/html'}
	
	except Exception as e:
		print("Error occurred:", str(e))
		error_message = f"Error fetching archived page: {str(e)}"
		return f"<html><body><p>{error_message}</p></body></html>", 500, {'Content-Type': 'text/html'}
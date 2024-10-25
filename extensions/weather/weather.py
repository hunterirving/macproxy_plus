from flask import request, redirect
import requests
from bs4 import BeautifulSoup
import config
import urllib.parse

DOMAIN = "weather.gov"
DEFAULT_LOCATION = config.ZIP_CODE

def process_html(content):
	soup = BeautifulSoup(content, 'html.parser')
	
	# Create the basic HTML structure
	html = '<html>\n<head>\n<title>National Weather Service</title>\n</head>\n<body>\n'
	
	# Find and process the current conditions summary
	current_conditions = soup.find('div', id='current_conditions-summary')
	if current_conditions:
		current_temp = current_conditions.find('p', class_='myforecast-current')
		current_condition = current_conditions.find('p', class_='myforecast-current-lrg')
		if current_temp and current_condition:
			summary = f"{current_temp.text} {current_condition.text}"
			html += f'<center><h1>{summary}</h1></center>\n'
	
	# Find and process the detailed forecast
	detailed_forecast = soup.find('div', id='detailed-forecast')
	if detailed_forecast:
		detailed_forecast_body = detailed_forecast.find('div', id='detailed-forecast-body')
		if detailed_forecast_body:
			forecast_rows = detailed_forecast_body.find_all('div', class_='row-forecast')
			for row in forecast_rows:
				label = row.find('div', class_='forecast-label').b.text
				text = row.find('div', class_='forecast-text').text
				html += f'<p><strong>{label}:</strong> {text}</p>\n<br>\n'
		else:
			html += str(detailed_forecast)
	
	# Close the HTML tags
	html += '\n</body>\n</html>'
	
	return html

def handle_request(req):
	if req.method == 'GET':
		base_url = "https://forecast.weather.gov/zipcity.php?inputstring="
		
		# Extract the path from the request
		path = req.path.lstrip('/')
		
		if path:
			# Use the provided path as the location string
			location = path
		else:
			# Use the default location from config
			location = DEFAULT_LOCATION
		
		try:
			# URL encode the location string
			encoded_location = urllib.parse.quote(location)
			full_url = base_url + encoded_location
			
			response = requests.get(full_url)
			processed_content = process_html(response.text)
			return processed_content, response.status_code
		except Exception as e:
			return f"Error: {str(e)}", 500

	return "Method not allowed", 405
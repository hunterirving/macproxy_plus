from flask import request
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import mimetypes

DOMAIN = "hunterirving.com"

def datetimeToPlaceholder(dateString):
	try:
		post_time = datetime.strptime(dateString.strip(), "%a, %d %b %Y %H:%M:%S %Z")
	except ValueError:
		return "Unknown Date"
	
	page_load_time = datetime.utcnow()
	start_of_today = page_load_time.replace(hour=0, minute=0, second=0, microsecond=0)
	dif_in_days = (start_of_today - post_time.replace(hour=0, minute=0, second=0, microsecond=0)).days

	if dif_in_days == 0:
		return "Today"
	elif dif_in_days == 1:
		return "Yesterday"
	elif dif_in_days < 7:
		return "A Few Days Ago"
	elif dif_in_days < 365:
		return "A While Ago"
	else:
		return "Ages ago"

def handle_request(req):
	if req.host == DOMAIN:
		url = f"https://{DOMAIN}{req.path}"
		try:
			response = requests.get(url)
			response.raise_for_status()  # Raise an exception for bad status codes
			
			# Check if the content is an image	
			content_type = response.headers.get('Content-Type', '')
			if content_type.startswith('image/'):
				# For images, return the content as-is
				return response.content, response.status_code, {'Content-Type': content_type}

			# For non-image content, proceed with HTML processing
			try:
				html_content = response.content.decode('utf-8')
			except UnicodeDecodeError:
				html_content = response.content.decode('iso-8859-1')

			soup = BeautifulSoup(html_content, 'html.parser')

			if req.path.startswith('/gobbler'):
				# Remove all img tags
				for img in soup.find_all('img'):
					img.decompose()

				# Remove all svg tags
				for svg in soup.find_all('svg'):
					svg.decompose()

				# Remove the div with id "follow_container"
				follow_container = soup.find('div', id='follow_container')
				if follow_container:
					follow_container.decompose()

				# Remove the span with id "website_url"
				website_url = soup.find('span', id='website_url')
				if website_url:
					website_url.decompose()

				# Remove the div with id "joined_container"
				joined_container = soup.find('div', id='joined_container')
				if joined_container:
					joined_container.decompose()

				# Wrap the div with id "display_name" with a <b> tag and add a <br> after it
				display_name = soup.find('div', id='display_name')
				if display_name:
					display_name.wrap(soup.new_tag('b'))
					display_name.insert_after(soup.new_tag('br'))

				# Insert <br> after specific elements
				elements_to_br = [
					('div', 'username'),
					('div', 'bio_text')
				]

				for tag, id_value in elements_to_br:
					element = soup.find(tag, id=id_value)
					if element:
						element.insert_after(soup.new_tag('br'))

				# Insert " | " after the div with id "follows"
				follows = soup.find('div', id='follows')
				if follows:
					follows.insert_after(", ")

				# Process gobble_prototype divs
				for gobble in soup.find_all('div', class_='gobble_prototype'):
					# Wrap the first div with <b> tags, excluding the '@' character
					first_div = gobble.find('div')
					if first_div and first_div.string:
						text = first_div.string.strip()
						if text.startswith('@'):
							first_char = text[0]
							rest_of_text = text[1:]
							first_div.clear()
							first_div.append(first_char)
							b_tag = soup.new_tag('b')
							b_tag.string = rest_of_text
							first_div.append(b_tag)
						else:
							first_div.string = text
							first_div.wrap(soup.new_tag('b'))
					first_div.insert_after(soup.new_tag('br'))

					# Process gobble_proto_body
					body = gobble.find('div', class_='gobble_proto_body')
					if body:
						body.insert_after(soup.new_tag('br'))
						body.insert_after(soup.new_tag('br'))

					# Process gobble_proto_date
					date = gobble.find('div', class_='gobble_proto_date')
					if date and date.string:
						date.string = datetimeToPlaceholder(date.string)
						font_tag = soup.new_tag('font', size="2")
						date.wrap(font_tag)
						date.insert_after(" - ")

					# Process the final div within gobble_prototype
					divs = gobble.find_all('div', recursive=False)
					if divs:
						final_div = divs[-1]
						if final_div.string:
							final_div.string = datetimeToPlaceholder(final_div.string)
						font_tag = soup.new_tag('font', size="2")
						final_div.wrap(font_tag)
						final_div.insert_after(soup.new_tag('br'))

			# Convert the soup back to a string for all paths
			modified_html = str(soup)
			
			return modified_html, response.status_code

		except requests.RequestException as e:
			return f"Error: {str(e)}", 500
		except Exception as e:
			return f"Error: {str(e)}", 500
	else:
		return "Not Found", 404
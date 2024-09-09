import requests
from flask import redirect
from bs4 import BeautifulSoup
from urllib.parse import urljoin

DOMAIN = "wiby.me"

def handle_request(request):
	if "surprise" in request.path:
		return handle_surprise(request)
	else:
		url = request.url.replace("https://", "http://", 1)

		resp = requests.get(url)
		
		# If it's the homepage, modify the page structure
		if url == "http://wiby.me" or url == "http://wiby.me/":
			surprise_url = get_final_surprise_url()
			content = modify_page_structure(resp.content, surprise_url)
			return content, resp.status_code
		else:
			return resp.content, resp.status_code

def handle_surprise(request):
	url = get_final_surprise_url()
	return redirect(url)

def get_final_surprise_url():
	url = "http://wiby.me/surprise"
	max_redirects = 10
	redirects = 0

	while redirects < max_redirects:
		resp = requests.get(url, allow_redirects=False)

		if resp.status_code in (301, 302, 303, 307, 308):
			url = urljoin(url, resp.headers['Location'])
			redirects += 1
			continue

		if resp.status_code == 200:
			soup = BeautifulSoup(resp.content, 'html.parser')
			meta_tag = soup.find("meta", attrs={"http-equiv": "refresh"})

			if meta_tag:
				content = meta_tag.get("content", "")
				parts = content.split("URL=")
				if len(parts) > 1:
					url = urljoin(url, parts[1].strip("'\""))
					redirects += 1
					continue

		return url

	return url

def modify_page_structure(content, surprise_url):
	soup = BeautifulSoup(content, 'html.parser')
	
	# Update surprise link
	surprise_link = soup.find('a', href="/surprise/")
	if surprise_link:
		surprise_link['href'] = surprise_url
		# Add a <br> directly before the surprise link
		surprise_link.insert_before(soup.new_tag('br'))
	
	# Remove divs with align="right"
	for div in soup.find_all('div', align="right"):
		div.decompose()
	
	# Find h1 with class "titlep"
	title = soup.find('h1', class_="titlep")
	if title:
		# Remove the first <br> immediately following the h1 at the same level
		next_sibling = title.find_next_sibling()
		if next_sibling and next_sibling.name == 'br':
			next_sibling.decompose()
		
		# Convert h1 to h5 and wrap in font tag
		new_h5 = soup.new_tag('h5')
		new_h5.string = title.string
		font_tag = soup.new_tag('font', size="8")
		font_tag.append(new_h5)
		title.replace_with(font_tag)
	
	# Modify img with specific aria-label and its parent div
	img = soup.find('img', attrs={"aria-label": "Lighthouse overlooking the sea."})
	if img:
		img['width'] = "100"
		img['height'] = "50"
		
		# Find the parent div of the image
		parent_div = img.find_parent('div')
		if parent_div:
			# Remove some <br>s from the parent div
			first_br = parent_div.find('br')
			if first_br:
				first_br.decompose()
			
			second_br = parent_div.find('br')
			if second_br:
				second_br.decompose()

			# Remove the last <br> from the parent div
			br_tags = parent_div.find_all('br')
			if len(br_tags) >= 2:
				br_tags[-1].decompose()
				br_tags[-2].decompose()

	# Wrap all body content with a single <center> tag
	body = soup.body
	if body:
		body.attrs.clear()  # Remove any attributes from the body tag
		
		# Create a new center tag
		center_tag = soup.new_tag("center")
		
		# Move all contents of the body into the center tag
		for content in body.contents[:]:  # Use a copy of contents to avoid modifying during iteration
			center_tag.append(content)
		
		# Clear the body and append the center tag
		body.clear()
		body.append(center_tag)
	
	return str(soup)
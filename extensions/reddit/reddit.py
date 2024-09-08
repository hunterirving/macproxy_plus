import requests
from bs4 import BeautifulSoup
from flask import Response
import io
from PIL import Image
import base64
import hashlib
import os
import shutil
import mimetypes

DOMAIN = "reddit.com"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cached_images")
image_counter = 0
MAX_WIDTH = 512
MAX_HEIGHT = 342

def clear_image_cache():
	global image_counter
	if os.path.exists(CACHE_DIR):
		shutil.rmtree(CACHE_DIR)
	os.makedirs(CACHE_DIR, exist_ok=True)
	image_counter = 0

# Call this function when the extension is loaded
clear_image_cache()

def optimize_image(image_data):
	img = Image.open(io.BytesIO(image_data))
	
	# Calculate the new size while maintaining aspect ratio
	width, height = img.size
	if width > MAX_WIDTH or height > MAX_HEIGHT:
		ratio = min(MAX_WIDTH / width, MAX_HEIGHT / height)
		new_size = (int(width * ratio), int(height * ratio))
		img = img.resize(new_size, Image.LANCZOS)
	
	# Convert to black and white
	img = img.convert("1")
	
	# Save as 1-bit GIF
	output = io.BytesIO()
	img.save(output, format="GIF", optimize=True)
	return output.getvalue()

def fetch_and_cache_image(url):
	global image_counter
	try:
		response = requests.get(url, stream=True)
		response.raise_for_status()
		
		# Optimize the image
		optimized_image = optimize_image(response.content)
		
		# Increment the counter and use it for the filename
		image_counter += 1
		file_name = f"img_{image_counter:04d}.gif"
		file_path = os.path.join(CACHE_DIR, file_name)
		
		with open(file_path, 'wb') as f:
			f.write(optimized_image)
		
		return f"http://reddit.com/cached_image/{file_name}"
	except Exception as e:
		print(f"Error processing image: {str(e)}")
		return None

def handle_request(request):
	if request.method != 'GET':
		return Response("Only GET requests are supported", status=405)

	url = request.url
	if url.startswith("http://reddit.com/cached_image/"):
		file_name = url.split("/")[-1]
		file_path = os.path.join(CACHE_DIR, file_name)
		if os.path.exists(file_path):
			with open(file_path, 'rb') as f:
				return Response(f.read(), mimetype='image/gif')
		else:
			return Response("Image not found", status=404)

	if not url.startswith(('http://old.reddit.com', 'https://old.reddit.com')):
		url = url.replace("reddit.com", "old.reddit.com", 1)
	
	headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
	}
	
	try:
		resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
		resp.raise_for_status()
		return process_content(resp.content, url)
	except requests.RequestException as e:
		return Response(f"An error occurred: {str(e)}", status=500)

def process_content(content, url):
	soup = BeautifulSoup(content, 'html.parser')
	
	new_soup = BeautifulSoup('', 'html.parser')
	html = new_soup.new_tag('html')
	new_soup.append(html)
	
	head = new_soup.new_tag('head')
	html.append(head)
	
	title = new_soup.new_tag('title')
	title.string = soup.title.string if soup.title else "Reddit"
	head.append(title)
	
	body = new_soup.new_tag('body')
	html.append(body)
	
	table = new_soup.new_tag('table', width="100%")
	body.append(table)
	tr = new_soup.new_tag('tr')
	table.append(tr)
	
	left_cell = new_soup.new_tag('td', align="left")
	right_cell = new_soup.new_tag('td', align="right")
	tr.append(left_cell)
	tr.append(right_cell)
	
	left_font = new_soup.new_tag('font', size="4")
	left_cell.append(left_font)
	
	b1 = new_soup.new_tag('b')
	b1.string = "reddit"
	left_font.append(b1)
	
	parts = url.split('reddit.com', 1)[1].split('/')
	if len(parts) > 2 and parts[1] == 'r':
		subreddit = parts[2]
		left_font.append(" | ")
		s = new_soup.new_tag('span')
		s.string = f"r/{subreddit}".lower()
		left_font.append(s)
	
	# Add tabmenu items for non-comment pages
	if "/comments/" not in url:
		tabmenu = soup.find('ul', class_='tabmenu')
		if tabmenu:
			right_font = new_soup.new_tag('font', size="4")
			right_cell.append(right_font)
			menu_items = tabmenu.find_all('li')
			for li in menu_items:
				a = li.find('a')
				if a and a.string in ['hot', 'new', 'top']:
					if 'selected' in li.get('class', []):
						right_font.append(a.string)
					else:
						href = a['href']
						if href.startswith(('http://old.reddit.com', 'https://old.reddit.com')):
							href = href.replace('//old.reddit.com', '//reddit.com', 1)
						new_a = new_soup.new_tag('a', href=href)
						new_a.string = a.string
						right_font.append(new_a)
					right_font.append(" ")
	
	hr = new_soup.new_tag('hr')
	body.append(hr)
	
	if "/comments/" in url:
		body.append(new_soup.new_tag('br'))
		
		thing = soup.find('div', id=lambda x: x and x.startswith('thing_'))
		if thing:
			top_matter = thing.find('div', class_='top-matter')
			if top_matter:
				title_a = top_matter.find('a')
				tagline = top_matter.find('p', class_='tagline', recursive=False)
				
				if title_a:
					d = new_soup.new_tag('div')
					b = new_soup.new_tag('b')
					b.string = title_a.string
					d.append(b)
					d.append(new_soup.new_tag('br'))
					
					if tagline:
						time_element = tagline.find('time', class_='live-timestamp')
						author_element = tagline.find('a', class_='author')
						
						d.append("submitted ")
						if time_element:
							d.append(time_element.string)
						d.append(" by ")
						if author_element:
							b_author = new_soup.new_tag('b')
							b_author.string = author_element.string
							d.append(b_author)
					
					# Add preview images if they exist and are not in gallery-tile-content
					preview_imgs = soup.find_all('img', class_='preview')
					valid_imgs = [img for img in preview_imgs if img.find_parent('div', class_='gallery-tile-content') is None]
					if valid_imgs:
						d.append(new_soup.new_tag('br'))
						d.append(new_soup.new_tag('br'))
						for img in valid_imgs:
							enclosing_a = img.find_parent('a')
							if enclosing_a and enclosing_a.has_attr('href'):
								img_src = enclosing_a['href']
								cached_url = fetch_and_cache_image(img_src)
								if cached_url:
									new_img = new_soup.new_tag('img', src=cached_url, width="50", height="40")
									d.append(new_img)
									d.append(" ")  # Add space between images
					
					# Add post content if it exists
					usertext_body = thing.find('div', class_='usertext-body')
					if usertext_body:
						md_content = usertext_body.find('div', class_='md')
						if md_content:
							d.append(new_soup.new_tag('br'))
							d.append(md_content)
					
					body.append(d)
	else:
		ol = new_soup.new_tag('ol')
		body.append(ol)
		
		site_table = soup.find('div', id='siteTable')
		if site_table:
			for thing in site_table.find_all('div', id=lambda x: x and x.startswith('thing_'), recursive=False):
				title_a = thing.find('a', class_='title')
				permalink = thing.get('data-permalink', '')
				
				if (title_a and 
					'alb.reddit.com' not in title_a.get('href', '') and 
					not permalink.startswith('/user/')):
					
					if permalink:
						title_a['href'] = f"http://reddit.com{permalink}"
					
					li = new_soup.new_tag('li')
					li.append(title_a)
					
					li.append(new_soup.new_tag('br'))
					
					font = new_soup.new_tag('font', size="2")
					author = thing.get('data-author', 'Unknown')
					font.append(f"{author} | ")
					
					time_element = thing.find('time', class_='live-timestamp')
					if time_element:
						font.append(time_element.string)
					else:
						font.append("Unknown time")
					
					buttons = thing.find('ul', class_='buttons')
					if buttons:
						comments_li = buttons.find('li', class_='first')
						if comments_li:
							comments_a = comments_li.find('a', class_='comments')
							if comments_a:
								font.append(f" | {comments_a.string}")
					
					# Add points
					points = thing.get('data-score', 'Unknown')
					font.append(f" | {points} points")
					
					font.append(new_soup.new_tag('br'))
					font.append(new_soup.new_tag('br'))
					
					li.append(font)
					ol.append(li)
	
	return str(new_soup), 200
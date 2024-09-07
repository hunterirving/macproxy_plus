import requests
from bs4 import BeautifulSoup
from flask import Response

DOMAIN = "reddit.com"

session = requests.Session()

def handle_request(request):
	if request.method != 'GET':
		return Response("Only GET requests are supported", status=405)

	url = request.url.replace("reddit.com", "old.reddit.com", 1)
	
	headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
	}
	
	try:
		resp = session.get(url, headers=headers, allow_redirects=True, timeout=10)
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
	
	font = new_soup.new_tag('font', size="4")
	if url == "http://old.reddit.com/" or url == "https://old.reddit.com/":
		b_tag = new_soup.new_tag('b')
		b_tag.string = "reddit"
		font.append(b_tag)
	else:
		parts = url.split('old.reddit.com')[1].split('/')
		subreddit = parts[2] if len(parts) > 2 else ''
		b1 = new_soup.new_tag('b')
		b1.string = "reddit"
		font.append(b1)
		font.append(" | ")
		s = new_soup.new_tag('span')
		s.string = f"r/{subreddit}".lower()
		font.append(s)
	body.append(font)
	
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
					
					# Add preview image if it exists
					preview_img = soup.find('img', class_='preview')
					if preview_img:
						img = new_soup.new_tag('img', src=preview_img['src'], width="50", height="40")
						d.append(new_soup.new_tag('br'))
						d.append(new_soup.new_tag('br'))
						d.append(img)
					
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
					
					font.append(new_soup.new_tag('br'))
					font.append(new_soup.new_tag('br'))
					
					li.append(font)
					ol.append(li)
	
	return str(new_soup), 200
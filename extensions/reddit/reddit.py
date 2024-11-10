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
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def handle_request(request):
	if request.method != 'GET':
		return Response("Only GET requests are supported", status=405)

	url = request.url
	
	if not url.startswith(('http://old.reddit.com', 'https://old.reddit.com')):
		url = url.replace("reddit.com", "old.reddit.com", 1)
	
	try:
		headers = {'User-Agent': USER_AGENT} if USER_AGENT else {}
		resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
		resp.raise_for_status()
		return process_content(resp.content, url)
	except requests.RequestException as e:
		return Response(f"An error occurred: {str(e)}", status=500)

def process_comments(comments_area, parent_element, new_soup, depth=0):
	for comment in comments_area.find_all('div', class_='thing', recursive=False):
		if 'comment' not in comment.get('class', []):
			continue  # Skip if it's not a comment

		comment_div = new_soup.new_tag('div')
		if depth > 0:
			blockquote = new_soup.new_tag('blockquote')
			parent_element.append(blockquote)
			blockquote.append(comment_div)
		else:
			parent_element.append(comment_div)

		# Author, points, and time
		author_element = comment.find('a', class_='author')
		author = author_element.string if author_element else 'Unknown'
		
		score_element = comment.find('span', class_='score unvoted')
		points = score_element.string.split()[0] if score_element else '0'
		
		time_element = comment.find('time', class_='live-timestamp')
		time_passed = time_element.string if time_element else 'Unknown time'
		
		header = new_soup.new_tag('p')
		author_b = new_soup.new_tag('b')
		author_b.string = author
		header.append(author_b)
		header.string = f"{author_b} | {points} points | {time_passed}"
		comment_div.append(header)

		# Comment body
		comment_body = comment.find('div', class_='md')
		if comment_body:
			body_text = comment_body.get_text().strip()
			if body_text:
				body_p = new_soup.new_tag('p')
				body_p.string = body_text
				comment_div.append(body_p)

		# Extra space between comments
		comment_div.append(new_soup.new_tag('br'))

		# Process child comments
		child_area = comment.find('div', class_='child')
		if child_area:
			child_comments = child_area.find('div', class_='sitetable listing')
			if child_comments:
				process_comments(child_comments, comment_div, new_soup, depth + 1)

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
								new_img = new_soup.new_tag('img', src=img_src, width="50", height="40")
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

		# Add a <br> before the <hr> that divides comments and the original post
		body.append(new_soup.new_tag('br'))
		body.append(new_soup.new_tag('br'))
		body.append(new_soup.new_tag('hr'))

		# Add comments
		comments_area = soup.find('div', class_='sitetable nestedlisting')
		if comments_area:
			comments_div = new_soup.new_tag('div')
			body.append(comments_div)
			process_comments(comments_area, comments_div, new_soup)
	else:
		ul = new_soup.new_tag('ul')
		body.append(ul)
		
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
					ul.append(li)

		# Add navigation buttons
		nav_buttons = soup.find('div', class_='nav-buttons')
		if nav_buttons:
			center_tag = new_soup.new_tag('center')
			body.append(center_tag)

			nav_table = new_soup.new_tag('table', width="100%")
			nav_tr = new_soup.new_tag('tr')
			nav_left = new_soup.new_tag('td', align="center")
			nav_right = new_soup.new_tag('td', align="center")
			nav_tr.append(nav_left)
			nav_tr.append(nav_right)
			nav_table.append(nav_tr)
			center_tag.append(nav_table)

			prev_button = nav_buttons.find('span', class_='prev-button')
			if prev_button and prev_button.find('a'):
				prev_link = prev_button.find('a')
				new_prev = new_soup.new_tag('a', href=prev_link['href'].replace('old.reddit.com', 'reddit.com'))
				new_prev.string = '&lt; prev'
				nav_left.append(new_prev)

			next_button = nav_buttons.find('span', class_='next-button')
			if next_button and next_button.find('a'):
				next_link = next_button.find('a')
				new_next = new_soup.new_tag('a', href=next_link['href'].replace('old.reddit.com', 'reddit.com'))
				new_next.string = 'next &gt;'
				nav_right.append(new_next)

	return str(new_soup), 200
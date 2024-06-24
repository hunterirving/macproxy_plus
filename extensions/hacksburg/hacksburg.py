from flask import request, redirect
import requests
from bs4 import BeautifulSoup
from html_utils import transcode_html

DOMAIN = "hacksburg.org"

def process_html(content, path):
	# Parse the HTML
	soup = BeautifulSoup(content, 'html.parser')

	# Replace <div> tag with id="header" with ASCII art version
	header_div = soup.find('div', id='header')
	if header_div:
		ascii_art = r"""
<center>
<pre>
   __ __         __        __                
  / // /__ _____/ /__ ___ / /  __ _________ _
 / _  / _ `/ __/  '_/(_--/ _ \/ // / __/ _ `/
/_//_/\_,_/\__/_/\_\/___/_.__/\_,_/_/  \_, / 
    Blacksburg's Community Workshop   /___/  
</pre>
</center>
"""
		new_header = BeautifulSoup(ascii_art, 'html.parser')
		header_div.replace_with(new_header)

	# Wrap the div with id="nav-links" in a <center> tag
	nav_links_div = soup.find('div', id='nav-links')
	if nav_links_div:
		center_tag = soup.new_tag('center')
		nav_links_div.wrap(center_tag)
		# Insert a <br> after the nav-links div
		nav_links_div.insert_after(soup.new_tag('br'))
		# Insert an <hr> after the nav-links div
		nav_links_div.insert_after(soup.new_tag('hr'))

		# Remove <a> tags with specific hrefs within the nav-links div
		hrefs_to_remove = ["/360tour", "https://meet.hacksburg.org/OpenGroupMeeting"]
		for href in hrefs_to_remove:
			a_tags = nav_links_div.find_all('a', href=href)
			for a_tag in a_tags:
				a_tag.decompose()

		# Insert a " | " between each <a> tag within the div with id="nav-links"
		a_tags = nav_links_div.find_all('a')
		for i in range(len(a_tags) - 1):
			a_tags[i].insert_after(" | ")

		# Bold the <a> tag with id="current-page"
		current_page_a = nav_links_div.find('a', id='current-page')
		if current_page_a:
			b_tag = soup.new_tag('b')
			current_page_a.wrap(b_tag)
    
	# Remove all divs with class="post-header"
	post_headers = soup.find_all('div', class_='post-header')
	for post_header in post_headers:
		post_header.decompose()

	# Convert spans with class="post-section-header" to h3 tags
	post_section_headers = soup.find_all('span', class_='post-section-header')
	for span in post_section_headers:
		h3_tag = soup.new_tag('h3')
		h3_tag.string = span.get_text()
		span.replace_with(h3_tag)

	# Convert spans with class="post-subsection-header" to h3 tags
	post_subsection_headers = soup.find_all('span', class_='post-subsection-header')
	for span in post_subsection_headers:
		h3_tag = soup.new_tag('h3')
		h3_tag.string = span.get_text()
		span.replace_with(h3_tag)

	# Specific modifications for hacksburg.org/contact
	if path == "/contact":
		# Transform the first <h3> within the div with class post-section into a <b> tag, with <br><br> after it
		post_section = soup.find('div', class_='post-section')
		if post_section:
			first_h3 = post_section.find('h3')
			if first_h3:
				b_tag = soup.new_tag('b')
				b_tag.string = first_h3.string
				first_h3.replace_with(b_tag)
				b_tag.insert_after(soup.new_tag('br'))
				b_tag.insert_after(soup.new_tag('br'))

	# Remove the div with id="donation-jar-container"
	donation_jar_div = soup.find('div', id='donation-jar-container')
	if donation_jar_div:
		donation_jar_div.decompose()
		
	# Unwrap specific divs
	divs_to_unwrap = ['closeable', 'post-body', 'post-text']
	for div_id in divs_to_unwrap:
		divs = soup.find_all('div', id=div_id) + soup.find_all('div', class_=div_id)
		for div in divs:
			div.unwrap()

	# Specific modifications for hacksburg.org/join
	if path == "/join":
		# Remove the span with id="student-membership-hint-text"
		student_membership_hint = soup.find('span', id='student-membership-hint-text')
		if student_membership_hint:
			student_membership_hint.decompose()

		# Remove all inputs with name="cmd" or name="hosted_button_id"
		inputs_to_remove = soup.find_all('input', {'name': ['cmd', 'hosted_button_id']})
		for input_tag in inputs_to_remove:
			input_tag.decompose()

		# Wrap all divs with class membership-options-container in <center> tags
		membership_options_containers = soup.find_all('div', class_='membership-options-container')
		for container in membership_options_containers:
			center_tag = soup.new_tag('center')
			container.wrap(center_tag)

		# Decompose <ol>s which are the children of <li>s
		lis_with_ol = soup.find_all('li')
		for li in lis_with_ol:
			child_ols = li.find_all('ol', recursive=False)
			for child_ol in child_ols:
				child_ol.decompose()

		# Insert a <br> after every div with class membership-option if it does not contain an <input> tag
		membership_options = soup.find_all('div', class_='membership-option')
		for div in membership_options:
			if not div.find('input'):
				div.insert_after(soup.new_tag('br'))
				div.insert_after(soup.new_tag('br'))

	# Specific modifications for the main page hacksburg.org
	if path == "/":
		# Find the div with id="bulletin-board" and keep only the div with class="pinned"
		bulletin_board_div = soup.find('div', id='bulletin-board')
		if bulletin_board_div:
			pinned_div = bulletin_board_div.find('div', class_='pinned')
			for child in bulletin_board_div.find_all('div', recursive=False):
				if child != pinned_div:
					child.decompose()


	# Remove all <img> tags
	img_tags = soup.find_all('img')
	for img in img_tags:
		img.decompose()

	# Insert a <br> after each div with class="membership-term"
	membership_terms = soup.find_all('div', class_='membership-term')
	for div in membership_terms:
		div.insert_after(soup.new_tag('br'))

	# Insert two <br>s before the <a> with class="unsubscribe"
	unsubscribe_a = soup.find('a', class_='unsubscribe')
	if unsubscribe_a:
		unsubscribe_a.insert_before(soup.new_tag('br'))
		unsubscribe_a.insert_before(soup.new_tag('br'))
		# Convert the <a> to an <input> with type='submit' and value='Unsubscribe'
		input_tag = soup.new_tag('input', type='submit', value='Unsubscribe')
		center_tag = soup.new_tag('center')
		center_tag.append(input_tag)
		unsubscribe_a.replace_with(center_tag)

	# Specific modifications for hacksburg.org/donate
	if path == "/donate":
		# Unwrap all <p> tags
		p_tags = soup.find_all('p')
		for p in p_tags:
			p.unwrap()

	# Specific modifications for hacksburg.org/about
	if path == "/about":
		# Find the div with id="bulletin-board" and keep the first div with class="post" and remove all others
		bulletin_board_div = soup.find('div', id='bulletin-board')
		if bulletin_board_div:
			posts = bulletin_board_div.find_all('div', class_='post')
			for post in posts[1:]:
				post.decompose()

	# Convert problem characters
	updated_html = str(soup)
	content = transcode_html(updated_html, "html5", False)
	return content

def handle_get(req):
	url = f"https://{DOMAIN}{req.path}"
	try:
		response = requests.get(url)
		processed_content = process_html(response.text, req.path)
		return processed_content, response.status_code
	except Exception as e:
		return f"Error: {str(e)}", 500

def handle_post(req):
	return "POST method not supported", 405

def handle_request(req):
	if req.method == 'POST':
		return handle_post(req)
	elif req.method == 'GET':
		return handle_get(req)
	else:
		return "Not Found", 404

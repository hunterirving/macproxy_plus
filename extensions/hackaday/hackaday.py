from flask import request, redirect, render_template_string
import requests
from bs4 import BeautifulSoup
from html_utils import transcode_html
from datetime import datetime

DOMAIN = "hackaday.com"

def process_html(content):
	# Parse the HTML and remove specific tags
	soup = BeautifulSoup(content, 'html.parser')

	# Remove divs with class="featured-slides"
	featured_slides_divs = soup.find_all('div', class_='featured-slides')
	for div in featured_slides_divs:
		div.decompose()

	# Remove <a> tags with class="skip-link"
	skip_links = soup.find_all('a', class_='skip-link')
	for link in skip_links:
		link.decompose()

	# Remove <a> tags with class="comments-link"
	comments_links = soup.find_all('a', class_='comments-link')
	for link in comments_links:
		link.decompose()

	# Remove <h1> tags with class="widget-title"
	widget_titles = soup.find_all('h1', class_='widget-title')
	for title in widget_titles:
		title.decompose()

	# Remove <a> tags with class="see-all-link"
	see_all_links = soup.find_all('a', class_='see-all-link')
	for link in see_all_links:
		link.decompose()

	# Remove <a> tags with class="comments-counts"
	comments_counts_links = soup.find_all('a', class_='comments-counts')
	for link in comments_counts_links:
		link.decompose()

	# Transform <ul> with class="meta-authors" to a span, remove <li>, and prepend "by: " to inner span with class="fn"
	meta_authors_list = soup.find('ul', class_='meta-authors')
	if meta_authors_list:
		meta_authors_span = soup.new_tag('span', **{'class': 'meta-authors'})
		for child in meta_authors_list.children:
			if child.name == 'li':
				# Skip the <li> element
				continue
			if child.name == 'span' and 'fn' in child.get('class', []):
				# Prepend "by: " to the content of the <span> with class="fn"
				child.insert(0, 'by: ')
				meta_authors_span.append(child)
				meta_authors_span.append(soup.new_tag('br'))
		meta_authors_list.replace_with(meta_authors_span)

	# Replace <h1> tags with class "entry-title" with <b> tags, preserving their inner contents and adding <br><br>
	entry_titles = soup.find_all('h1', class_='entry-title')
	for h1 in entry_titles:
		b_tag = soup.new_tag('b')
		for content in h1.contents:
			b_tag.append(content)
		b_tag.append(soup.new_tag('br'))
		b_tag.append(soup.new_tag('br'))
		h1.replace_with(b_tag)
	
	# Remove all <figure> tags
	figures = soup.find_all('figure')
	for figure in figures:
		figure.decompose()

	# Add <br> directly after the span with class="entry-date"
	entry_date_span = soup.find('span', class_='entry-date')
	if entry_date_span:
		entry_date_span.insert_after(soup.new_tag('br'))

	# Remove <nav> with class="post-navigation"
	post_navigation_nav = soup.find('nav', class_='post-navigation')
	if post_navigation_nav:
		post_navigation_nav.decompose()

	# Remove div with class="entry-featured-image"
	entry_featured_image_div = soup.find('div', class_='entry-featured-image')
	if entry_featured_image_div:
		entry_featured_image_div.decompose()
	
	# Remove specific <p> tags within the div with id="comments" based on text content
	comments_div = soup.find('div', id='comments')
	if comments_div:
		for p in comments_div.find_all('p'):
			if 'Please be kind and respectful' in p.get_text() or 'This site uses Akismet' in p.get_text():
				p.decompose()

	# Remove <ul>s with class="share-post" and class="sharing"
	share_post_lists = soup.find_all('ul', class_='share-post')
	for ul in share_post_lists:
		ul.decompose()

	sharing_lists = soup.find_all('ul', class_='sharing')
	for ul in sharing_lists:
		ul.decompose()

	# Insert <br> after <span> with class="cat-links" in <footer> with class="entry-footer"
	entry_footers = soup.find_all('footer', class_='entry-footer')
	for footer in entry_footers:
		cat_links = footer.find('span', class_='cat-links')
		if cat_links:
			cat_links.insert_after(soup.new_tag('br'))

	# Remove div with id="respond"
	respond_div = soup.find('div', id='respond')
	if respond_div:
		respond_div.decompose()

	# Remove divs with class="share-dialog-content"
	share_dialog_content_divs = soup.find_all('div', class_='share-dialog-content')
	for div in share_dialog_content_divs:
		div.decompose()

	# Remove <span> tags inside <h2> with class="comments-title" but preserve their content
	comments_title = soup.find('h2', class_='comments-title')
	if comments_title:
		for span in comments_title.find_all('span'):
			span.unwrap()

	# Remove divs with class="reply" or class="report-abuse"
	reply_divs = soup.find_all('div', class_='reply')
	for div in reply_divs:
		div.decompose()

	report_abuse_divs = soup.find_all('div', class_='report-abuse')
	for div in report_abuse_divs:
		div.decompose()

	# Remove the <footer> with id="colophon"
	colophon_footer = soup.find('footer', id='colophon')
	if colophon_footer:
		colophon_footer.decompose()

	# Remove the <div> with class="cookie-notifications"
	cookie_notifications_div = soup.find('div', class_='cookie-notifications')
	if cookie_notifications_div:
		cookie_notifications_div.decompose()

	# Remove the <div> with class="sidebar-widget-wrapper"
	sidebar_widget_wrapper = soup.find('div', class_='sidebar-widget-wrapper')
	if sidebar_widget_wrapper:
		sidebar_widget_wrapper.decompose()
	
	sidebar_widget_wrapper = soup.find('div', class_='sidebar-widget-wrapper')
	if sidebar_widget_wrapper:
		sidebar_widget_wrapper.decompose()

	# Remove the <div> with id="secondary-bottom-ad"
	secondary_bottom_ad_div = soup.find('div', id='secondary-bottom-ad')
	if secondary_bottom_ad_div:
		secondary_bottom_ad_div.decompose()

	# Remove divs with id="sidebar-mobile-1" or id="sidebar-mobile-2"
	sidebar_mobile_1_divs = soup.find_all('div', id='sidebar-mobile-1')
	for div in sidebar_mobile_1_divs:
		div.decompose()
	sidebar_mobile_2_divs = soup.find_all('div', id='sidebar-mobile-2')
	for div in sidebar_mobile_2_divs:
		div.decompose()

	# Remove divs with class="ads-one" or class="ads-two"
	ads_one_divs = soup.find_all('div', class_='ads-one')
	for div in ads_one_divs:
		div.decompose()

	ads_two_divs = soup.find_all('div', class_='ads-two')
	for div in ads_two_divs:
		div.decompose()

	# Remove asides with class="widget_text"
	widget_text_asides = soup.find_all('aside', class_='widget_text')
	for aside in widget_text_asides:
		aside.decompose()

	# Remove divs with class="entry-featured-image"
	entry_featured_image_divs = soup.find_all('div', class_='entry-featured-image')
	for div in entry_featured_image_divs:
		div.decompose()

	# Center the nav with class="navigation paging-navigation" using HTML 1.0
	paging_navigation = soup.find('nav', class_='navigation paging-navigation')
	if paging_navigation:
		center_tag = soup.new_tag('center')
		paging_navigation.wrap(center_tag)

	# Remove the div with id="leaderboard"
	leaderboard_div = soup.find('div', id='leaderboard')
	if leaderboard_div:
		leaderboard_div.decompose()

	# Remove divs with class="content-ads-holder"
	content_ads_holder_divs = soup.find_all('div', class_='content-ads-holder')
	for div in content_ads_holder_divs:
		div.decompose()

	# Remove divs with class="series-of-posts-box"
	series_divs = soup.find_all('div', id='series-of-posts-box')
	for div in series_divs:
		div.decompose()

	# Insert a <br> directly after <a> tags with class="more-link"
	more_links = soup.find_all('a', class_='more-link')
	for link in more_links:
		link.insert_after(soup.new_tag('br'))

	# Remove divs with class="entry-mobile-image"
	entry_mobile_image_divs = soup.find_all('div', class_='entry-mobile-image')
	for div in entry_mobile_image_divs:
		div.decompose()

	# Insert a <br> directly after spans with class="tags-links"
	tags_links_spans = soup.find_all('span', class_='tags-links')
	for span in tags_links_spans:
		span.insert_after(soup.new_tag('br'))

	# Remove the img with id="hdTrack"
	hdtrack_img = soup.find('img', id='hdTrack')
	if hdtrack_img:
		hdtrack_img.decompose()

	# Remove full-width inline images from posts
	fullsize_imgs = soup.find_all('img', class_='size-full')
	for img in fullsize_imgs:
		img.decompose()

	# Remove the div with class="jp-carousel-overlay"
	jp_carousel_overlay_divs = soup.find_all('div', class_='jp-carousel-overlay')
	for div in jp_carousel_overlay_divs:
		div.decompose()

	# Remove the div with class="entries-image-holder"
	entries_image_holders = soup.find_all('a', class_='entries-image-holder')
	for a in entries_image_holders:
		a.decompose()
	
	# Transform <ul> with class="recent_entries-list" to remove <ul> and <li> but preserve inner <div> structure
	recent_entries_lists = soup.find_all('ul', class_='recent_entries-list')
	for ul in recent_entries_lists:
		parent = ul.parent
		for li in ul.find_all('li'):
			for div in li.find_all('div', recursive=False):
				parent.append(div)
		li.decompose()
		ul.decompose()

	# Lift <a> tag with class="more-link" and place it directly after the <div> with id="primary"
	more_link = soup.find('a', class_='more-link')
	primary_div = soup.find('div', id='primary')
	if more_link and primary_div:
		more_link.extract()
		p_tag = soup.new_tag('p')
		p_tag.append(more_link)
		primary_div.insert_after(p_tag)

	# Remove the <div> with id="jp-carousel-loading-overlay"
	jp_carousel_loading_overlay_div = soup.find('div', id='jp-carousel-loading-overlay')
	if jp_carousel_loading_overlay_div:
		jp_carousel_loading_overlay_div.decompose()

	# Insert <br>s directly after all divs with class="entry-intro"
	entry_intro_divs = soup.find_all('div', class_='entry-intro')
	for entry_intro in entry_intro_divs:
		entry_intro.insert_after(soup.new_tag('br'))
		entry_intro.insert_after(soup.new_tag('br'))
		entry_intro.insert_after(soup.new_tag('br'))

	# Remove the div with id="secondary"
	secondary_div = soup.find('div', id='secondary')
	if secondary_div:
		secondary_div.decompose()

	# Insert two <br>s at the bottom of (inside of) all divs with class="entry-content" that have itemprop="articleBody"
	entry_content_divs = soup.find_all('div', class_='entry-content', itemprop='articleBody')
	for div in entry_content_divs:
		div.append(soup.new_tag('br'))
		div.append(soup.new_tag('br'))

	# Add a div with copyright information and a search form at the very bottom of the <body> tag
	body_tag = soup.find('body')
	if body_tag:
		# Create the search form
		search_form = soup.new_tag('form', method='post', action='/search')
		search_input = soup.new_tag('input', **{'type': 'text', 'size': '49', 'required': True, 'autocomplete': 'off'})
		search_input['name'] = 'search_term'
		search_button = soup.new_tag('input', **{'type': 'submit', 'value': 'Search'})
		search_form.append(search_input)
		search_form.append(search_button)

		# Center the search form
		search_center_tag = soup.new_tag('center')
		search_center_tag.append(search_form)

		# Create the copyright div
		copyright_div = soup.new_tag('div')
		current_year = datetime.now().year
		copyright_div.string = f"Copyright © {current_year} | Hackaday, Hack A Day, and the Skull and Wrenches Logo are Trademarks of Hackaday.com"
		copyright_p = soup.new_tag('p')
		copyright_p.append(copyright_div)

		# Center the copyright text
		copyright_center_tag = soup.new_tag('center')
		copyright_center_tag.append(copyright_p)

		# Append the search form and copyright text to the body tag
		body_tag.append(search_center_tag)
		body_tag.append(copyright_center_tag)


	# Transform <h2> within the "entry-intro" classed div to <b> and preserve its content
	entry_intro_divs = soup.find_all('div', class_='entry-intro')
	for entry_intro_div in entry_intro_divs:
		h2_tag = entry_intro_div.find('h2')
		if h2_tag:
			b_tag = soup.new_tag('b')
			b_tag.string = h2_tag.string
			h2_tag.replace_with(b_tag)
	
	# Remove all divs with class "comment-metadata"
	comment_metadata_divs = soup.find_all('div', class_='comment-metadata')
	for div in comment_metadata_divs:
		div.decompose()

	# Remove <p> tags within divs with class "recent-post-meta" but keep their content and add a <br> at the top
	recent_post_meta_divs = soup.find_all('div', class_='recent-post-meta')
	for div in recent_post_meta_divs:
		# Insert a <br> at the top of the div
		div.insert(0, soup.new_tag('br'))
		# Unwrap all <p> tags within the div
		for p in div.find_all('p'):
			p.unwrap()

	# Unwrap <a> tags with class "author" within <span> within divs with class "recent-post-meta"
	recent_post_meta_divs = soup.find_all('div', class_='recent-post-meta')
	for div in recent_post_meta_divs:
		spans = div.find_all('span')
		for span in spans:
			author_links = span.find_all('a', class_='author')
			for author_link in author_links:
				author_link.unwrap()

	# Remove the first <br> element within the <aside> with id="recent-posts-2"
	recent_posts_aside = soup.find('aside', id='recent-posts-2')
	if recent_posts_aside:
		first_br = recent_posts_aside.find('br')
		if first_br:
			first_br.decompose()
	
	# Remove <footer> tags with class "comment-meta" but keep their inner contents
	comment_meta_footers = soup.find_all('footer', class_='comment-meta')
	for footer in comment_meta_footers:
		footer.unwrap()

	# Remove <div> tags with both classes "comment-author" and "vcard" but keep their inner contents
	comment_author_vcard_divs = soup.find_all('div', class_=['comment-author', 'vcard'])
	for div in comment_author_vcard_divs:
		div.unwrap()

	# Remove all <img> tags with classes whose names begin with "wp-image-"
	for img in soup.find_all('img'):
		if any(cls.startswith('wp-image-') for cls in img.get('class', [])):
			img.decompose()

	# Replace <header> tag with id="masthead" with ascii art version
	masthead = soup.find('header', id='masthead')
	if masthead:
		ascii_art = r"""
<pre>
   __ __         __            ___           
  / // /__ _____/ /__  ___ _  / _ \___ ___ __
 / _  / _ `/ __/  '_/ / _ `/ / // / _ `/ // /
/_//_/\_,_/\__/_/\_\  \_,_/ /____/\_,_/\_, / 
fresh hacks every day                 /___/
<br>
</pre>
"""
		new_header = BeautifulSoup(ascii_art, 'html.parser')
		masthead.replace_with(new_header)

	# Add <br> after each comment
	add_br_after_comments(soup)

	# Convert problem characters
	updated_html = str(soup)
	content = transcode_html(updated_html, "html5", False)
	return content

def handle_get(req):
	url = f"https://hackaday.com{req.path}"
	try:
		response = requests.get(url)
		processed_content = process_html(response.text)
		return processed_content, response.status_code
	except Exception as e:
		return f"Error: {str(e)}", 500

def handle_post(req):
	if req.path == '/search':
		search_term = req.form.get('search_term')
		if search_term:
			search_url = f"https://hackaday.com/blog/?s={search_term.replace(' ', '+')}"
			try:
				response = requests.get(search_url)
				processed_content = process_html(response.text)
				return processed_content, response.status_code
			except Exception as e:
				return f"Error: {str(e)}", 500
	return "POST method not supported", 405

def handle_request(req):
	if req.method == 'POST':
		return handle_post(req)
	elif req.method == 'GET':
		return handle_get(req)
	else:
		return "Not Found", 404

def add_br_after_comments(soup):
	def process_ol(ol):
		children = ol.find_all('li', recursive=False)
		for index, li in enumerate(children):
			inner_ol = li.find('ol', recursive=False)
			if inner_ol:
				# Add <br> before the inner ol
				inner_ol.insert_before(soup.new_tag('br'))
				process_ol(inner_ol)
			else:
				# Add <br> after the current li unless it is the last li
				if index != len(children) - 1:
					li.insert_after(soup.new_tag('br'))
	
	comment_lists = soup.find_all('ol', class_='comment-list')
	for comment_list in comment_lists:
		process_ol(comment_list)
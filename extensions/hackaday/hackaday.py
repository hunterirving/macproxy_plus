from flask import request, redirect
import requests
from bs4 import BeautifulSoup
from html_utils import transcode_html

DOMAIN = "hackaday.com"

def handle_get(req):
	url = f"https://hackaday.com{req.path}"
	try:
		response = requests.get(url)

		# Parse the HTML and remove specific tags
		soup = BeautifulSoup(response.text, 'html.parser')
		
		# Remove divs with id="secondary"
		'''secondary_div = soup.find('div', id='secondary')
		if secondary_div:
			print("Removing div with id 'secondary'!!")
			secondary_div.decompose()'''

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

		# Process comments to add <br> after each comment
		comments_div = soup.find('div', id='comments')
		if comments_div:
			comments_list = comments_div.find('ol', class_='comment-list')
			if comments_list:
				for comment_article in comments_list.find_all('article'):
					comment_article.insert_after(soup.new_tag('br'))

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

		# Remove specific <p> tags within the div with id="comments" based on text content
		if comments_div:
			for p in comments_div.find_all('p'):
				if 'Please be kind and respectful' in p.get_text() or 'This site uses Akismet' in p.get_text():
					p.decompose()

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
			#print(sidebar_widget_wrapper)
			print("removing sidebar-widget-wrapper!!")
			sidebar_widget_wrapper.decompose()
		
		sidebar_widget_wrapper = soup.find('div', class_='sidebar-widget-wrapper')
		if sidebar_widget_wrapper:
			#print(sidebar_widget_wrapper)
			print("removing sidebar-widget-wrapper!!")
			sidebar_widget_wrapper.decompose()

		# Remove the <div> with id="secondary-bottom-ad"
		secondary_bottom_ad_div = soup.find('div', id='secondary-bottom-ad')
		if secondary_bottom_ad_div:
			secondary_bottom_ad_div.decompose()

		# Add a div with copyright information at the very bottom of the <body> tag
		body_tag = soup.find('body')
		if body_tag:
			copyright_div = soup.new_tag('div')
			copyright_div.string = "Copyright © 2024 | Hackaday, Hack A Day, and the Skull and Wrenches Logo are Trademarks of Hackaday.com"
			center_tag = soup.new_tag('center')
			center_tag.append(copyright_div)
			body_tag.append(center_tag)

		# Replace <header> tag with id="masthead"
		masthead = soup.find('header', id='masthead')
		if masthead:
			ascii_art = """
<pre>
   __ __         __            ___           
  / // /__ _____/ /__  ___ _  / _ \___ ___ __
 / _  / _ `/ __/  '_/ / _ `/ / // / _ `/ // /
/_//_/\_,_/\__/_/\_\  \_,_/ /____/\_,_/\_, / 
retro edition                         /___/ 
</pre>
"""
			new_header = BeautifulSoup(ascii_art, 'html.parser')
			masthead.replace_with(new_header)

		# Ensure changes are reflected
		updated_html = str(soup)
		content = transcode_html(updated_html, "html5", False)
		return content, response.status_code
	except Exception as e:
		return f"Error: {str(e)}", 500

def handle_post(req):
	return "POST method not supported", 405

def handle_request(req):
	if req.host == "hackaday.com":
		return handle_get(req)
	else:
		return "Not Found", 404
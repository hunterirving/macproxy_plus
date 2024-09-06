# HINT: MacWeb 2.0 doesn't seem to have CSS support. To work around this, set <h5> styling to font="Palatino" and <h6> styling to font="Times", both with Size="As Is"

from flask import request
import requests
from bs4 import BeautifulSoup, Comment
import urllib.parse
import re

DOMAIN = "wikipedia.org"

def create_search_form():
	return '''
	<br>
	<center>
		<h6><font size="7" face="Times"><b>WIKIPEDIA</b></font><br>The Free Encyclopedia</h6>
		<form action="/wiki/" method="get">
			<input size="35" type="text" name="search" required>
			<input type="submit" value="Search">
		</form>
	</center>
	'''

def get_featured_article_snippet():
	try:
		response = requests.get("https://en.wikipedia.org/wiki/Main_Page")
		response.raise_for_status()
		soup = BeautifulSoup(response.text, 'html.parser')
		tfa_div = soup.find('div', id='mp-tfa')
		if tfa_div:
			first_p = tfa_div.find('p')
			if first_p:
				return f'<br><br><b>From today\'s featured article:</b>{str(first_p)}'
	except Exception as e:
		print(f"Error fetching featured article: {str(e)}")
	return ''

def process_html(content, title):
	return f'<html><head><title>{title.replace("_", " ")}</title></head><body>{content}</body></html>'

def handle_request(req):
	if req.method == 'GET':
		path = req.path.lstrip('/')
		
		if not path or path == 'wiki/':
			search_query = req.args.get('search', '')
			if not search_query:
				content = create_search_form() + get_featured_article_snippet()
				return process_html(content, "Wikipedia"), 200
			
			# Redirect to /wiki/[SEARCH_TERM]
			return handle_wiki_page(search_query)

		if path.startswith('wiki/'):
			page_title = urllib.parse.unquote(path.replace('wiki/', ''))
			return handle_wiki_page(page_title)

	return "Method not allowed", 405

def handle_wiki_page(title):
	# First, try to search using the Wikipedia API
	search_url = f"https://{DOMAIN}/w/api.php"
	params = {
		"action": "query",
		"format": "json",
		"list": "search",
		"srsearch": title,
		"srprop": "",
		"utf8": 1
	}
	
	try:
		search_response = requests.get(search_url, params=params)
		search_response.raise_for_status()
		search_data = search_response.json()

		if search_data["query"]["search"]:
			# Get the title of the first search result
			found_title = search_data["query"]["search"][0]["title"]
			
			# Now fetch the page using the found title
			url = f"https://{DOMAIN}/wiki/{urllib.parse.quote(found_title)}"
			response = requests.get(url)
			response.raise_for_status()

			soup = BeautifulSoup(response.text, 'html.parser')

			# Extract the page title
			title_element = soup.select_one('span.mw-page-title-main')
			if title_element:
				page_title = title_element.text
			else:
				page_title = found_title.replace('_', ' ')

			# Create the table with title and search form
			search_form = f'''
			<form action="/wiki/" method="get">
				<input size="20" type="text" name="search" required>
				<input type="submit" value="Go">
			</form>
			'''
			header_table = f'''
			<table width="100%" cellspacing="0" cellpadding="0">
				<tr>
					<td valign="bottom"><h5><b><font size="5" face="Times">{page_title}</font></b></h5></td>
					<td align="right" valign="middle">
						<form action="/wiki/" method="get">
							<input size="20" type="text" name="search" required>
							<input type="submit" value="Go">
						</form>
					</td>
				</tr>
			</table>
			<hr>
			'''

			# Extract the main content
			content_div = soup.select_one('div#mw-content-text')
			if content_div:
				# Remove infoboxes and figures
				for element in content_div.select('table.infobox, figure'):
					element.decompose()

				# Remove shortdescription divs
				for element in content_div.select('div.shortdescription'):
					element.decompose()

				# Remove ambox tables
				for element in content_div.select('table.ambox'):
					element.decompose()
				
				# Remove style tags
				for element in content_div.select('style'):
					element.decompose()

				# Remove script tags
				for element in content_div.select('script'):
					element.decompose()
				
				# Remove edit section links
				for element in content_div.select('span.mw-editsection'):
					element.decompose()

				# Remove specific sections (External links, References, Notes)
				for section_id in ['External_links', 'References', 'Notes', 'Further_reading', 'Bibliography', 'Timeline']:
					heading = content_div.find(['h2', 'h3'], id=section_id)
					if heading:
						parent_div = heading.find_parent('div', class_='mw-heading')
						if parent_div:
							parent_div.decompose()

				# Convert <h2> to <b> and insert <hr> after, with <br><br> before
				for h2 in content_div.find_all('h2'):
					new_structure = soup.new_tag('div')
					
					br1 = soup.new_tag('br')
					br2 = soup.new_tag('br')
					b_tag = soup.new_tag('b')
					hr_tag = soup.new_tag('hr')
					
					b_tag.string = h2.get_text()
					
					new_structure.append(br1)
					new_structure.append(br2)
					new_structure.append(b_tag)
					new_structure.append(hr_tag)
					
					h2.replace_with(new_structure)

				# Unwrap <i> tags
				for i_tag in content_div.find_all('i'):
					i_tag.unwrap()

				# Decompose <sup> tags
				for sup_tag in content_div.find_all('sup'):
					sup_tag.decompose()

				# Remove div with id "catlinks" if it exists
				catlinks = content_div.find('div', id='catlinks')
				if catlinks:
					catlinks.decompose()

				# Remove divs with class "reflist"
				for div in content_div.find_all('div', class_='reflist'):
					div.decompose()
				
				# Remove divs with class "sistersitebox"
				for div in content_div.find_all('div', class_='sistersitebox'):
					div.decompose()

				# Remove divs with class "thumb"
				for div in content_div.find_all('div', class_='thumb'):
					div.decompose()

				# Remove HTML comments
				for comment in content_div.find_all(text=lambda text: isinstance(text, Comment)):
					comment.extract()

				# Remove divs with class "navbox"
				for navbox in content_div.find_all('div', class_='navbox'):
					navbox.decompose()
				
				# Remove divs with class "navbox-styles"
				for navbox in content_div.find_all('div', class_='navbox-styles'):
					navbox.decompose()

				# Remove divs with class "printfooter"
				for div in content_div.find_all('div', class_='printfooter'):
					div.decompose()
				
				# Remove divs with class "refbegin"
				for div in content_div.find_all('div', class_='refbegin'):
					div.decompose()

				# Remove divs with class "quotebox"
				for div in content_div.find_all('div', class_='quotebox'):
					div.decompose()

				#remove tables with class "sidebar"
				for table in soup.find_all('table', class_='sidebar'):
					table.decompose()
				
				#remove tables with class "wikitable"
				for table in soup.find_all('table', class_='wikitable'):
					table.decompose()
				
				#remove tables with class "wikitable"
				for table in soup.find_all('table', class_='mw-collapsible'):
					table.decompose()

				#remove ul with class "gallery"
				for ul in soup.find_all('ul', class_='gallery'):
					ul.decompose()

				# Remove <link> tags
				for link in content_div.find_all('link'):
					link.decompose()

				# Remove all noscript tags
				for noscript_tag in soup.find_all('noscript'):
					noscript_tag.decompose()

				# Remove all img tags
				for img_tag in soup.find_all('img'):
					img_tag.decompose()

				content = header_table + str(content_div)
			else:
				content = header_table + "<p>Content not found.</p>"

			return process_html(content, f"{page_title} - Wikipedia"), 200

		else:
			return process_html("<p>No results found.</p>", f"Search - Wikipedia"), 404

	except requests.RequestException as e:
		if hasattr(e, 'response') and e.response.status_code == 404:
			return process_html("<p>Page not found.</p>", f"Error - Wikipedia"), 404
		else:
			return process_html(f"<p>Error: {str(e)}</p>", "Error - Wikipedia"), 500

	except Exception as e:
		return process_html(f"<p>Error: {str(e)}</p>", "Error - Wikipedia"), 500
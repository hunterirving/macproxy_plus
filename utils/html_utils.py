
from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter
import re
import html
from config import WHITELISTED_DOMAINS, SIMPLIFY_HTML, TAGS_TO_STRIP, ATTRIBUTES_TO_STRIP, CONVERT_CHARACTERS, CONVERSION_TABLE

class URLAwareHTMLFormatter(HTMLFormatter):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def escape(self, string):
		"""
		Escape special characters in the given string or list of strings.
		"""
		if isinstance(string, list):
			return [html.escape(str(item), quote=True) for item in string]
		elif string is None:
			return ''
		else:
			return html.escape(str(string), quote=True)

	def attributes(self, tag):
		for key, val in tag.attrs.items():
			if key in ['href', 'src']:  # Don't escape URL attributes
				yield key, val
			else:
				yield key, self.escape(val)

def transcode_content(content):
	"""
	Convert HTTPS to HTTP in CSS or JavaScript content
	"""
	if isinstance(content, bytes):
		content = content.decode('utf-8', errors='replace')
		
	# Simple pattern to match URLs in both CSS and JS
	patterns = [
		(r"""url\(['"]?(https://[^)'"]+)['"]?\)""", r"url(\1)"),  # CSS url()
		(r'"https://', '"http://'),  # Double-quoted URLs
		(r"'https://", "'http://"),  # Single-quoted URLs
		(r"https://", "http://"),    # Unquoted URLs
	]
	
	for pattern, replacement in patterns:
		content = re.sub(pattern, 
						lambda m: replacement.replace(r"\1", 
						m.group(1).replace("https://", "http://") if len(m.groups()) > 0 else ""),
						content)
	
	return content.encode('utf-8')

def transcode_html(html):
	"""
	Uses BeautifulSoup to transcode payloads of the text/html content type
	"""
	if isinstance(html, bytes):
		html = html.decode("utf-8", errors="replace")

	if CONVERT_CHARACTERS:
		for key, replacement in CONVERSION_TABLE.items():
			if isinstance(replacement, bytes):
				replacement = replacement.decode("utf-8")
			html = html.replace(key, replacement)

	soup = BeautifulSoup(html, "html.parser")
	
	# Convert all HTTPS resources to HTTP through our proxy
	for tag in soup(['link', 'script', 'img', 'a', 'iframe']):
		# Handle src attributes
		if 'src' in tag.attrs:
			if tag['src'].startswith('https://'):
				tag['src'] = tag['src'].replace('https://', 'http://')
			elif tag['src'].startswith('//'):  # Handle protocol-relative URLs
				tag['src'] = 'http:' + tag['src']
				
		# Handle href attributes
		if 'href' in tag.attrs:
			if tag['href'].startswith('https://'):
				tag['href'] = tag['href'].replace('https://', 'http://')
			elif tag['href'].startswith('//'):  # Handle protocol-relative URLs
				tag['href'] = 'http:' + tag['href']

	if SIMPLIFY_HTML:
		for tag in soup(TAGS_TO_STRIP):
			tag.decompose()
		for tag in soup():
			for attr in ATTRIBUTES_TO_STRIP:
				if attr in tag.attrs:
					del tag[attr]

	# Remove any meta refresh tags that might use HTTPS
	for tag in soup.find_all('meta', attrs={'http-equiv': 'refresh'}):
		if 'content' in tag.attrs and 'https://' in tag['content']:
			tag['content'] = tag['content'].replace('https://', 'http://')

	# Handle CSS with inline URLs
	for tag in soup.find_all(['style', 'link']):
		if tag.string:
			tag.string = tag.string.replace('https://', 'http://')

	# Use the custom formatter when converting the soup back to a string
	html = soup.decode(formatter=URLAwareHTMLFormatter())

	html = html.replace('<br/>', '<br>')
	html = html.replace('<hr/>', '<hr>')
	
	# Ensure the output is properly encoded
	html_bytes = html.encode('utf-8')

	return html_bytes

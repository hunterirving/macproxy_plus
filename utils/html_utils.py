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
	
	if SIMPLIFY_HTML:
		for tag in soup(TAGS_TO_STRIP):
			tag.decompose()
		for tag in soup():
			for attr in ATTRIBUTES_TO_STRIP:
				if attr in tag.attrs:
					del tag[attr]
	for tag in soup(["base", "a"]):
		if "href" in tag.attrs:
			tag["href"] = tag["href"].replace("https://", "http://")
	for tag in soup("img"):
		if "src" in tag.attrs:
			tag["src"] = tag["src"].replace("https://", "http://")

	# Use the custom formatter when converting the soup back to a string
	html = soup.decode(formatter=URLAwareHTMLFormatter())

	html = html.replace('<br/>', '<br>')
	html = html.replace('<hr/>', '<hr>')
	
	# Ensure the output is properly encoded
	html_bytes = html.encode('utf-8')

	return html_bytes
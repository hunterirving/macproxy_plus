from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter
import re
import html

CONVERSION_TABLE = {
	"¢": b"cent",
	"&cent;": b"cent",
	"€": b"EUR",
	"&euro;": b"EUR",
	"&yen;": b"YEN",
	"&pound;": b"GBP",
	"«": b"'",
	"&laquo;": b"'",
	"»": b"'",
	"&raquo;": b"'",
	"‘": b"'",
	"&lsquo;": b"'",
	"’": b"'",
	"&rsquo;": b"'",
	"“": b"''",
	"&ldquo;": b"''",
	"”": b"''",
	"&rdquo;": b"''",
	"–": b"-",
	"&ndash;": b"-",
	"—": b"--",
	"&mdash;": b"--",
	"―": b"-",
	"&horbar;": b"-",
	"·": b"-",
	"&middot;": b"-",
	"‚": b",",
	"&sbquo;": b",",
	"„": b",,",
	"&bdquo;": b",,",
	"†": b"*",
	"&dagger;": b"*",
	"‡": b"**",
	"&Dagger;": b"**",
	"•": b"-",
	"&bull;": b"*",
	"…": b"...",
	"&hellip;": b"...",
	"\u00A0": b" ",
	"&nbsp;": b" ",
	"±": b"+/-",
	"&plusmn;": b"+/-",
	"≈": b"~",
	"&asymp;": b"~",
	"≠": b"!=",
	"&ne;": b"!=",
	"&times;": b"x",
	"⁄": b"/",
	"°": b"*",
	"&deg;": b"*",
	"′": b"'",
	"&prime;": b"'",
	"″": b"''",
	"&Prime;": b"''",
	"™": b"(tm)",
	"&trade;": b"(TM)",
	"&reg;": b"(R)",
	"®": b"(R)",
	"&copy;": b"(c)",
	"©": b"(c)",
	"é": b"e",
	"ø": b"o",
	"Å": b"A",
	"â": b"a",
	"Æ": b"AE",
	"æ": b"ae",
	"á": b"a",
	"ō": b"o",
	"ó": b"o",
	"ū": b"u",
	"⟨": b"<",
	"⟩": b">",
	"←": b"<",
	"&larr;": b"<",
	"→": b">",
	"&rarr;": b">",
	"↑": b"^",
	"&uarr;": b"^",
	"↓": b"v",
	"&darr;": b"v",
	"↖": b"\\",
	"&nwarr;": b"\\",
	"↗": b"/",
	"&nearr;": b"/",
	"↘": b"\\",
	"&searr;": b"\\",
	"↙": b"/",
	"&swarr;": b"/",
	"─": b"-",
	"&boxh;": b"-",
	"│": b"|",
	"&boxv;": b"|",
	"┌": b"+",
	"&boxdr;": b"+",
	"┐": b"+",
	"&boxdl;": b"+",
	"└": b"+",
	"&boxur;": b"+",
	"┘": b"+",
	"&boxul;": b"+",
	"├": b"+",
	"&boxvr;": b"+",
	"┤": b"+",
	"&boxvl;": b"+",
	"┬": b"+",
	"&boxhd;": b"+",
	"┴": b"+",
	"&boxhu;": b"+",
	"┼": b"+",
	"&boxvh;": b"+",
	"█": b"#",
	"&block;": b"#",
	"▌": b"|",
	"&lhblk;": b"|",
	"▐": b"|",
	"&rhblk;": b"|",
	"▀": b"-",
	"&uhblk;": b"-",
	"▄": b"_",
	"&lhblk;": b"_",
	"▾": b"v",
	"&dtrif;": b"v",
	"&#x25BE;": b"v",
	"&#9662;": b"v",
	"♫": b"",
	"&spades;": b"",
	"\u200B": b"",
	"&ZeroWidthSpace;": b"",
	"\u200C": b"",
	"\u200D": b"",
	"\uFEFF": b"",
}

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

def transcode_html(html, disable_char_conversion):
	"""
	Uses BeautifulSoup to transcode payloads of the text/html content type
	"""
	if isinstance(html, bytes):
		html = html.decode("utf-8", errors="replace")

	if not disable_char_conversion:
		for key, replacement in CONVERSION_TABLE.items():
			if isinstance(replacement, bytes):
				replacement = replacement.decode("utf-8")
			html = html.replace(key, replacement)

	soup = BeautifulSoup(html, "html.parser")
	
	# Remove all class attributes to make pages load faster
	for tag in soup.find_all(class_=True):
		del tag['class']
	
	for tag in soup(["script", "link", "style", "source", "picture"]):
		tag.decompose()
	for tag in soup():
		for attr in ["style", "onclick"]:
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
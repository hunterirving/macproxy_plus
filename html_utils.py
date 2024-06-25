from bs4 import BeautifulSoup
import re

CONVERSION_TABLE = {
	# Currency symbols
	"¢": b"cent",
	"&cent;": b"cent",
	"€": b"EUR",
	"&euro;": b"EUR",

	# Quotes and dashes
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

	# Punctuation and special characters
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

	# Math symbols
	"±": b"+/-",
	"&plusmn;": b"+/-",
	"≈": b"~",
	"&asymp;": b"~",
	"≠": b"!=",
	"&ne;": b"!=",

	# Miscellaneous symbols
	"°": b"*",
	"&deg;": b"*",
	"′": b"'",
	"&prime;": b"'",
	"″": b"''",
	"&Prime;": b"''",
	"™": b"(tm)",
	"&trade;": b"(tm)",

	# Arrows
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

	# Box-drawing characters
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


	# Block elements
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

	# Downward triangle
	"▾": b"v",
	"&dtrif;": b"v",
	"&#x25BE;": b"v",
	"&#9662;": b"v",

	# Musical note
	"♫": b"",
	"&spades;": b""
}

def transcode_html(html, html_formatter, disable_char_conversion):
	"""
	Uses BeautifulSoup to transcode payloads of the text/html content type
	"""
	# Ensure html is in bytes
	if isinstance(html, str):
		html = html.encode("utf-8")

	if not disable_char_conversion:
		# Replace characters and entities based on the conversion table
		for key, replacement in CONVERSION_TABLE.items():
			html = html.replace(key.encode("utf-8"), replacement)

	soup = BeautifulSoup(html, "html.parser")
	for tag in soup(["script", "link", "style", "source", "picture"]):
		tag.decompose()
	for tag in soup():
		for attr in ["style", "onclick"]:
			if attr in tag.attrs:
				del tag[attr]
	for tag in soup("base"):
		tag["href"] = tag["href"].replace("https://", "http://")
	for tag in soup.findAll("a", href=True):
		tag["href"] = tag["href"].replace("https://", "http://")
	for tag in soup("img"):
		try:
			tag["src"] = tag["src"].replace("https://", "http://")
		except:
			print("Malformed img tag: " + str(tag))

	# Prettify the HTML
	html = soup.prettify(formatter=html_formatter).encode("utf-8")

	# Convert to string for manipulation
	html_str = html.decode('utf-8')

	# Strip whitespace from inner text of <a> tags
	html_str = re.sub(r'(<a [^>]*>)(\s+)([^<]*)(\s+)(</a>)', lambda match: f'{match.group(1)}{match.group(3).strip()}{match.group(5)}', html_str)

	# Convert back to bytes
	html = html_str.encode('utf-8')

	if not disable_char_conversion:
		# Replace characters and entities based on the conversion table
		for key, replacement in CONVERSION_TABLE.items():
			html = html.replace(key.encode("utf-8"), replacement)

	return html.decode("utf-8")

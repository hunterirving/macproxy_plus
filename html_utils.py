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
	"\u00A0": b" ",
	"&nbsp;": b" ",

	# Math symbols
	"±": b"+/-",
	"&plusmn;": b"+/-",
	"≈": b"~",
	"&asymp;": b"~",
	"≠": b"!=",
	"&ne;": b"!=",
	"&times;": b"x",
	"⁄": b"/",

	# Miscellaneous symbols
	"°": b"*",
	"&deg;": b"*",
	"′": b"'",
	"&prime;": b"'",
	"″": b"''",
	"&Prime;": b"''",
	"™": b"(tm)",
	"&trade;": b"(tm)",
	"é": b"e",
	"ø": b"o",
	"Å": b"A",
	"â": b"a",
	"Æ": b"AE",
	"æ": b"ae",
	"⟨": b"<",
	"⟩": b">",

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
	"♫": b"~",
	"&spades;": b""
}

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

	html = str(soup)
	html = html.replace('<br/>', '<br>')
	html = html.replace('<hr/>', '<hr>')
	
	# Ensure the output is properly encoded
	html_bytes = html.encode('utf-8')

	return html_bytes
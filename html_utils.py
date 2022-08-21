"""
HTML transcoding helper methods for Macproxy
"""

from bs4 import BeautifulSoup

# Conversion table based on https://www.w3.org/wiki/Common_HTML_entities_used_for_typography
UNICODE_CHAR_CONVERSION_TABLE = {
        "¢": b"cent",
        "«": b"'",
        "»": b"'",
        "°": b"*",
        "±": b"+/-",
        "–": b"-",   # En dash
        "—": b"--",  # Em dash
        "‘": b"'",
        "’": b"'",
        "·": b".",
        "½": b"1/2",
        "¼": b"1/4",
        "¾": b"3/4",
        "‚": b",",
        "“": b"``",
        "”": b"``",
        "„": b",,",
        "†": b"*",
        "‡": b"**",
        "•": b"*",
        "…": b"...",
        "′": b"'",
        "″": b"''",
        "€": b"EUR",
        "™": b"(tm)",
        "≈": b"~",
        "≠": b"!=",
}
 
def transcode_html(html, html_formatter, disable_char_conversion):
    """
    Uses BeautifulSoup to transcode payloads of the text/html content type
    """
    if not disable_char_conversion:
        for char in UNICODE_CHAR_CONVERSION_TABLE.keys():
            html = html.replace(char.encode("utf-8"), UNICODE_CHAR_CONVERSION_TABLE[char])
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "link", "style", "source", "picture"]):
        tag.decompose()
    for tag in soup():
        for attr in ["style", "onclick"]:
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
    return soup.prettify(formatter=html_formatter)

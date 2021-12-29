"""
HTML transcoding helper methods for Macproxy
"""

from bs4 import BeautifulSoup
 
def transcode_html(html):
    """
    Uses BeatifulSoup to transcode payloads with the text/html content type
    """
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
    return soup.prettify(formatter="html5")

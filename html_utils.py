from bs4 import BeautifulSoup
 
def transcode_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    for tag in soup('base'):
        tag['href'] = tag['href'].replace("https://", "http://")
    for tag in soup.findAll('a', href=True):
        tag['href'] = tag['href'].replace("https://", "http://")
    for tag in soup('img'):
        try:
            tag['src'] = tag['src'].replace("https://", "http://")
        except:
            pass
    for tag in soup(['script', 'link', 'style', 'noscript']):
        tag.extract()
    for tag in soup():
        for attr in ['style', 'onclick']:
            del tag[attr]
    return str(soup)

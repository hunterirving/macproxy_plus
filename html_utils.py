from bs4 import BeautifulSoup
 
def transcode_html(html):
    soup = BeautifulSoup(html, features="html.parser")
    for tag in soup('base'):
        tag['href'] = tag['href'].replace("https://", "http://")
    for tag in soup.findAll('a', href=True):
        tag['href'] = tag['href'].replace("https://", "http://")
    for tag in soup('img'):
        tag['src'] = tag['src'].replace("https://", "http://")
    for tag in soup(['script', 'link', 'style', 'noscript']):
        tag.extract()
    for tag in soup():
        for attr in ['style', 'onclick']:
            del tag[attr]
    return str(soup)

if __name__ == '__main__':
    import requests
    html = requests.get('http://stackoverflow.com/questions/5598524/can-i-remove-script-tags-with-beautifulsoup').content
    html = macify(html)
    with open('macified.html', 'w') as fd:
        fd.write(html)


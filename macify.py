from bs4 import BeautifulSoup
 
def macify(html):
    soup = BeautifulSoup(html)
    for tag in soup(['script', 'link', 'style', 'noscript']):
        tag.extract()
    for tag in soup(['div', 'span']):
        tag.replaceWithChildren()
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


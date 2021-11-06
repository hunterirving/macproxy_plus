from macify import macify
import requests
from flask import request, Flask

app = Flask(__name__)
session = requests.Session()

@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def get(path):
    url = request.url.replace('https://', 'http://', 1)
    resp = session.get(url, params=request.args)
    if resp.headers['Content-Type'].startswith("text/html"):
        return macify(resp.content), resp.status_code
    return resp.content, resp.status_code

@app.route('/', defaults={'path': ''}, methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def post(path):
    url = request.url.replace('https://', 'http://', 1)
    resp = session.post(url, data=request.form, allow_redirects=True)
    if resp.headers['Content-Type'].startswith("text/html"):
        return macify(resp.content), resp.status_code
    return resp.content, resp.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

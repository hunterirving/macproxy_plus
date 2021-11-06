from macify import macify
import requests
from flask import Flask, request, session, g

app = Flask(__name__)
session = requests.Session()

@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def get(path):
    url = request.url.replace('https://', 'http://', 1)
    resp = session.get(url, params=request.args)
    g.contenttype = resp.headers['Content-Type']
    if resp.headers['Content-Type'].startswith("text/html"):
        return macify(resp.content), resp.status_code
    return resp.content, resp.status_code

@app.route('/', defaults={'path': ''}, methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def post(path):
    url = request.url.replace('https://', 'http://', 1)
    resp = session.post(url, data=request.form, allow_redirects=True)
    g.contenttype = resp.headers['Content-Type']
    if resp.headers['Content-Type'].startswith("text/html"):
        return macify(resp.content), resp.status_code
    return resp.content, resp.status_code

@app.after_request
def apply_caching(resp):
    # Workaround for retaining the Content-Type header for f.e. downloading binary files.
    # There may be a more elegant way to do this.
    resp.headers['Content-Type'] = g.contenttype
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

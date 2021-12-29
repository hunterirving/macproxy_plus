"""
Macproxy -- A simple HTTP proxy for vintage web browsers
"""

import requests
from sys import argv
from flask import Flask, request, session, g
from html_utils import transcode_html

app = Flask(__name__)
session = requests.Session()

@app.route("/", defaults={"path": ""}, methods=["GET"])
@app.route("/<path:path>", methods=["GET"])
def get(path):
"""
Builds the request for the HTTP GET method
"""
    url = request.url.replace("https://", "http://", 1)
    headers = {
        "Accept": request.headers.get("Accept"),
        "Accept-Encoding": request.headers.get("Accept-Encoding"),
        "Accept-Language": request.headers.get("Accept-Language"),
        "Connection": request.headers.get("Connection"),
        "Referer": request.headers.get("Referer"),
        "User-Agent": request.headers.get("User-Agent"),
    }
    resp = session.get(url, params=request.args, headers=headers)
    try:
        g.content_type = resp.headers["Content-Type"]
    except:
        print("No Content-Type header present")
    if resp.headers["Content-Type"].startswith("text/html"):
        return transcode_html(resp.content), resp.status_code
    return resp.content, resp.status_code

@app.route("/", defaults={"path": ""}, methods=["POST"])
@app.route("/<path:path>", methods=["POST"])
def post(path):
"""
Builds the request for the HTTP POST method
"""
    url = request.url.replace("https://", "http://", 1)
    headers = {
        "Accept": request.headers.get("Accept"),
        "Accept-Encoding": request.headers.get("Accept-Encoding"),
        "Accept-Language": request.headers.get("Accept-Language"),
        "Connection": request.headers.get("Connection"),
        "Referer": request.headers.get("Referer"),
        "User-Agent": request.headers.get("User-Agent"),
    }
    resp = session.post(url, data=request.form, headers=headers, allow_redirects=True)
    try:
        g.content_type = resp.headers["Content-Type"]
    except:
        print("No Content-Type header present")
    if resp.headers["Content-Type"].startswith("text/html"):
        return transcode_html(resp.content), resp.status_code
    return resp.content, resp.status_code

@app.after_request
def apply_caching(resp):
"""
Modifies the response after the request has been built
"""
    # Workaround for retaining the Content-Type header for f.e. downloading binary files.
    # There may be a more elegant way to do this.
    try:
        resp.headers["Content-Type"] = g.content_type
    except:
        pass
    return resp

if __name__ == "__main__":
    if len(argv) > 1:
        port = argv[1]
    else:
        port = 5000
    app.run(host="0.0.0.0", port=port)

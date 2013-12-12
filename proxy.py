from macify import macify
import requests
from flask import request, Flask

app = Flask(__name__)
session = requests.Session()

@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def get(path):
    resp = session.get(path, params=request.args)
    return macify(resp.content), resp.status_code

@app.route('/', defaults={'path': ''}, methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def post(path):
    resp = session.post(path, data=request.form, allow_redirects=True)
    return macify(resp.content), resp.status_code

if __name__ == '__main__':
    app.debug = True
    app.run()

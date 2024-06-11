import requests
from flask import redirect
from bs4 import BeautifulSoup

DOMAIN = "wiby.me"

def handle_get(request):
	if "surprise" in request.path:
		return handle_surprise(request)
	else:
		return proxy_request(request)

def handle_post(request):
	return proxy_request(request)

def handle_surprise(request):
	# Fetch the interstitial "you asked for it!" page
	url = "http://wiby.me/surprise"
	resp = requests.get(url, allow_redirects=True)  # Automatically follow redirects

	if resp.status_code == 200:
		soup = BeautifulSoup(resp.content, 'html.parser')
		meta_tag = soup.find("meta", attrs={"http-equiv": "refresh"})

		if meta_tag:
			content = meta_tag.get("content", "")
			parts = content.split("URL=")
			if len(parts) > 1:
				redirect_url = parts[1].strip("'\"")
				return redirect(redirect_url, code=302)

	# If the meta tag isn't found, or some other issue occurs, just return the content of the page
	return resp.content, resp.status_code

def proxy_request(request):
	url = request.url.replace("https://", "http://", 1)
	headers = {
		"Accept": request.headers.get("Accept"),
		"Accept-Language": request.headers.get("Accept-Language"),
		"Referer": request.headers.get("Referer"),
		"User-Agent": request.headers.get("User-Agent"),
	}

	resp = requests.get(url, headers=headers)
	return resp.content, resp.status_code

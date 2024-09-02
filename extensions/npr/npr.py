from flask import request, redirect
import requests
from bs4 import BeautifulSoup

DOMAIN = "npr.org"

# Description:
# This extension handles requests to the NPR website (npr.org).
# It modifies URLs to ensure they are compatible with older browsers by converting them to absolute URLs.
# Additionally, it removes the <header> tag containing the "Text-Only Version" message and link to the full site.
# It redirects all requests from npr.org and text.npr.org to the proxy-modified npr.org while keeping the original domain in the address bar.

def handle_get(req):
	url = f"https://text.npr.org{req.path}"
	try:
		response = requests.get(url)

		# Parse the HTML and remove the <header> tag
		soup = BeautifulSoup(response.text, 'html.parser')
		header_tag = soup.find('header')
		if header_tag:
			header_tag.decompose()
		
		# Modify relative URLs to absolute URLs
		for tag in soup.find_all(['a', 'img']):
			if tag.has_attr('href'):
				tag['href'] = f"/{tag['href'].lstrip('/')}"
			if tag.has_attr('src'):
				tag['src'] = f"/{tag['src'].lstrip('/')}"

		return str(soup), response.status_code
	except Exception as e:
		return f"Error: {str(e)}", 500

def handle_post(req):
	return "POST method not supported", 405

def handle_request(req):
	if req.host == "text.npr.org":
		return redirect(f"http://npr.org{req.path}")
	else:
		return handle_get(req)
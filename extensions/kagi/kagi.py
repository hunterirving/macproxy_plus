from flask import render_template_string
import requests
from bs4 import BeautifulSoup
import config
from utils.image_utils import is_image_url
import os
import math
from urllib.parse import urlencode

DOMAIN = "kagi.com"
OUTPUT_ENCODING = "macintosh" # change to utf-8 for modern machines

# Description:
# This extension handles requests to the Kagi search engine (kagi.com)
# It adds a token Kagi uses to authenticate private browser requests to
# authenticate searches. Results are formatted in a custom template.

here = os.path.dirname(__file__)
template_path = os.path.join(here, "template.html")
with open(template_path,"r") as f:
	HTML_TEMPLATE = f.read()

def handle_request(req):
	if is_image_url(req.path) or req.path.startswith('/proxy'):
		return handle_image_request(req)

	url = f"https://kagi.com{req.path}"
	if not req.path.startswith('/html'):
		url = f"https://kagi.com/html{req.path}"

	args = {
		'token': config.KAGI_SESSION_TOKEN
	}

	for key, value in req.args.items():
		args[key] = value

	try:
		response = requests.request(req.method, url, params=args)
		response.encoding = response.apparent_encoding

		soup = BeautifulSoup(response.text, 'html.parser')

		query = req.args.get('q', '')
		title = f"{query} - Kagi Search" if len(query) > 0 else "Kagi Search"

		num_results = soup.select_one('.num_results')
		num_results = num_results.get_text().strip() if num_results else None

		nav_items = parse_nav_items(soup, query)
		lenses = parse_lenses(soup)
		results = parse_web_results(soup) + parse_news_results(soup)
		images = parse_image_results(soup)
		videos = parse_video_results(soup)

		load_more = soup.select_one('#load_more_results')
		load_more = load_more['href'] if load_more else None

		content = render_template_string(HTML_TEMPLATE,
			title=title,
			query=query,
			nav_items=nav_items,
			lenses=lenses,
			num_results=num_results,
			results=results,
			image_results=images,
			video_results=videos,
			load_more=load_more)

		return content.encode(OUTPUT_ENCODING, errors='xmlcharrefreplace'), 200

	except Exception as e:
		return f"Error: {str(e)}", 500

def parse_nav_items(soup, query):
	nav_items = []
	for el in soup.select('.nav_item._0_query_link_item'):
		item = {
			'title': el.string.strip(),
			'url': '',
			'active': '--active' in el['class']
		}
		if el.get('href'):
			item['url'] = el['href']
		elif el.get('formaction'):
			item['url'] = f"{el['formaction']}?{urlencode({'q': query})}"
		nav_items.append(item)
	return nav_items

def parse_lenses(soup):
	lenses = []
	for el in soup.select('._0_lenses .list_items a'):
		if not 'edit_lense_btn' in el['class']:
			lens = {
				'title': el.get_text().strip(),
				'url': el['href'],
				'active': '--active' in el['class']
			}
			lenses.append(lens)
	return lenses

def parse_web_results(soup):
	results = []
	for el in soup.select('.search-result'):
		a = el.select_one('.__sri_title_link')
		if a:
			result = {
				'title': a.string.strip(),
				'url': a['href'],
				'desc': '',
				'time': ''
			}
			desc = el.select_one('.__sri-body .__sri-desc')
			if desc:
				time = desc.select_one('.__sri-time')
				if time:
					result['time'] = time.get_text().strip()
					time.decompose()
				result['desc'] = desc.get_text().strip()
			results.append(result)
	return results

def parse_image_results(soup):
	row_height = 100
	row_width = 0
	max_width = 500
	results = []
	row = []
	for el in soup.select('.results-box .item'):
		a = el.select_one('a._0_img_link_el')
		img = el.select_one('img._0_img_src')
		width = int(img['width']) if img['width'] else 100
		height = int(img['height']) if img['height'] else 100
		item_width = math.floor(width*row_height/height)
		result = {
			'title': img['alt'],
			'url': f"http://kagi.com{a['href']}",
			'src': f"http://kagi.com{img['src']}",
			'width': item_width,
			'height': row_height
		}
		if row_width + item_width > max_width:
			if len(row) > 0:
				results.append(row)
			row_width = 0
			row = []
		row_width = row_width + item_width
		row.append(result)
	if len(row) > 0:
		results.append(row)
	return results

def parse_video_results(soup):
	results = []
	for el in soup.select('.videoResultItem'):
		a = el.select_one('.videoResultTitle')
		img = el.select_one('.videoResultThumbnail img')
		desc = el.select_one('.videoResultDesc')
		time = el.select_one('.videoResultVideoTime')

		result = {
			'title': a.get_text().strip(),
			'url': a['href'],
			'src': f"http://kagi.com{img['src']}",
			'desc': desc.get_text().strip(),
			'time': time.get_text().strip() if time else None
		}
		results.append(result)
	return results

def parse_news_results(soup):
	results = []
	for el in soup.select('.newsResultItem'):
		a = el.select_one('.newsResultTitle a')
		if a:
			result = {
				'title': a.string.strip(),
				'url': a['href'],
				'desc': '',
				'time': ''
			}
			desc = el.select_one('.newsResultContent')
			if desc:
				result['desc'] = desc.get_text().strip()
			time = el.select_one('.newsResultTime')
			if time:
				result['time'] = time.get_text().strip()
			results.append(result)
	return results

def handle_image_request(req):
	try:
		response = requests.get(req.url, params=req.args)
		return response.content, response.status_code, response.headers
	except Exception as e:
		return f"Error: {str(e)}", 500

	cached_url = fetch_and_cache_image(req.url)
	if cached_url:
		return send_from_directory(CACHE_DIR, os.path.basename(cached_url), mimetype='image/gif')
	else:
		return abort(404, "Image not found or could not be processed")


# HINT: "NOT Youtube" is not associated with or endorsed by YouTube, and does not connect to or otherwise interact with YouTube in any way.

import os
import json
import random
import string
import subprocess
from flask import request, send_file, render_template_string
from urllib.parse import urlparse, parse_qs
import config

DOMAIN = "notyoutube.com"
EXTENSION_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE_PATH = os.path.join(EXTENSION_DIR, "videos.json")
FLIM_DIRECTORY = os.path.join(EXTENSION_DIR, "flims")
PREVIEW_DIRECTORY = os.path.join(EXTENSION_DIR, "previews")
PROFILE = "plus"

# Ensure directories exist
os.makedirs(FLIM_DIRECTORY, exist_ok=True)
os.makedirs(PREVIEW_DIRECTORY, exist_ok=True)

def generate_video_id():
	return ''.join(random.choices(string.ascii_letters + string.digits, k=11))

# Load recommended videos from JSON file
def load_recommended_videos():
	try:
		with open(JSON_FILE_PATH, 'r') as json_file:
			data = json.load(json_file)
			return data
	except FileNotFoundError:
		print(f"Error: {JSON_FILE_PATH} not found.")
		return []
	except json.JSONDecodeError:
		print(f"Error: Invalid JSON in {JSON_FILE_PATH}.")
		return []

RECOMMENDED_VIDEOS = load_recommended_videos()
VIDEO_ID_MAP = {generate_video_id(): video for video in RECOMMENDED_VIDEOS}

def generate_videos_html(videos, max_videos=6):
	videos = random.sample(videos, len(videos))
	videos = videos[:max_videos]
	
	html = '<table width="100%" cellpadding="5" cellspacing="0">'
	for i in range(0, len(videos), 2):
		html += '<tr>'
		for j in range(2):
			if i + j < len(videos):
				video = videos[i + j]
				video_id = next(id for id, v in VIDEO_ID_MAP.items() if v == video)
				url = f"https://www.{DOMAIN}/watch?v={video_id}"
				title = video.get('title', 'Untitled')
				creator = video.get('creator', 'Unknown creator')
				description = video.get('description', 'No description available')
				html += f'''
				<td width="60" valign="top"><img src="" width="50" height="40"></td>
				<td valign="top" width="50%">
					<b><a href="{url}">{title}</a></b>
					<br>
					<font size="2">
						<b>{creator}</b>
						<br>
						{description}
					</font>
				</td>
				'''
		html += '</tr>'
	html += '</table>'
	return html

def generate_homepage():
	videos_html = generate_videos_html(RECOMMENDED_VIDEOS, max_videos=6)
	return render_template_string('''
	<!DOCTYPE html>
	<html lang="en">
		<head>
			<meta charset="UTF-8">
			<title>NOT YouTube - Don't Broadcast Yourself</title>
		</head>
		<body>
			<center>
<pre>
                                                   
  ##      ##         ########     ##               
   ##    ##             ##        ##               
    ##  ## ####  ##  ## ## ##  ## #####   ####     
     #### ##  ## ##  ## ## ##  ## ##  ## ##  ##    
      ##  ##  ## ##  ## ## ##  ## ##  ## ######    
      ##  ##  ## ##  ## ## ##  ## ##  ## ##        
 not  ##   ####   ##### ##  ##### #####   #####    
<br>
</pre>
				<form method="get" action="/results">
					<input type="text" size="40" name="search_query" required style="font-size: 42px;">
					<input type="submit" value="Search">
				</form>
				<br>
			</center>
			<hr>
			{{ videos_html|safe }}
		</body>
	</html>
	''', videos_html=videos_html)

def generate_search_results(search_results, query):
	videos_html = generate_search_results_html(search_results)
	return render_template_string('''
	<!DOCTYPE html>
	<html lang="en">
		<head>
			<meta charset="UTF-8">
			<title>NOT YouTube - Search Results</title>
		</head>
		<body>
			<form method="get" action="/results">
				<input type="text" size="40" name="search_query" value="{{ query }}" required style="font-size: 16px;">
				<input type="submit" value="Search">
			</form>
			<hr>
			{{ videos_html|safe }}
		</body>
	</html>
	''', videos_html=videos_html, query=query)

def generate_search_results_html(videos):
	html = ''
	for video in videos:
		video_id = next(id for id, v in VIDEO_ID_MAP.items() if v == video)
		url = f"https://www.{DOMAIN}/watch?v={video_id}"
		title = video.get('title', 'Untitled')
		creator = video.get('creator', 'Unknown creator')
		description = video.get('description', '')

		# Handle description formatting
		if description:
			if len(description) > 200:
				formatted_description = f"{description[:200]}..."
			else:
				formatted_description = description
		else:
			formatted_description = "..."

		html += f'''
		<b><a href="{url}">{title}</a></b><br>
		<font size="2">
			<b>{creator}</b><br>
			{formatted_description}
		</font>
		<br><br>
		'''
	return html

def handle_video_request(video_id):
	video = VIDEO_ID_MAP.get(video_id)
	if not video:
		return "Video not found", 404

	input_path = video['path']
	flim_path = os.path.join(FLIM_DIRECTORY, f"{video_id}.flim")
	preview_path = os.path.join(PREVIEW_DIRECTORY, f"{video_id}.mp4")
	
	try:
		subprocess.run([
			"flimmaker",
			input_path,
			"--flim", flim_path,
			"--profile", PROFILE,
			"--mp4", preview_path,
			"--bars", "false"
		], check=True)
	except subprocess.CalledProcessError:
		return "Error generating video", 500

	if os.path.exists(flim_path):
		return send_file(flim_path, as_attachment=True, download_name=f"{video_id}.flim")
	else:
		return "Error: File not generated", 500

def search_videos(query):
	query = query.lower()
	search_results = []
	
	for video in RECOMMENDED_VIDEOS:
		title = video.get('title', '').lower()
		description = video.get('description', '').lower()
		
		if query in title or query in description:
			search_results.append(video)
	
	return search_results

def handle_request(req):
	parsed_url = urlparse(req.url)
	path = parsed_url.path
	query_params = parse_qs(parsed_url.query)

	if path == "/watch" and 'v' in query_params:
		video_id = query_params['v'][0]
		return handle_video_request(video_id)
	elif path == "/results" and 'search_query' in query_params:
		query = query_params['search_query'][0]
		search_results = search_videos(query)
		return generate_search_results(search_results, query), 200
	else:
		return generate_homepage(), 200
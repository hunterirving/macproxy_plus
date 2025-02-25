from flask import request, render_template_string
from google import genai
from google.genai import types
import config

# Initialize the Google API Client with your API key
client = genai.Client(api_key=config.GEMINI_API_KEY)

DOMAIN = "gemini.google.com"

messages = []
selected_model = "gemini-2.0-flash"
previous_model = selected_model

system_prompt = """Please provide your response in plain text using only ASCII characters. 
Never use any special or esoteric characters that might not be supported by older systems.
Your responses will be presented to the user within the body of an html document. Be aware that any html tags you respond with will be interpreted and rendered as html. 
Therefore, when discussing an html tag, do not wrap it in <>, as it will be rendered as html. Instead, wrap the name of the tag in <b> tags to emphasize it."""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<title>Google Gemini</title>
</head>
<body>
	<form method="post" action="/">
		<select id="model" name="model">
			<option value="gemini-2.0-pro-exp-02-05" {{ 'selected' if selected_model == 'gemini-2.0-pro-exp-0205' else '' }}>Gemini 2.0 Pro Experimental 0205</option>
			<option value="gemini-2.0-flash-lite-preview-02-05" {{ 'selected' if selected_model == 'gemini-2.0-flash-lite-preview-0205' else '' }}>Gemini 2.0 Flash Lite Preview 0205</option>
			<option value="gemini-2.0-flash" {{ 'selected' if selected_model == 'gemini-2.0-flash' else '' }}>Gemini 2.0 Flash</option>
			<option value="gemini-2.0-flash-exp" {{ 'selected' if selected_model == 'gemini-2.0-flash-exp' else '' }}>Gemini 2.0 Flash Experimental</option>
			<option value="gemini-exp-1206" {{ 'selected' if selected_model == 'gemini-exp-1206' else '' }}>Gemini Experimental 1206</option>
			<option value="learnlm-1.5-pro-experimental" {{ 'selected' if selected_model == 'learnlm-1.5-pro-experimental' else '' }}>LearnLM 1.5 Pro Experimental</option>
			<option value="gemini-1.5-pro-latest" {{ 'selected' if selected_model == 'gemini-1.5-pro-latest' else '' }}>Gemini 1.5 Pro Latest</option>
			<option value="gemini-1.5-flash-latest" {{ 'selected' if selected_model == 'gemini-1.5-flash-latest' else '' }}>Gemini 1.5 Flash Latest</option>
			<option value="gemini-1.5-flash-8b" {{ 'selected' if selected_model == 'gemini-1.5-flash-8b' else '' }}>Gemini 1.5 Flash 8b</option>
		</select>
		<input type="text" size="63" name="command" required autocomplete="off">
		<input type="submit" value="Submit">
	</form>
	<div id="chat">
		<p>{{ output|safe }}</p>
	</div>
</body>
</html>
"""

def get_generation_config():
	return types.GenerateContentConfig(
		temperature=1,
		top_p=0.95,
		top_k=40,
		max_output_tokens=8192,
		system_instruction=system_prompt
	)

def handle_request(req):
	if req.method == 'POST':
		content, status_code = handle_post(req)
	elif req.method == 'GET':
		content, status_code = handle_get(req)
	else:
		content, status_code = "Not Found", 404
	return content, status_code

def handle_get(request):
	return chat_interface(request), 200

def handle_post(request):
	return chat_interface(request), 200

def chat_interface(request):
	global messages, selected_model, previous_model
	output = ""
	
	if request.method == 'POST':
		user_input = request.form['command']
		selected_model = request.form['model']

		# Reset chat if model changes
		if selected_model != previous_model:
			messages = []
			previous_model = selected_model
		
		try:
			# Create content list starting with user input
			current_message = {"text": user_input}
			contents = [{"role": "user", "parts": [current_message]}]
			
			# Add previous messages to maintain context
			if messages:
				history_contents = []
				for msg in messages:
					history_contents.append({
						"role": msg["role"],
						"parts": [{"text": msg["content"]}]
					})
				contents = history_contents + contents
			
			# Generate response
			response = client.models.generate_content(
				model=selected_model,
				contents=contents,
				config=get_generation_config()
			)
			
			# Add messages to history
			messages.append({"role": "user", "content": user_input})
			messages.append({"role": "model", "content": response.text})
			
		except Exception as e:
			error_message = f"Error: {str(e)}"
			messages.append({"role": "user", "content": user_input})
			messages.append({"role": "assistant", "content": error_message})
	
	# Generate output HTML
	for msg in reversed(messages[-10:]):  # Show last 10 messages
		if msg['role'] == 'user':
			output += f"<b>User:</b> {msg['content']}<br>"
		elif msg['role'] == 'model' or msg['role'] == 'assistant':
			output += f"<b>Assistant:</b> {msg['content']}<br>"
	
	return render_template_string(HTML_TEMPLATE, output=output, selected_model=selected_model)

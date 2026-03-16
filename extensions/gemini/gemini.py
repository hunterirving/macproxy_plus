from flask import request, render_template_string
from google import genai
from google.genai import types
import config

# Initialize the Google API Client with your API key
client = genai.Client(api_key=config.GEMINI_API_KEY)

DOMAIN = "gemini.google.com"

messages = []
selected_model = "gemini-3-flash-preview"
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
			<option value="gemini-3-flash-preview" {{ 'selected' if selected_model == 'gemini-3-flash-preview' else '' }}>Gemini 3 Flash Preview (Balanced)</option>
			<option value="gemini-3.1-flash-lite-preview" {{ 'selected' if selected_model == 'gemini-3.1-flash-lite-preview' else '' }}>Gemini 3.1 Flash-Lite Preview (Fast)</option>
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
	for msg in reversed(messages[-10:]):
		if msg['role'] == 'user':
			output += f"<b>User:</b> {msg['content']}<br>"
		elif msg['role'] == 'model' or msg['role'] == 'assistant':
			output += f"<b>Assistant:</b> {msg['content']}<br>"
	
	return render_template_string(HTML_TEMPLATE, output=output, selected_model=selected_model)

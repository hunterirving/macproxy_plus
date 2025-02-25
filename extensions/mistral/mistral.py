from flask import request, render_template_string
from mistralai import Mistral
import config

# Initialize the Mistral Client with your API key
client = Mistral(api_key=config.MISTRAL_API_KEY)

DOMAIN = "chat.mistral.ai"

messages = []
selected_model = "mistral-large-latest"
previous_model = selected_model

system_prompt = """Please provide your response in plain text using only ASCII characters. 
Never use any special or esoteric characters that might not be supported by older systems.
Your responses will be presented to the user within the body of an html document. Be aware that any html tags you respond with will be interpreted and rendered as html. 
Therefore, when discussing an html tag, do not wrap it in <>, as it will be rendered as html. Instead, wrap the name of the tag in <b> tags to emphasize it, for example "the <b>a</b> tag". 
You do not need to provide a <body> tag. 
When responding with a list, ALWAYS format it using <ol> or <ul> with individual list items wrapped in <li> tags. 
When responding with a link, use the <a> tag.
When responding with code or other formatted text (including prose or poetry), always insert <pre></pre> tags with <code></code> tags nested inside (which contain the formatted content).
If the user asks you to respond 'in a code block', this is what they mean. NEVER use three backticks (```like so``` (markdown style)) when discussing code. If you need to highlight a variable name or text of similar (short) length, wrap it in <code> tags (without the aforementioned <pre> tags). Do not forget to close html tags where appropriate. 
When using a code block, ensure that individual lines of text do not exceed 60 characters.
NEVER use **this format** (markdown style) to bold text  - instead, wrap text in <b> tags or <i> tags (when appropriate) to emphasize it."""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<title>Mistral Le Chat</title>
</head>
<body>
	<form method="post" action="/">
		<select id="model" name="model">
			<option value="mistral-large-latest" {{ 'selected' if selected_model == 'mistral-large-latest' else '' }}>Mistral Large Latest</option>
			<option value="mistral-small-latest" {{ 'selected' if selected_model == 'mistral-small-latest' else '' }}>Mistral Small Latest</option>
			<option value="open-mistral-nemo" {{ 'selected' if selected_model == 'open-mistral-nemo' else '' }}>Mistral Nemo 2407</option>
			<option value="ministral-8b-latest" {{ 'selected' if selected_model == 'ministral-8b-latest' else '' }}>Ministral 8b</option>
			<option value="ministral-3b-latest" {{ 'selected' if selected_model == 'ministral-3b-latest' else '' }}>Ministral 3b</option>
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

		# Check if the model has changed
		if selected_model != previous_model:
			previous_model = selected_model
			messages = [{"role": "user", "content": user_input}]
		else:
			messages.append({"role": "user", "content": user_input})

		# Prepare messages for the API call
		api_messages = [{"role": msg["role"], "content": (system_prompt + msg["content"]) if msg["role"] == "user" and i < 2 else msg["content"]} for i, msg in enumerate(messages[-10:])]

		# Send the conversation to Mistral La Plateforme and get the response
		try:
			response = client.chat.complete(
				model=selected_model,
				max_tokens=1000,
				messages=api_messages,
			)
			response_body = response.choices[0].message.content
			messages.append({"role": "assistant", "content": response_body})

		except Exception as e:
			response_body = f"An error occurred: {str(e)}"
			messages.append({"role": "assistant", "content": response_body})

	for msg in reversed(messages[-10:]):
		if msg['role'] == 'user':
			output += f"<b>User:</b> {msg['content']}<br>"
		elif msg['role'] == 'assistant':
			output += f"<b>Mistral:</b> {msg['content']}<br>"

	return render_template_string(HTML_TEMPLATE, output=output, selected_model=selected_model)
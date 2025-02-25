from flask import request, render_template_string
import anthropic
import config

# Initialize the Anthropic client with your API key
client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

DOMAIN = "claude.ai"

messages = []
selected_model = "claude-3-7-sonnet-latest"
previous_model = selected_model

system_prompt = """Please provide your response in plain text using only ASCII characters. 
Never use any special or esoteric characters that might not be supported by older systems.
Your responses will be presented to the user within the body of an html document. Be aware that any html tags you respond with will be interpreted and rendered as html. 
Therefore, when discussing an html tag, do not wrap it in <>, as it will be rendered as html. Instead, wrap the name of the tag in <b> tags to emphasize it, for example "the <b>a</b> tag". 
You do not need to provide a <body> tag.
Use <p> tags to separate chunks of text (plain newlines will not be rendered as such).
Your response must not begin with an html tag, and should instead begin with raw text.
When responding with a list, always format it using <ol> or <ul> with individual list items wrapped in <li> tags. 
When responding with a link, use the <a> tag.
When responding with code, use <pre></pre> tags with <code></code> tags nested inside (which contain the code).
If the user asks you to respond 'in a code block', this is what they mean. Never use three backticks (```like so``` (markdown style)) when discussing code. If you need to highlight a variable name or text of similar (short) length, wrap it in <code> tags (without the aforementioned <pre> tags).
Remember to close html tags where appropriate. 
When using a code block, ensure that individual lines of text do not exceed 60 characters.
Never use **this format** (markdown style) to bold text  - instead, wrap text in <b> tags or <i> tags (when appropriate) to emphasize it."""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<title>Claude</title>
</head>
<body>
	<form method="post" action="/">
		<select id="model" name="model">
			<option value="claude-3-7-sonnet-latest" {{ 'selected' if selected_model == 'claude-3-7-sonnet-latest' else '' }}>Claude 3.7 Sonnet</option>
			<option value="claude-3-5-sonnet-latest" {{ 'selected' if selected_model == 'claude-3-5-sonnet-latest' else '' }}>Claude 3.5 Sonnet</option>
			<option value="claude-3-5-haiku-latest" {{ 'selected' if selected_model == 'claude-3-5-haiku-latest' else '' }}>Claude 3.5 Haiku</option>
			<option value="claude-3-opus-latest" {{ 'selected' if selected_model == 'claude-3-opus-latest' else '' }}>Claude 3 Opus</option>
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
		api_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages[-10:]]

		# Send the conversation to Anthropic and get the response
		try:
			response = client.messages.create(
				model=selected_model,
				max_tokens=1000,
				messages=api_messages,
				system=system_prompt
			)
			response_body = response.content[0].text
			messages.append({"role": "assistant", "content": response_body})
			print(response_body)

		except Exception as e:
			response_body = f"An error occurred: {str(e)}"
			messages.append({"role": "assistant", "content": response_body})

	for msg in reversed(messages[-10:]):
		if msg['role'] == 'user':
			output += f"<b>User:</b> {msg['content']}<br>"
		elif msg['role'] == 'assistant':
			output += f"<b>Claude:</b> {msg['content']}<br>"

	return render_template_string(HTML_TEMPLATE, output=output, selected_model=selected_model)

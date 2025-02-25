from flask import request, render_template_string
from openai import OpenAI
import config

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=config.OPEN_AI_API_KEY)

DOMAIN = "chatgpt.com"

messages = []
selected_model = "gpt-4o"
previous_model = selected_model

system_prompts = [
	{"role": "system", "content": "Please provide your response in plain text using only ASCII characters. "
		"Never use any special or esoteric characters that might not be supported by older systems. "},
	{"role": "system", "content": "Your responses will be presented to the user within "
		"the body of an html document. Be aware that any html tags you respond with will be interpreted and rendered as html. "
		"Therefore, when discussing an html tag, do not wrap it in <>, as it will be rendered as html. Instead, wrap the name "
		"of the tag in <b> tags to emphasize it, for example \"the <b>a</b> tag\". "
		"You do not need to provide a <body> tag. "
		"When responding with a list, ALWAYS format it using <ol> or <ul> with individual list items wrapped in <li> tags. "
		"When responding with a link,  the <a> tag."},
	{"role": "system", "content": "When responding with code or other formatted text (including prose or poetry), always insert "
		"<pre></pre> tags with <code></code> tags nested inside (which contain the formatted content)."
		"If the user asks you to respond 'in a code block', this is what they mean. NEVER use three backticks "
		"(```like so``` (markdown style)) when discussing code. If you need to highlight a variable name or text of similar (short) length, "
		"wrap it in <code> tags (without the aforementioned <pre> tags). Do not forget to close html tags where appropriate. "
		"When using a code block, ensure that individual lines of text do not exceed 60 characters."},
	{"role": "system", "content": "NEVER use **this format** (markdown style) to bold text  - instead, wrap text in <b> tags or <i> "
		"tags (when appropriate) to emphasize it."},
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<title>ChatGPT</title>
</head>
<body>
	<form method="post" action="/">
		<select id="model" name="model">
		    <option value="chatgpt-4o-latest" {{ 'selected' if selected_model == 'chatgpt-4o-latest' else '' }}>ChatGPT-4o</option>
			<option value="gpt-4o" {{ 'selected' if selected_model == 'gpt-4o' else '' }}>GPT-4o</option>
			<option value="gpt-4o-mini" {{ 'selected' if selected_model == 'gpt-4o-mini' else '' }}>GPT-4o Mini</option>
			<option value="gpt-4-turbo" {{ 'selected' if selected_model == 'gpt-4-turbo' else '' }}>GPT-4</option>
			<option value="gpt-3.5-turbo" {{ 'selected' if selected_model == 'gpt-3.5-turbo' else '' }}>GPT-3.5</option>
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

		# Prepare messages, ensuring not to exceed the most recent 10 interactions
		messages_to_send = system_prompts + messages[-10:]

		# Send the messages to OpenAI and get the response
		response = client.chat.completions.create(
			model=selected_model,
			messages=messages_to_send
		)
		response_body = response.choices[0].message.content
		messages.append({"role": "system", "content": response_body})

	for msg in reversed(messages[-10:]):
		if msg['role'] == 'user':
			output += f"<b>User:</b> {msg['content']}<br>"
		elif msg['role'] == 'system':
			output += f"<b>ChatGPT:</b> {msg['content']}<br>"

	return render_template_string(HTML_TEMPLATE, output=output, selected_model=selected_model)

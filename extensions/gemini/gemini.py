from flask import request, render_template_string
import google.generativeai as genai
import extensions.config as config

# Initialize the Google API Client with your API key
genai.configure(api_key=config.google_api_key)

DOMAIN = "gemini.google.com"

messages = []
selected_model = "gemini-1.5-pro-latest"
previous_model = selected_model

system_prompt = """Please provide your response in plain text using only ASCII characters. 
Never use any special or esoteric characters that might not be supported by older systems.
Your responses will be presented to the user within the body of an html document. Be aware that any html tags you respond with will be interpreted and rendered as html. 
Therefore, when discussing an html tag, do not wrap it in <>, as it will be rendered as html. Instead, wrap the name of the tag in <b> tags to emphasize it, for example "the <b>a</b> tag". 
You do not need to provide a <body> tag. 
When responding with a list, ALWAYS format it using <ol> or <ul> with individual list items wrapped in <li> tags. 
When responding with a link, use the <a> tag.
When responding with code or other formatted text (including prose or poetry), always insert <pre></pre> tags with <code></code> tags nested inside (which contain the formatted content).
If the user asks you to respond 'in a code block', this is what they mean."""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Google Gemini</title>
</head>
<body>
    <form method="post" action="/">
        <input type="text" size="38" name="command" required autocomplete="off">
        <input type="submit" value="Submit">
        <select id="model" name="model">
            <option value="gemini-1.5-pro-latest" {{ 'selected' if selected_model == 'gemini-1.5-pro-latest' else '' }}>Gemini 1.5 Pro Latest</option>
            <option value="gemini-1.5-pro-exp-0801" {{ 'selected' if selected_model == 'gemini-1.5-pro-exp-0801' else '' }}>Gemini 1.5 Pro Experimental 0801</option>
            <option value="gemini-1.5-pro-exp-0827" {{ 'selected' if selected_model == 'gemini-1.5-pro-exp-0827' else '' }}>Gemini 1.5 Pro Experimental 0827</option>
            <option value="gemini-exp-1114" {{ 'selected' if selected_model == 'gemini-exp-1114' else '' }}>Gemini Experimental 1114</option>
            <option value="gemini-1.5-flash-latest" {{ 'selected' if selected_model == 'gemini-1.5-flash-latest' else '' }}>Gemini 1.5 Flash Latest</option>
            <option value="gemini-1.5-flash-exp-0801" {{ 'selected' if selected_model == 'gemini-1.5-flash-exp-0801' else '' }}>Gemini 1.5 Flash Experimental 0801</option>
            <option value="gemini-1.5-flash-exp-0827" {{ 'selected' if selected_model == 'gemini-1.5-flash-exp-0827' else '' }}>Gemini 1.5 Flash Experimental 0827</option>
            <option value="gemini-1.5-flash-8b" {{ 'selected' if selected_model == 'gemini-1.5-flash-8b' else '' }}>Gemini 1.5 Flash 8b</option>
            <option value="gemini-1.5-flash-8b-exp-0924" {{ 'selected' if selected_model == 'gemini-1.5-flash-8b-exp-0924' else '' }}>Gemini 1.5 Flash 8b Experimental 0924</option>
            <option value="gemini-1.0-pro" {{ 'selected' if selected_model == 'gemini-1.0-pro' else '' }}>Gemini 1.0 Pro (Legacy)</option>
        </select>
    </form>
    <div id="chat">
        <p>{{ output|safe }}</p>
    </div>
</body>
</html>
"""

def get_generation_config():
    return {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1000,
        "response_mime_type": "text/plain",
    }

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
            messages = []

        try:
            # Initialize model with proper configuration
            model = genai.GenerativeModel(
                model_name=selected_model,
                generation_config=get_generation_config()
            )

            # Start or continue chat session
            if not messages:
                chat = model.start_chat(history=[])
                messages.append({"role": "system", "content": system_prompt})
            else:
                history = [
                    {"role": msg["role"], "parts": [msg["content"]]} 
                    for msg in messages[1:]  # Skip system prompt when creating history
                ]
                chat = model.start_chat(history=history)

            # Send message and get response
            response = chat.send_message(user_input)
            
            # Add messages to history
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "model", "content": response.text})

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "model", "content": error_message})

    # Display last 10 messages
    for msg in reversed(messages[-10:]):
        if msg['role'] == 'user':
            output += f"<b>User:</b> {msg['content']}<br>"
        elif msg['role'] == 'assistant':
            output += f"<b>Gemini:</b> {msg['content']}<br>"
        # Skip system messages in output

    return render_template_string(HTML_TEMPLATE, output=output, selected_model=selected_model)

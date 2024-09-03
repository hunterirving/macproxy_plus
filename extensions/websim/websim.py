# HINT: MacWeb 2.0 doesn't seem to have CSS support. To work around this, set <h4> styling to font="Chicago" with Size="As Is".

from flask import request, render_template_string

DOMAIN = "websim.ai"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
	<title>websim.ai</title>
</head>
<body>
    <center><br><br>
        <font size="7"><h4>w e b s i m</h4></font>
        <form method="post">
            {% if override_active %}
                <input type="submit" name="action" value="disable">
            {% else %}
                <input type="submit" name="action" value="enable">
            {% endif %}
        </form>
        <p>
            {% if override_active %}
                <b>{{ status }}!</b><br><br>
                enter a URL in the address bar,<br>or click <b>disable</b> to quit.
            {% else %}
                {{ status }}.<br>
                click <b>enable</b> to begin.
            {% endif %}
        </p>
    </center>
</body>
</html>
"""

override_active = False

def get_override_status():
	global override_active
	return override_active

def handle_request(req):
	global override_active

	if req.method == 'POST':
		action = req.form.get('action')
		if action == 'enable':
			override_active = True
		elif action == 'disable':
			override_active = False

	status = "websim enabled" if override_active else "websim disabled"
	
	requested_url = req.url if override_active else ""

	return render_template_string(HTML_TEMPLATE, 
								  status=status, 
								  override_active=override_active,
								  requested_url=requested_url)
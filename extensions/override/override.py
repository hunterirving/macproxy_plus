from flask import request, render_template_string

DOMAIN = "override.test"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
	<title>Override Control</title>
</head>
<body>
	<h1>Override Control</h1>
	<form method="post">
		<input type="submit" name="action" value="Enable Override">
		<input type="submit" name="action" value="Disable Override">
	</form>
	<p>Current status: {{ status }}</p>
	{% if override_active %}
	<p>Requested URL: {{ requested_url }}</p>
	{% endif %}
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
		if action == 'Enable Override':
			override_active = True
		elif action == 'Disable Override':
			override_active = False

	status = "Override Active" if override_active else "Override Inactive"
	
	requested_url = req.url if override_active else ""

	return render_template_string(HTML_TEMPLATE, 
								  status=status, 
								  override_active=override_active,
								  requested_url=requested_url)
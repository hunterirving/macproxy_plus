# Standard Library imports
import os

def load_preset():
	# Try to import config.py first
	try:
		import config
	except ModuleNotFoundError:
		print("config.py not found, exiting.")
		quit()

	"""
	Load preset configuration and override default settings if a preset is specified
	"""
	if not hasattr(config, 'PRESET') or not config.PRESET:
		return config

	preset_name = config.PRESET
	preset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../presets', preset_name)
	preset_file = os.path.join(preset_dir, f"{preset_name}.py")

	if not os.path.exists(preset_dir):
		print(f"Error: Preset directory not found: {preset_dir}")
		print(f"Make sure the preset '{preset_name}' exists in the presets directory")
		quit()

	if not os.path.exists(preset_file):
		print(f"Error: Preset file not found: {preset_file}")
		print(f"Make sure {preset_name}.py exists in the {preset_name} directory")
		quit()

	try:
		# Import the preset module
		import importlib.util
		spec = importlib.util.spec_from_file_location(preset_name, preset_file)
		preset_module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(preset_module)

		# List of variables that can be overridden by presets
		override_vars = [
			'SIMPLIFY_HTML',
			'TAGS_TO_STRIP',
			'TAGS_TO_UNWRAP',
			'ATTRIBUTES_TO_STRIP',
			'CAN_RENDER_INLINE_IMAGES',
			'RESIZE_IMAGES',
			'MAX_IMAGE_WIDTH',
			'MAX_IMAGE_HEIGHT',
			'CONVERT_IMAGES',
			'CONVERT_IMAGES_TO_FILETYPE',
			'DITHERING_ALGORITHM',
			'WEB_SIMULATOR_PROMPT_ADDENDUM',
			'CONVERT_CHARACTERS',
			'CONVERSION_TABLE'
		]

		changes_made = False
		# Override config variables with preset values
		for var in override_vars:
			if hasattr(preset_module, var):
				preset_value = getattr(preset_module, var)
				if not hasattr(config, var) or getattr(config, var) != preset_value:
					changes_made = True
					old_value = getattr(config, var) if hasattr(config, var) else None
					setattr(config, var, preset_value)
					
					# Format the values for printing
					def format_value(val):
						if isinstance(val, (list, dict)):
							return str(val)
						elif isinstance(val, str):
							return f"'{val}'"
						else:
							return str(val)
					if old_value is None:
						val = str(format_value(preset_value)).replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
						truncated = val[:100] + ('...' if len(val) > 100 else '')
						print(f"Preset '{preset_name}' set {var} to {truncated}")
					else:
						old_val = str(format_value(old_value)).replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
						new_val = str(format_value(preset_value)).replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
						old_truncated = old_val[:100] + ('...' if len(old_val) > 100 else '')
						new_truncated = new_val[:100] + ('...' if len(new_val) > 100 else '')
						print(f"Preset '{preset_name}' changed {var} from {old_truncated} to {new_truncated}")
		if changes_made:
			print(f"Successfully loaded preset: {preset_name}")
		else:
			print(f"Loaded preset '{preset_name}' (no changes were necessary)")

		return config

	except Exception as e:
		print(f"Error loading preset '{preset_name}': {str(e)}")
		quit()

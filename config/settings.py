# settings.py
import json
import logging

SETTINGS_FILE = 'settings.json'

def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            logging.info("Settings loaded successfully.")
            return settings
    except FileNotFoundError:
        logging.error("Settings file not found. Using default settings.")
        return {
            "last_device_id": 1,
            "noise_reduction": 1.0,
            "sensitivity": 1.0,
            "language": "en-US",
            "shortcuts": {}
        }

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)
    logging.info("Settings saved.")
import pystray
from PIL import Image, ImageDraw
import tkinter as tk
import threading
import logging

def create_image():
    try:
        # Create an image with a simple icon
        image = Image.new('RGB', (64, 64), (255, 255, 255))
        dc = ImageDraw.Draw(image)
        dc.rectangle((0, 0, 64, 64), fill=(0, 0, 0))
        return image
    except Exception as e:
        logging.error(f"Error creating system tray image: {e}")
        return None

def on_quit(icon, item):
    try:
        icon.stop()
        if tk._default_root:
            tk._default_root.quit()
    except Exception as e:
        logging.error(f"Error quitting application from system tray: {e}")

def show_window(icon, item):
    try:
        if tk._default_root:
            tk._default_root.after(0, tk._default_root.deiconify)
    except Exception as e:
        logging.error(f"Error showing window from system tray: {e}")

def setup_tray():
    try:
        def run_tray():
            try:
                icon = pystray.Icon("Voice Shortcut Controller")
                icon.icon = create_image()
                if icon.icon is None:
                    logging.error("Failed to create system tray icon.")
                    return
                icon.menu = pystray.Menu(
                    pystray.MenuItem("Show", show_window),
                    pystray.MenuItem("Quit", on_quit)
                )
                icon.run_detached()
            except Exception as e:
                logging.error(f"Error in system tray thread: {e}")
        threading.Thread(target=run_tray, daemon=True).start()
    except Exception as e:
        logging.error(f"Error setting up system tray: {e}")

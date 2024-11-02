import logging
import threading
import tkinter as tk
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item

def setup_tray(app):
    try:
        # Load the icon image (ensure 'icon.png' exists in the appropriate directory)
        image = Image.open("icon.png")
        menu = (
            item('Show', lambda: show_app(app)),
            item('Exit', lambda: exit_app(app))
        )
        tray_icon = pystray.Icon("voice-controller", image, "Voice Shortcut Controller", menu)
        threading.Thread(target=tray_icon.run, daemon=True).start()
        logging.info("System tray icon created.")
    except Exception as e:
        logging.error(f"Error setting up system tray: {e}")

def show_app(app):
    if app.winfo_exists():
        app.deiconify()
        app.lift()
        logging.info("Application window restored from system tray.")
    else:
        logging.warning("Attempted to show app, but it no longer exists.")

def exit_app(app):
    if app.winfo_exists():
        app.destroy()
        logging.info("Application exited from system tray.")
    else:
        logging.warning("Application already destroyed. Cannot exit again.")

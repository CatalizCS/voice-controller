import tkinter as tk
from tkinter import scrolledtext
import logging

class DebugWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        try:
            self.title("Debug Window")
            self.geometry("800x600")  # Resize the window
            self.resizable(True, True)  # Allow resizing
            self.create_widgets()
            self.protocol("WM_DELETE_WINDOW", self.on_close)
            self.periodic_update()  # Add periodic update
        except Exception as e:
            logging.error(f"Error initializing DebugWindow: {e}")

    def create_widgets(self):
        try:
            self.log_text = scrolledtext.ScrolledText(self, state='disabled')
            self.log_text.pack(expand=True, fill='both', padx=10, pady=10)
        except Exception as e:
            logging.error(f"Error creating widgets in DebugWindow: {e}")

    def append_log(self, message):
        try:
            self.log_text.configure(state='normal')
            self.log_text.insert(tk.END, message + '\n')
            self.log_text.configure(state='disabled')
            self.log_text.yview(tk.END)
        except Exception as e:
            logging.error(f"Error appending log to DebugWindow: {e}")

    def on_close(self):
        try:
            self.destroy()
            self.master.debug_window = None  # Reset the reference in master
        except Exception as e:
            logging.error(f"Error closing DebugWindow: {e}")

    def periodic_update(self):
        try:
            # Optionally, fetch logs from a log handler and display them
            self.update_idletasks()
            self.after(50, self.periodic_update)  # Schedule the next update
        except Exception as e:
            logging.error(f"Error during periodic update in DebugWindow: {e}")

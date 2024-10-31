import tkinter as tk
from tkinter import ttk
from audio.device_manager import list_input_devices

class InputDevicesWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Input Devices")
        self.geometry("400x300")
        self.create_widgets()

    def create_widgets(self):
        devices = list_input_devices()
        device_listbox = tk.Listbox(self)
        device_listbox.pack(expand=True, fill='both')
        for index, name in devices:
            device_listbox.insert(tk.END, f"{index}: {name}")

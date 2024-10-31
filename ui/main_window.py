import tkinter as tk
from tkinter import ttk
import logging
import threading
from config.settings import load_settings, save_settings
from ui.system_tray import setup_tray
from ui.device_settings import DeviceSettings
from audio.device_manager import list_input_devices
from audio.visualizer import AudioVisualizer
from ui.input_devices import InputDevicesWindow
from audio.voice_recognition import voice_recognition, stop_voice_recognition
import base64  # Add import for base64

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            self.settings = load_settings()
            logging.debug(f"Loaded settings: {self.settings}")
            self.title("Voice Shortcut Controller")
            self.geometry("800x600")  # Resize the window
            self.resizable(True, True)  # Allow resizing
            self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
            self.language_display_mapping = {  # Added as an instance variable
                "": "Auto (Default)",
                "en-US": "English (United States)",
                "es-ES": "Spanish (Spain)",
                "fr-FR": "French (France)",
                "de-DE": "German (Germany)",
                "zh-CN": "Chinese (Mandarin)",
                "ja-JP": "Japanese",
                "ko-KR": "Korean",
                "pt-BR": "Portuguese (Brazil)",
                "vi-VN": "Vietnamese (Vietnam)",  # Add Vietnamese
            }
            language_code = self.settings.get("language", "")
            logging.debug(f"Language code: {language_code}")
            self.settings["language_display"] = self.language_display_mapping.get(
                language_code, "English (United States)"
            )
            logging.debug(f"Language display: {self.settings['language_display']}")
            self.visualizer_running = False  # Flag to track visualizer state
            self.device_settings_window = None  # Reference to DeviceSettings window
            self.input_devices_window = None  # Reference to InputDevicesWindow
            self.debug_window = None  # Reference to DebugWindow (if applicable)
            self.create_widgets()
            # Temporarily disable system tray to test GUI startup
            # setup_tray()
            self.periodic_update()  # Add periodic update
            self.voice_recognition_thread = None
            self.start_voice_recognition()  # Start voice recognition
            logging.info("Application UI initialized.")
        except Exception as e:
            logging.error(f"Error during App initialization: {e}")

    def start_voice_recognition(self):
        try:
            if self.voice_recognition_thread and self.voice_recognition_thread.is_alive():
                logging.warning("Voice recognition thread is already running.")
                return  # Prevent starting another thread
            logging.info("Starting voice recognition thread.")
            self.voice_recognition_thread = threading.Thread(target=voice_recognition, args=(self.settings,), daemon=True)
            self.voice_recognition_thread.start()
            logging.info("Voice recognition thread started.")
        except Exception as e:
            logging.error(f"Error starting voice recognition: {e}")

    def restart_voice_recognition(self):
        try:
            logging.info("Restarting voice recognition.")
            stop_voice_recognition()  # Stop existing recognition
            if self.voice_recognition_thread:
                self.voice_recognition_thread.join(timeout=2)  # Ensure thread has stopped
                logging.info("Voice recognition thread stopped.")
            self.start_voice_recognition()  # Restart with new settings
        except Exception as e:
            logging.error(f"Error restarting voice recognition: {e}")

    def create_device_settings_button(self, parent):
        device_settings_button = ttk.Button(parent, text="Device Settings", command=self.open_device_settings)
        device_settings_button.pack(side='left', padx=5)

    def create_device_list_button(self, parent):
        device_list_button = ttk.Button(parent, text="List Input Devices", command=self.list_devices)
        device_list_button.pack(side='left', padx=5)

    def create_visualizer_button(self, parent):
        # Store the button as an instance variable for later reference
        self.visualizer_button = ttk.Button(parent, text="Start Visualizer", command=self.start_visualizer)
        self.visualizer_button.pack(side='left', padx=5)

    def create_input_devices_button(self, parent):
        input_devices_button = ttk.Button(parent, text="Input Devices", command=self.open_input_devices)
        input_devices_button.pack(side='left', padx=5)

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill='both')

        # Device Selection
        device_frame = ttk.LabelFrame(main_frame, text="Device Settings", padding="10")
        device_frame.pack(fill='x', pady=5)
        device_label = ttk.Label(device_frame, text="Input Device:")
        device_label.grid(row=0, column=0, sticky='w')
        self.device_var = tk.StringVar(value=self.settings.get("last_device_name", ""))
        devices = list_input_devices()
        device_names = [name for _, name in devices]
        device_combobox = ttk.Combobox(device_frame, textvariable=self.device_var, values=device_names)
        device_combobox.grid(row=0, column=1, sticky='ew')
        device_combobox.bind("<<ComboboxSelected>>", self.on_device_selected)  # Bind selection event
        device_frame.columnconfigure(1, weight=1)

        # Noise Reduction
        noise_frame = ttk.LabelFrame(main_frame, text="Noise Reduction", padding="10")
        noise_frame.pack(fill='x', pady=5)
        noise_label = ttk.Label(noise_frame, text="Noise Reduction Level:")
        noise_label.grid(row=0, column=0, sticky='w')
        self.noise_var = tk.DoubleVar(value=self.settings.get("noise_reduction", 1.0))
        noise_scale = ttk.Scale(noise_frame, from_=0.0, to=2.0, variable=self.noise_var)
        noise_scale.grid(row=0, column=1, sticky='ew')
        noise_frame.columnconfigure(1, weight=1)

        # Shortcuts Management
        shortcuts_frame = ttk.LabelFrame(main_frame, text="Shortcuts", padding="10")
        shortcuts_frame.pack(fill='both', expand=True, pady=5)
        self.shortcuts_listbox = tk.Listbox(shortcuts_frame)
        self.shortcuts_listbox.pack(fill='both', expand=True, pady=5)
        self.shortcuts_listbox.bind("<<ListboxSelect>>", self.on_shortcut_selected)  # Bind selection event
        self.load_shortcuts()

        add_button = ttk.Button(shortcuts_frame, text="Add Shortcut", command=self.add_shortcut)
        add_button.pack(side='left', padx=5)
        edit_button = ttk.Button(shortcuts_frame, text="Edit Shortcut", command=self.edit_shortcut)
        edit_button.pack(side='left', padx=5)
        remove_button = ttk.Button(shortcuts_frame, text="Remove Shortcut", command=self.remove_shortcut)
        remove_button.pack(side='left', padx=5)

        # Save Settings Button
        save_button = ttk.Button(main_frame, text="Save Settings", command=self.save_settings)
        save_button.pack(pady=10)

        # Additional Buttons
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.pack(fill='x', pady=5)
        self.create_device_settings_button(button_frame)
        self.create_device_list_button(button_frame)
        self.create_visualizer_button(button_frame)
        self.create_input_devices_button(button_frame)

        # Add Audio Length Settings
        audio_length_frame = ttk.LabelFrame(main_frame, text="Audio Length Settings", padding="10")
        audio_length_frame.pack(fill='x', pady=5)

        # Minimum Audio Length
        min_length_label = ttk.Label(audio_length_frame, text="Minimum Audio Length (s):")
        min_length_label.grid(row=0, column=0, sticky='w')
        self.min_length_var = tk.IntVar(value=self.settings.get("min_audio_length", 1))
        min_length_spinbox = ttk.Spinbox(
            audio_length_frame, from_=1, to=10, textvariable=self.min_length_var, width=5
        )
        min_length_spinbox.grid(row=0, column=1, sticky='w')

        # Maximum Audio Length
        max_length_label = ttk.Label(audio_length_frame, text="Maximum Audio Length (s):")
        max_length_label.grid(row=1, column=0, sticky='w', pady=5)
        self.max_length_var = tk.IntVar(value=self.settings.get("max_audio_length", 10))
        max_length_spinbox = ttk.Spinbox(
            audio_length_frame, from_=1, to=10, textvariable=self.max_length_var, width=5
        )
        max_length_spinbox.grid(row=1, column=1, sticky='w')

        # Validate that min <= max
        self.min_length_var.trace('w', self.validate_audio_lengths)
        self.max_length_var.trace('w', self.validate_audio_lengths)

        audio_length_frame.columnconfigure(1, weight=1)

        # Add Processing Backend Selection
        processing_frame = ttk.LabelFrame(main_frame, text="Processing Backend", padding="10")
        processing_frame.pack(fill='x', pady=5)

        processing_label = ttk.Label(processing_frame, text="Select Processing Backend:")
        processing_label.grid(row=0, column=0, sticky='w')
        self.processing_var = tk.StringVar(value=self.settings.get("processing_backend", "CPU"))
        processing_options = ["CPU", "GPU"]
        processing_combobox = ttk.Combobox(
            processing_frame, textvariable=self.processing_var, values=processing_options, state="readonly"
        )
        processing_combobox.grid(row=0, column=1, sticky='w')
        processing_combobox.bind("<<ComboboxSelected>>", self.on_processing_selected)

        processing_frame.columnconfigure(1, weight=1)

        # Add Language Display in Main Window (Optional)
        language_label = ttk.Label(main_frame, text="Current Recognition Language:")
        language_label.pack(pady=5)
        self.current_language_label = ttk.Label(
            main_frame, 
            text=self.settings.get("language_display", "English (United States)")
        )
        self.current_language_label.pack(pady=5)

        # Add Enable Shortcuts Option
        enable_shortcuts_frame = ttk.LabelFrame(main_frame, text="Shortcut Settings", padding="10")
        enable_shortcuts_frame.pack(fill='x', pady=5)
        self.enable_shortcuts_var = tk.BooleanVar(value=self.settings.get("enable_shortcuts", True))
        enable_shortcuts_checkbutton = ttk.Checkbutton(enable_shortcuts_frame, text="Enable Shortcuts", variable=self.enable_shortcuts_var)
        enable_shortcuts_checkbutton.grid(row=0, column=0, sticky='w')

        # Add Required Keyword Entry
        required_keyword_label = ttk.Label(enable_shortcuts_frame, text="Required Keyword:")
        required_keyword_label.grid(row=1, column=0, sticky='w')
        self.required_keyword_var = tk.StringVar(value=self.settings.get("required_keyword", ""))
        required_keyword_entry = ttk.Entry(enable_shortcuts_frame, textvariable=self.required_keyword_var)
        required_keyword_entry.grid(row=1, column=1, sticky='ew')
        enable_shortcuts_frame.columnconfigure(1, weight=1)

    def validate_audio_lengths(self, *args):
        min_val = self.min_length_var.get()
        max_val = self.max_length_var.get()
        if min_val > max_val:
            logging.warning("Minimum audio length cannot be greater than maximum audio length.")
            self.min_length_var.set(max_val)
        elif min_val < 1:
            self.min_length_var.set(1)
        elif max_val > 10:
            self.max_length_var.set(10)

    def on_processing_selected(self, event):
        selected_backend = self.processing_var.get()
        logging.info(f"Selected processing backend: {selected_backend}")
        # Additional actions can be performed here if necessary

    def on_device_selected(self, event):
        selected_device = self.device_var.get()
        logging.info(f"Selected device: {selected_device}")
        # Update settings or perform other actions based on the selected device

    def on_shortcut_selected(self, event):
        try:
            selected = self.shortcuts_listbox.curselection()
            if not selected:
                logging.warning("No shortcut selected.")
                return
            selected_shortcut = self.shortcuts_listbox.get(selected)
            logging.info(f"Selected shortcut: {selected_shortcut}")
            # Update settings or perform other actions based on the selected shortcut
        except Exception as e:
            logging.error(f"Error selecting shortcut: {e}")

    def open_device_settings(self):
        if self.device_settings_window and tk.Toplevel.winfo_exists(self.device_settings_window):
            logging.info("Device Settings window already open. Bringing it to focus.")
            self.device_settings_window.deiconify()
            self.device_settings_window.lift()
            return
        self.device_settings_window = DeviceSettings(self, self.settings)
        self.device_settings_window.protocol("WM_DELETE_WINDOW", self.on_device_settings_close)

    def on_device_settings_close(self):
        if self.device_settings_window:
            self.device_settings_window.destroy()
            self.device_settings_window = None

    def load_shortcuts(self):
        """Load shortcuts from settings into the Listbox."""
        self.shortcuts_listbox.delete(0, tk.END)
        for command, shortcut in self.settings.get("shortcuts", {}).items():
            self.shortcuts_listbox.insert(tk.END, f"{command}: {shortcut['execute']}")

    def add_shortcut(self):
        """Open a dialog to add a new shortcut."""
        self.AddShortcutDialog(self)

    def edit_shortcut(self):
        """Open a dialog to edit the selected shortcut."""
        selected = self.shortcuts_listbox.curselection()
        if selected:
            shortcut_entry = self.shortcuts_listbox.get(selected)
            try:
                command, execute = shortcut_entry.split(":", 1)
                command = command.strip()
                execute = execute.strip()
                shortcut = self.settings["shortcuts"].get(command, {})
                self.AddShortcutDialog(self, command, shortcut)
            except ValueError:
                logging.error("Invalid shortcut format selected.")
        else:
            logging.warning("No shortcut selected to edit.")

    def remove_shortcut(self):
        """Remove the selected shortcut from the list and settings."""
        selected = self.shortcuts_listbox.curselection()
        if selected:
            shortcut_entry = self.shortcuts_listbox.get(selected)
            try:
                command, _ = shortcut_entry.split(":", 1)
                command = command.strip()
                if command in self.settings["shortcuts"]:
                    del self.settings["shortcuts"][command]
                    self.shortcuts_listbox.delete(selected)
                    save_settings(self.settings)
                    logging.info(f"Removed shortcut: {command}")
                else:
                    logging.error(f"Command '{command}' not found in settings.")
            except ValueError:
                logging.error("Invalid shortcut format selected.")
        else:
            logging.warning("No shortcut selected to remove.")

    def list_devices(self):
        threading.Thread(target=self._list_devices, daemon=True).start()

    def _list_devices(self):
        try:
            devices = list_input_devices()
            device_list_window = tk.Toplevel(self)
            device_list_window.title("Input Devices")
            device_list_window.geometry("400x300")
            listbox = tk.Listbox(device_list_window)
            listbox.pack(expand=True, fill='both')
            for index, name in devices:
                listbox.insert(tk.END, f"{index}: {name}")
        except Exception as e:
            logging.error(f"Error listing devices: {e}")

    def start_visualizer(self):
        if self.visualizer_running:
            logging.warning("Visualizer is already running.")
            return  # Prevent starting another instance
        self.visualizer_running = True  # Set the flag
        self.visualizer_button.config(state='disabled')  # Disable the button
        threading.Thread(target=self._start_visualizer, daemon=True).start()
    
    def _start_visualizer(self):
        try:
            visualizer = AudioVisualizer(device_name=self.device_var.get(), processing_backend=self.processing_var.get())
            visualizer.start()
        except Exception as e:
            logging.error(f"Error starting visualizer: {e}")
        finally:
            self.visualizer_running = False  # Reset the flag
            self.visualizer_button.config(state='normal')  # Re-enable the button

    def minimize_to_tray(self):
        try:
            self.withdraw()
            language_code = self.settings.get("language", "en-US")  # Define language_code
            language_display = self.language_display_mapping.get(
                language_code, "English (United States)"
            )  # Updated reference
            self.settings["language_display"] = language_display
            save_settings(self.settings)
            self.current_language_label.config(text=language_display)
            logging.info("Settings updated via UI.")
        except Exception as e:
            logging.error(f"Error minimizing to tray: {e}")

    def open_input_devices(self):
        if self.input_devices_window and tk.Toplevel.winfo_exists(self.input_devices_window):
            logging.info("Input Devices window already open. Bringing it to focus.")
            self.input_devices_window.deiconify()
            self.input_devices_window.lift()
            return
        self.input_devices_window = InputDevicesWindow(self)
        self.input_devices_window.protocol("WM_DELETE_WINDOW", self.on_input_devices_close)

    def on_input_devices_close(self):
        if self.input_devices_window:
            self.input_devices_window.destroy()
            self.input_devices_window = None

    def periodic_update(self):
        try:
            self.update_idletasks()
            self.after(50, self.periodic_update)  # Schedule the next update
        except Exception as e:
            logging.error(f"Error during periodic update: {e}")

    def save_settings(self):
        """Save current settings to the settings file."""
        try:
            self.settings["last_device_name"] = self.device_var.get()
            self.settings["noise_reduction"] = self.noise_var.get()
            self.settings["min_audio_length"] = self.min_length_var.get()
            self.settings["max_audio_length"] = self.max_length_var.get()
            self.settings["processing_backend"] = self.processing_var.get()
            self.settings["enable_shortcuts"] = self.enable_shortcuts_var.get()  # Save enable shortcuts setting
            self.settings["required_keyword"] = self.required_keyword_var.get()  # Save required keyword setting
            save_settings(self.settings)
            logging.info("Settings saved.")
            self.restart_voice_recognition()
            self.update_language_display()
        except Exception as e:
            logging.error(f"Error saving settings: {e}")

    def update_language_display(self):
        try:
            language_display = self.settings.get("language_display", "English (United States)")
            self.current_language_label.config(text=language_display)
            logging.info(f"Language updated to: {language_display}")
        except Exception as e:
            logging.error(f"Error updating language display: {e}")

    class AddShortcutDialog(tk.Toplevel):
        """A dialog window to add or edit a shortcut."""

        def __init__(self, master, command=None, shortcut=None):
            super().__init__(master)
            try:
                self.master = master
                self.command = command
                self.shortcut = shortcut or {"description": "", "execute": "", "enable": True, "requireWord": ""}
                self.title("Edit Shortcut" if command else "Add Shortcut")
                self.geometry("400x400")  # Increased size for more UI elements
                self.resizable(False, False)

                # Voice Command Entry
                ttk.Label(self, text="Voice Command:").pack(pady=5)
                self.command_var = tk.StringVar(value=command if command else "")
                self.command_entry = ttk.Entry(self, textvariable=self.command_var)
                self.command_entry.pack(pady=5, fill='x', padx=10)

                # Description Entry
                ttk.Label(self, text="Description:").pack(pady=5)
                self.description_var = tk.StringVar(value=self.shortcut["description"])
                self.description_entry = ttk.Entry(self, textvariable=self.description_var)
                self.description_entry.pack(pady=5, fill='x', padx=10)

                # Keyboard Shortcut Entry with Autocomplete
                ttk.Label(self, text="Keyboard Shortcut:").pack(pady=5)
                self.execute_var = tk.StringVar(value=self.shortcut["execute"])
                self.execute_entry = ttk.Entry(self, textvariable=self.execute_var)
                self.execute_entry.pack(pady=5, fill='x', padx=10)
                self.execute_entry.bind('<KeyRelease>', self.on_shortcut_keyrelease)

                # Enable Checkbox
                self.enable_var = tk.BooleanVar(value=self.shortcut["enable"])
                self.enable_checkbutton = ttk.Checkbutton(self, text="Enable", variable=self.enable_var)
                self.enable_checkbutton.pack(pady=5)

                # Required Keyword Entry
                ttk.Label(self, text="Required Keyword:").pack(pady=5)
                self.require_word_var = tk.StringVar(value=self.shortcut["requireWord"])
                self.require_word_entry = ttk.Entry(self, textvariable=self.require_word_var)
                self.require_word_entry.pack(pady=5, fill='x', padx=10)

                # Add/Edit Button
                action_button = ttk.Button(self, text="Edit" if command else "Add", command=self.on_add_edit)
                action_button.pack(pady=10)

                # Bind Enter key to add/edit action
                self.bind('<Return>', lambda event: self.on_add_edit())

                # Focus on command entry
                self.command_entry.focus_set()
            except Exception as e:
                logging.error(f"Error initializing AddShortcutDialog: {e}")

        def on_shortcut_keyrelease(self, event):
            """Handle key release in shortcut entry to provide autocomplete suggestions."""
            try:
                current_text = self.execute_var.get()
                suggestions = [s for s in self.get_shortcut_suggestions() if s.startswith(current_text)]
                if suggestions:
                    self.show_autocomplete_menu(suggestions)
                else:
                    self.hide_autocomplete_menu()
            except Exception as e:
                logging.error(f"Error handling shortcut key release: {e}")

        def get_shortcut_suggestions(self):
            """Return a list of possible shortcut suggestions."""
            return [
                "[ctrl]",
                "[shift]",
                "[alt]",
                "[ctrl] + [c]",
                "[ctrl] + [v]",
                "[ctrl] + [s]",
                "[alt] + [f4]",
                "[shift] + [ctrl] + [s]",
                "<hello world>",
                "<goodbye>",
                "[ctrl] + [a]",
                "[ctrl] + [z]"
                # Add more predefined or common shortcuts as needed
            ]

        def show_autocomplete_menu(self, suggestions):
            """Display the autocomplete suggestions in a dropdown menu."""
            if not hasattr(self, 'autocomplete_menu'):
                self.autocomplete_menu = tk.Menu(self, tearoff=0)
            else:
                self.autocomplete_menu.delete(0, tk.END)

            for suggestion in suggestions:
                self.autocomplete_menu.add_command(
                    label=suggestion,
                    command=lambda s=suggestion: self.select_autocomplete(s)
                )

            # Get the position of the execute_entry
            x = self.execute_entry.winfo_rootx()
            y = self.execute_entry.winfo_rooty() + self.execute_entry.winfo_height()
            self.autocomplete_menu.post(x, y)

        def hide_autocomplete_menu(self):
            """Hide the autocomplete suggestions menu."""
            if hasattr(self, 'autocomplete_menu'):
                self.autocomplete_menu.unpost()

        def select_autocomplete(self, suggestion):
            """Insert the selected autocomplete suggestion into the shortcut entry."""
            self.execute_var.set(suggestion)
            self.hide_autocomplete_menu()
            self.execute_entry.focus_set()

        def on_add_edit(self):
            """Handle the addition or editing of a shortcut."""
            command = self.command_var.get().strip()
            description = self.description_var.get().strip()
            execute = self.execute_var.get().strip()
            enable = self.enable_var.get()
            require_word = self.require_word_var.get().strip()

            if not command or not execute:
                logging.warning("Both Voice Command and Keyboard Shortcut are required.")
                tk.messagebox.showwarning("Input Error", "Both Voice Command and Keyboard Shortcut are required.")
                return

            if self.command and self.command != command:
                # If editing and the command has changed, remove the old command
                if self.command in self.master.settings.get("shortcuts", {}):
                    del self.master.settings["shortcuts"][self.command]

            if command in self.master.settings.get("shortcuts", {}):
                logging.warning(f"Command '{command}' already exists.")
                tk.messagebox.showwarning("Duplicate Command", f"Command '{command}' already exists.")
                return

            # Add or update the shortcut in settings
            self.master.settings["shortcuts"][command] = {
                "description": description,
                "execute": execute,
                "enable": enable,
                "requireWord": require_word
            }
            self.master.load_shortcuts()
            self.master.save_settings()
            logging.info(f"{'Edited' if self.command else 'Added'} shortcut: {command} -> {execute}")
            self.destroy()

        def on_close(self):
            try:
                self.destroy()
            except Exception as e:
                logging.error(f"Error closing AddShortcutDialog: {e}")
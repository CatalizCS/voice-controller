import logging
import tkinter as tk
from tkinter import ttk
import pyaudio
import wave
from audio.device_manager import list_input_devices, get_device_sample_rate
import threading
import numpy as np  # Add import for NumPy

class DeviceSettings(tk.Toplevel):
    def __init__(self, master, settings):
        super().__init__(master)
        try:
            self.settings = settings
            self.title("Device Settings")
            self.geometry("400x400")  # Resize the window
            self.resizable(True, True)  # Allow resizing
            self.test_device_window = None  # Reference to Test Device window
            self.create_widgets()
            self.create_device_list_button()
            self.testing_device = False  # Flag to track testing state
            self.periodic_update()  # Add periodic update
        except Exception as e:
            logging.error(f"Error initializing DeviceSettings: {e}")

    def create_widgets(self):
        device_label = ttk.Label(self, text="Input Device:")
        device_label.pack(pady=5)
        self.device_var = tk.StringVar(value=self.settings.get("last_device_name", ""))
        devices = list_input_devices()
        device_names = [name for _, name in devices]
        self.device_dict = {name: index for index, name in devices}  # Store the mapping
        device_combobox = ttk.Combobox(self, textvariable=self.device_var, values=device_names, state="readonly")
        device_combobox.pack(pady=5)
        device_combobox.bind("<<ComboboxSelected>>", self.on_device_selected)  # Bind selection event

        sensitivity_label = ttk.Label(self, text="Microphone Sensitivity:")
        sensitivity_label.pack(pady=5)
        self.sensitivity_var = tk.DoubleVar(value=self.settings.get("sensitivity", 1.0))
        sensitivity_scale = ttk.Scale(self, from_=0.0, to=2.0, variable=self.sensitivity_var)
        sensitivity_scale.pack(pady=5)

        noise_label = ttk.Label(self, text="Noise Reduction:")
        noise_label.pack(pady=5)
        self.noise_var = tk.DoubleVar(value=self.settings.get("noise_reduction", 1.0))
        noise_scale = ttk.Scale(self, from_=0.0, to=2.0, variable=self.noise_var)
        noise_scale.pack(pady=5)

        # Replace Language Selection Entry with Droplist
        language_label = ttk.Label(self, text="Recognition Language:")
        language_label.pack(pady=5)
        self.language_var = tk.StringVar(value=self.settings.get("language", "en-US"))

        # Define supported languages
        supported_languages = [
            ("Auto (Default)", ""),
            ("English (United States)", "en-US"),
            ("Spanish (Spain)", "es-ES"),
            ("French (France)", "fr-FR"),
            ("German (Germany)", "de-DE"),
            ("Chinese (Mandarin)", "zh-CN"),
            ("Japanese", "ja-JP"),
            ("Korean", "ko-KR"),
            ("Portuguese (Brazil)", "pt-BR"),
            ("Vietnamese (Vietnam)", "vi-VN")
            # Add more languages as needed
        ]

        # Create a list of language display names
        language_options = [lang[0] for lang in supported_languages]

        # Create a mapping from display names to language codes
        self.language_mapping = {lang[0]: lang[1] for lang in supported_languages}

        # Modify the language_combobox by removing the 'height' parameter
        language_combobox = ttk.Combobox(
            self, 
            textvariable=self.language_var, 
            values=language_options, 
            state="readonly"
            # Removed height=10
        )
        language_combobox.pack(pady=5)
        language_combobox.set(
            "Auto (Default)" if self.settings.get("language", "") == "" else next(
                (name for name, code in supported_languages if code == self.settings.get("language")), "Auto (Default)"
            )
        )

        test_button = ttk.Button(self, text="Test Device", command=self.test_device)
        self.test_button = test_button  # Store button reference
        test_button.pack(pady=10)

        save_button = ttk.Button(self, text="Save Settings", command=self.save_settings)
        save_button.pack(pady=10)

    def create_device_list_button(self):
        device_list_button = ttk.Button(self, text="List Input Devices", command=self.list_devices)
        device_list_button.pack(pady=10)

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

    def test_device(self):
        if self.testing_device:
            logging.warning("Device test is already running.")
            return  # Prevent starting another test
        self.testing_device = True  # Set the flag
        self.test_button.config(state='disabled')  # Disable the button
        threading.Thread(target=self._test_device, daemon=True).start()

    def _test_device(self):
        frames = []  # Initialize frames to an empty list
        try:
            p = pyaudio.PyAudio()
            device_name = self.device_var.get()
            device_id = self.device_dict.get(device_name, None)  # Get the device index
            if device_id is None:
                logging.error(f"Device '{device_name}' not found.")
                return
            sample_rate = get_device_sample_rate(device_id)
            channels = p.get_device_info_by_index(device_id)["maxInputChannels"]  # Get the max input channels
            if channels < 1:
                logging.error(f"Invalid number of audio channels: {channels}")
                return
            stream = p.open(
                format=pyaudio.paInt16,
                channels=channels,  # Use the appropriate number of channels
                rate=sample_rate,
                input=True,
                input_device_index=device_id
            )
            for _ in range(0, int(sample_rate / 1024 * 5)):
                data = stream.read(1024)
                frames.append(data)
            stream.stop_stream()
            stream.close()
        except Exception as e:
            logging.error(f"Error testing device: {e}")
        finally:
            p.terminate()
            try:
                if frames:  # Ensure frames is not empty
                    # Convert frames to NumPy array for normalization
                    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)

                    # Normalize the audio to the maximum amplitude
                    max_amp = np.max(np.abs(audio_data))
                    if max_amp == 0:
                        max_amp = 1  # Prevent division by zero
                    normalized_data = (audio_data / max_amp * 32767).astype(np.int16)

                    wf = wave.open("test.wav", 'wb')
                    wf.setnchannels(channels)  # Ensure the number of channels is consistent
                    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                    wf.setframerate(sample_rate)
                    wf.writeframes(normalized_data.tobytes())
                    wf.close()

                    # Playback the normalized audio
                    wf = wave.open("test.wav", 'rb')
                    p = pyaudio.PyAudio()
                    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()), channels=wf.getnchannels(), rate=wf.getframerate(), output=True)
                    data = wf.readframes(1024)
                    while data:
                        stream.write(data)
                        data = wf.readframes(1024)
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
            except Exception as e:
                logging.error(f"Error during audio processing: {e}")
            finally:
                if self.test_button.winfo_exists():  # Check if the button still exists
                    self.testing_device = False  # Reset the flag
                    self.test_button.config(state='normal')  # Re-enable the button

    def save_settings(self):
        try:
            self.settings["last_device_name"] = self.device_var.get()
            self.settings["sensitivity"] = self.sensitivity_var.get() / 2.0  # Scale 0-2 to 0-1
            self.settings["noise_reduction"] = self.noise_var.get() / 2.0  # Scale 0-2 to 0-1
            
            # Save the language code based on selection
            selected_language_display = self.language_var.get()
            self.settings["language"] = self.language_mapping.get(selected_language_display, "en-US")  # Default to en-US
            
            # Set 'language_display' to the selected display name
            self.settings["language_display"] = selected_language_display
            
            # Save settings and update the main application
            self.master.save_settings()
            self.master.restart_voice_recognition()  # Restart voice recognition with new language
            self.master.update_language_display()  # Update language display in main window
            self.destroy()
        except Exception as e:
            logging.error(f"Error saving settings: {e}")

    def periodic_update(self):
        try:
            self.update_idletasks()
            self.after(50, self.periodic_update)  # Schedule the next update
        except Exception as e:
            logging.error(f"Error during periodic update: {e}")

    def on_device_selected(self, event):
        selected_device = self.device_var.get()
        logging.info(f"Selected device: {selected_device}")
        # Update settings or perform other actions based on the selected device

    def update_language_display(self):
        try:
            language_display = self.settings.get("language_display", "English (United States)")
        except Exception as e:
            logging.error(f"Error updating language display: {e}")

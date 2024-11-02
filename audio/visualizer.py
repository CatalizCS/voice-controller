import pyaudio
import numpy as np
import matplotlib
matplotlib.use("TkAgg")  # Use TkAgg backend for compatibility with tkinter
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging
import threading  # Add threading import
import queue  # Add queue import
import tkinter as tk

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    logging.warning("CuPy is not installed. GPU processing is unavailable.")
    CUPY_AVAILABLE = False

def list_input_devices():
    try:
        p = pyaudio.PyAudio()
        devices = []
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                devices.append((i, device_info['name']))
        p.terminate()
        return devices
    except Exception as e:
        logging.error(f"Error listing devices for visualizer: {e}")
        return []

class AudioVisualizer:
    def __init__(self, parent, device_name="", processing_backend="CPU", chunk=1024):
        try:
            self.device_name = device_name
            self.chunk = chunk
            self.processing_backend = processing_backend.upper()
            self.use_gpu = False

            if self.processing_backend == "GPU" and CUPY_AVAILABLE:
                self.use_gpu = True
                logging.info("GPU processing enabled.")

            self.p = pyaudio.PyAudio()
            devices = list_input_devices()
            if self.device_name:
                self.device_index = next((index for index, name in devices if name == self.device_name), None)
                if self.device_index is None:
                    logging.warning(f"Device '{self.device_name}' not found. Using default device.")
                    self.device_index = devices[0][0] if devices else None
            else:
                self.device_index = devices[0][0] if devices else None

            if self.device_index is None:
                logging.error("No valid input devices found.")
                return

            device_info = self.p.get_device_info_by_index(self.device_index)
            self.rate = int(device_info["defaultSampleRate"])
            self.channels = device_info["maxInputChannels"]

            # Initialize Matplotlib figure and axis in the main thread
            self.fig, self.ax = plt.subplots()
            self.line, = self.ax.plot(np.zeros(self.chunk))
            self.ax.set_ylim(-32768, 32767)
            self.ax.set_xlim(0, self.chunk)

            self.queue = queue.Queue()
            self.running = False
            self.audio_thread = None

            # Configure the parent frame to allow the canvas to expand
            parent.rowconfigure(0, weight=1)
            parent.columnconfigure(0, weight=1)

            # Embed the plot into the Tkinter parent frame using grid
            self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
            self.canvas.draw()
            self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')  # Changed from pack to grid

            # Initialize animation
            self.ani = animation.FuncAnimation(
                self.fig, self.update_plot, interval=50, blit=True, save_count=100
            )
            logging.info("AudioVisualizer initialized and embedded in Tkinter frame.")

        except Exception as e:
            logging.error(f"Error initializing AudioVisualizer: {e}")

    def start(self):
        try:
            self.running = True
            # Start the audio processing in a separate thread
            self.audio_thread = threading.Thread(target=self.read_audio_data, daemon=True)
            self.audio_thread.start()
        except Exception as e:
            logging.error(f"Error starting AudioVisualizer: {e}")

    def read_audio_data(self):
        try:
            # Open audio stream
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk
            )
            while self.running:
                data = self.stream.read(self.chunk)
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Convert to mono if multiple channels are present
                if self.channels > 1:
                    audio_data = audio_data.reshape(-1, self.channels)
                    audio_data = audio_data.mean(axis=1).astype(np.int16)
                    logging.debug(f"Converted to mono. Shape: {audio_data.shape}")
                else:
                    logging.debug(f"Mono audio data received. Shape: {audio_data.shape}")
                
                self.queue.put(audio_data)
        except Exception as e:
            logging.error(f"Error in AudioVisualizer read_audio_data: {e}")
            self.running = False  # Stop if there's an error
        finally:
            self.stop()

    def update_plot(self, frame):
        try:
            if not self.queue.empty():
                audio_data = self.queue.get_nowait()
                self.line.set_ydata(audio_data)
            return self.line,
        except Exception as e:
            logging.error(f"Error updating plot: {e}")

    def stop(self):
        try:
            self.running = False
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join()
            self.p.terminate()
            if hasattr(self, 'stream') and self.stream.is_active():
                self.stream.stop_stream()
                self.stream.close()
            self.p.terminate()
            plt.close(self.fig)
            logging.info("Visualizer stopped.")
        except Exception as e:
            logging.error(f"Error stopping AudioVisualizer: {e}")

            plt.close(self.fig)
            logging.info("Visualizer stopped.")
        except Exception as e:
            logging.error(f"Error stopping AudioVisualizer: {e}")

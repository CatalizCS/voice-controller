import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import logging
import threading  # Add threading import

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
    def __init__(self, device_name="", processing_backend="CPU", chunk=1024):
        try:
            self.device_name = device_name
            self.chunk = chunk
            self.processing_backend = processing_backend.upper()
            self.use_gpu = False

            if self.processing_backend == "GPU":
                if CUPY_AVAILABLE:
                    self.use_gpu = True
                    logging.info("GPU processing enabled for AudioVisualizer.")
                else:
                    logging.warning("CuPy is not installed or GPU is unavailable. Falling back to CPU processing.")
                    self.processing_backend = "CPU"

            self.p = pyaudio.PyAudio()
            devices = list_input_devices()
            if self.device_name:
                self.device_index = next((index for index, name in devices if name == self.device_name), 0)
            else:
                self.device_index = 0  # Default device

            device_info = self.p.get_device_info_by_index(self.device_index)
            self.rate = int(device_info["defaultSampleRate"])
            self.channels = device_info["maxInputChannels"]  # Ensure the number of channels is consistent
            self.stream = self.p.open(format=pyaudio.paInt16, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk, input_device_index=self.device_index)
            self.fig, self.ax = plt.subplots()
            self.x = np.arange(0, 2 * self.chunk, 2)
            self.line, = self.ax.plot(self.x, np.random.rand(self.chunk))
            self.ax.set_ylim(-32768, 32767)
            self.ax.set_xlim(0, self.chunk)
        except Exception as e:
            logging.error(f"Error initializing AudioVisualizer: {e}")
            self.stream = None

    def update(self, frame):
        try:
            if self.stream is None:
                return self.line,

            data = np.frombuffer(self.stream.read(self.chunk), dtype=np.int16)

            if self.use_gpu:
                # Transfer data to GPU using CuPy
                data_gpu = cp.asarray(data)
                # Example: perform FFT on GPU
                fft_gpu = cp.fft.fft(data_gpu)
                fft_magnitude = cp.abs(fft_gpu)
                # Transfer back to CPU
                fft_magnitude_cpu = cp.asnumpy(fft_magnitude)
                self.line.set_ydata(fft_magnitude_cpu)
            else:
                # CPU processing using NumPy
                fft = np.fft.fft(data)
                fft_magnitude = np.abs(fft)
                self.line.set_ydata(fft_magnitude)

            return self.line,
        except Exception as e:
            logging.error(f"Error updating visualizer: {e}")
            return self.line,

    def start(self):
        try:
            def run_visualizer():
                ani = animation.FuncAnimation(self.fig, self.update, interval=50, blit=True, cache_frame_data=False)
                plt.show()
            # Ensure the visualizer runs in the main thread
            if threading.current_thread() is threading.main_thread():
                run_visualizer()
            else:
                self.fig.canvas.manager.window.after(0, run_visualizer)
        except Exception as e:
            logging.error(f"Error starting visualizer animation: {e}")

    def stop(self):
        try:
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
            self.p.terminate()
        except Exception as e:
            logging.error(f"Error stopping AudioVisualizer: {e}")

import pyaudio
import logging

def list_input_devices():
    try:
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        devices = []
        for i in range(device_count):
            device_info = p.get_device_info_by_index(i)
            if device_info["maxInputChannels"] > 0:
                devices.append((i, device_info["name"]))
        p.terminate()
        logging.info(f"Found {len(devices)} input devices.")
        return devices
    except Exception as e:
        logging.error(f"Error listing input devices: {e}")
        return []

def get_device_sample_rate(device_index):
    try:
        p = pyaudio.PyAudio()
        device_info = p.get_device_info_by_index(device_index)
        sample_rate = int(device_info["defaultSampleRate"])
        p.terminate()
        logging.info(f"Sample rate for device {device_index}: {sample_rate}")
        return sample_rate
    except Exception as e:
        logging.error(f"Error retrieving sample rate for device {device_index}: {e}")
        try:
            p.terminate()
        except:
            pass
        return 44100  # Fallback to a common sample rate

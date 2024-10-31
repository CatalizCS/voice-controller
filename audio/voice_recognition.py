# voice_recognition.py
import speech_recognition as sr
import logging
import threading
from config.settings import load_settings
from utils.keyboard_controller import execute_shortcut
from audio.device_manager import list_input_devices, get_device_sample_rate
import collections
import numpy as np  # Add import for NumPy
import base64  # Add import for base64

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    logging.warning("CuPy is not installed. GPU processing is unavailable for voice recognition.")
    CUPY_AVAILABLE = False

recognition_running = False

def stop_voice_recognition():
    global recognition_running
    logging.info("Stopping voice recognition.")
    recognition_running = False

def apply_noise_reduction(audio_data, noise_reduction_level):
    # Simple noise reduction algorithm (placeholder)
    # This can be replaced with a more sophisticated algorithm if needed
    return audio_data * (1 - noise_reduction_level)

def normalize_audio(audio_data):
    max_amp = np.max(np.abs(audio_data))
    if max_amp == 0:
        max_amp = 1  # Prevent division by zero
    return (audio_data / max_amp * 32767).astype(np.int16)

def voice_recognition(settings):
    global recognition_running
    recognition_running = True
    recognizer = sr.Recognizer()
    devices = list_input_devices()
    if not devices:
        logging.error("No input devices found.")
        recognition_running = False
        return

    min_audio_length = settings.get("min_audio_length", 1)
    max_audio_length = settings.get("max_audio_length", 10)
    sensitivity = settings.get("sensitivity", 1.0)  # Sensitivity ranges from 0 to 1
    noise_reduction_level = settings.get("noise_reduction", 1.0)  # Noise reduction level ranges from 0 to 1
    processing_backend = settings.get("processing_backend", "CPU").upper()
    use_gpu = False

    if processing_backend == "GPU":
        if CUPY_AVAILABLE:
            use_gpu = True
            logging.info("GPU processing enabled for voice recognition.")
        else:
            logging.warning("CuPy is not installed or GPU is unavailable. Falling back to CPU processing.")
            processing_backend = "CPU"

    try:
        device_name = settings.get("last_device_name", "")
        device_index = next((index for index, name in devices if name == device_name), None)
        if device_index is None:
            if devices:
                device_index = devices[0][0]
                logging.warning(f"Device '{device_name}' not found. Using default device: '{devices[0][1]}'")
            else:
                logging.error("No input devices available.")
                recognition_running = False
                return
        sample_rate = get_device_sample_rate(device_index)
        mic = sr.Microphone(device_index=device_index, sample_rate=sample_rate)
        with mic as source:
            logging.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1.0)  # Use a fixed duration for ambient noise adjustment
            logging.info("Ambient noise adjustment complete.")
        
        logging.info("Listening started.")
        audio_buffer = collections.deque(maxlen=int(sample_rate * max_audio_length))

        while recognition_running:
            try:
                with mic as source:
                    logging.info("Listening for audio...")
                    audio_chunk = recognizer.listen(source, timeout=min_audio_length + 5, phrase_time_limit=None)
                    audio_buffer.extend(audio_chunk.get_raw_data())
                    
                    if len(audio_buffer) >= sample_rate * min_audio_length:
                        audio_data = sr.AudioData(bytes(audio_buffer), sample_rate, 2)
                        
                        # Convert audio data to NumPy array for processing
                        audio_array = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
                        
                        # Apply volume adjustment
                        audio_array = audio_array * sensitivity
                        logging.info(f"Volume adjusted with sensitivity: {sensitivity}")
                        
                        # Apply noise reduction
                        audio_array = apply_noise_reduction(audio_array, noise_reduction_level)
                        logging.info(f"Noise reduction applied with level: {noise_reduction_level}")
                        
                        # Normalize audio
                        audio_array = normalize_audio(audio_array)
                        logging.info("Audio normalized.")
                        
                        # Convert back to AudioData
                        audio_data = sr.AudioData(audio_array.tobytes(), sample_rate, 2)
                        
                        language = settings.get("language", "en-US")
                        logging.info(f"Using language: {language}")
                        
                        # Save audio to file for debugging
                        with open("debug_audio.wav", "wb") as f:
                            f.write(audio_data.get_wav_data())
                        
                        command = recognizer.recognize_google(audio_data, language=language)
                        logging.info(f"Recognized command: {command}")
                        
                        if settings.get("enable_shortcuts", True):
                            for cmd, shortcut in settings.get("shortcuts", {}).items():
                                if shortcut["enable"] and cmd.lower() in command.lower():
                                    if shortcut["requireWord"] and not command.lower().startswith(shortcut["requireWord"].lower()):
                                        logging.warning(f"Command does not start with the required keyword: {shortcut['requireWord']}")
                                        continue
                                    logging.info(f"Executing shortcut for command '{cmd}': {shortcut['execute']}")
                                    execute_shortcut(shortcut["execute"])
                                    break
                            else:
                                logging.warning(f"No matching shortcut found for recognized command: {command}")
                        else:
                            logging.info("Shortcuts are disabled.")
                        audio_buffer.clear()
            except sr.WaitTimeoutError:
                logging.warning("Listening timed out while waiting for phrase to start.")
            except sr.UnknownValueError:
                logging.warning("Could not understand audio.")
                audio_buffer.clear()
            except sr.RequestError as e:
                logging.error(f"Recognition service error: {e}")
                break
            except Exception as e:
                logging.error(f"Unexpected error in listen_loop: {e}")
                break
    except Exception as e:
        logging.error(f"Error initializing voice recognition: {e}")
    finally:
        recognition_running = False
        logging.info("Voice recognition stopped.")
# keyboard_controller.py
import keyboard
import logging
import time
import re
import base64  # Add import for base64

def execute_shortcut(shortcut):
    try:
        parts = [part.strip() for part in shortcut.split('+')]
        modifiers = []
        keys = []
        strings = []
        
        for part in parts:
            # Check for modifier keys like [ctrl], [shift], [alt]
            modifier_match = re.match(r'\[(.*?)\]', part)
            if modifier_match:
                modifier = modifier_match.group(1).lower()
                modifiers.append(modifier)
                continue
            
            # Check for typing strings like <hello world>
            string_match = re.match(r'<(.*?)>', part)
            if string_match:
                string_to_type = string_match.group(1)
                strings.append(string_to_type)
                continue
            
            # Check for single keys like [a], [s], [1], etc.
            key_match = re.match(r'\[(.*?)\]', part)
            if key_match:
                key = key_match.group(1).lower()
                keys.append(key)
                continue
        
        # Press and hold modifier keys
        for mod in modifiers:
            keyboard.press(mod)
        
        # Execute key presses
        for key in keys:
            keyboard.press_and_release(key)
            time.sleep(0.05)  # Small delay between key presses
        
        # Type out strings
        for string in strings:
            keyboard.write(string)
            time.sleep(0.05)  # Small delay between typing
        
        # Release modifier keys
        for mod in reversed(modifiers):
            keyboard.release(mod)
        
        time.sleep(0.1)  # Add a small delay after executing shortcuts
        logging.info(f"Executed shortcut: {shortcut}")
    except Exception as e:
        logging.error(f"Error executing shortcut '{shortcut}': {e}")
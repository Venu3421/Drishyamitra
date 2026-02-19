
try:
    print("Attempting to import pywhatkit...")
    import pywhatkit
    print("SUCCESS: pywhatkit imported.")
except ImportError as e:
    print(f"ERROR: pywhatkit failed to import: {e}")
except Exception as e:
    print(f"ERROR: pywhatkit raised unexpected error: {e}")

try:
    print("Attempting to import pyautogui...")
    import pyautogui
    print("SUCCESS: pyautogui imported.")
except ImportError as e:
    print(f"ERROR: pyautogui failed to import: {e}")
except Exception as e:
    print(f"ERROR: pyautogui raised unexpected error: {e}")

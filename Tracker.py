import cv2
import mediapipe as mp
import pydirectinput
from pynput import keyboard

# Global tracking variable
system_enabled = False

# Dictionary to track key states dynamically
states = {
    'index':  [False, False],
    'middle': [False, False],
    'ring':   [False, False],
    'pinky':  [False, False]
}

finger_keys = {
    'index':  {'top': 'u', 'bot': 'j'},
    'middle': {'top': 'y', 'bot': 'h'},
    'ring':   {'top': 't', 'bot': 'g'},
    'pinky':  {'top': 'r', 'bot': 'f'}
}
def release_all_keys():
    """Safety function to release all keys when system is toggled off or exits."""
    for finger, state in states.items():
        if state[0]:
            pydirectinput.keyUp(finger_keys[finger]['top'])
            states[finger][0] = False
        if state[1]:
            pydirectinput.keyUp(finger_keys[finger]['bot'])
            states[finger][1] = False

def on_press(key):
    """Listens globally for the F8 key to toggle the system."""
    global system_enabled
    try:
        if key == keyboard.Key.f8:
            system_enabled = not system_enabled
            if not system_enabled:
                release_all_keys()
                print(">>> SYSTEM DISABLED (Keys Paused) <<<")
            else:
                print(">>> SYSTEM ENABLED (Controlling Keyboard) <<<")
    except AttributeError:
        pass

# Start the background keyboard listener for the toggle hotkey
listener = keyboard.Listener(on_press=on_press)
listener.start()

def handle_finger_input(finger_name, is_curled):
    """Handles direct hardware press/release logic if system is enabled."""
    if not system_enabled:
        return

    top_key = finger_keys[finger_name]['top']
    bot_key = finger_keys[finger_name]['bot']
    
    if is_curled:
        if not states[finger_name][0]:  
            if states[finger_name][1]:  
                pydirectinput.keyUp(bot_key)
                states[finger_name][1] = False
            pydirectinput.keyDown(top_key)
            states[finger_name][0] = True
    else:
        if not states[finger_name][1]:  
            if states[finger_name][0]:  
                pydirectinput.keyUp(top_key)
                states[finger_name][0] = False
            pydirectinput.keyDown(bot_key)
            states[finger_name][1] = True

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

print("--------------------------------------------------")
print("Press F8 anywhere on your computer to toggle tracking ON/OFF!")
print("Status: DISABLED (Press F8 to activate)")
print("--------------------------------------------------")

with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Finger tracking logic
                index_pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                handle_finger_input('index', index_tip.y > index_pip.y)
                
                middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
                middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                handle_finger_input('middle', middle_tip.y > middle_pip.y)
                
                ring_pip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP]
                ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
                handle_finger_input('ring', ring_tip.y > ring_pip.y)
                
                pinky_pip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP]
                pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
                handle_finger_input('pinky', pinky_tip.y > pinky_pip.y)

                y_offset = 40
                status_str = "yea" if system_enabled else "nah press f8"
                status_color = (0, 255, 0) if system_enabled else (0, 0, 255)
                
                cv2.putText(frame, f"yo is this working?: {status_str}", (20, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                y_offset += 35

                if system_enabled:
                    for finger, state in states.items():
                        active_key = finger_keys[finger]['top'] if state[0] else finger_keys[finger]['bot']
                        cv2.putText(frame, f"{finger.upper()}: {active_key.upper()}", (20, y_offset), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        y_offset += 25

        cv2.imshow('cool thingy', frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

release_all_keys()
listener.stop()
cap.release()
cv2.destroyAllWindows()

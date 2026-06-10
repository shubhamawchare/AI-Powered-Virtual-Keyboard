import cv2
import mediapipe as mp
import numpy as np
import math
import threading
import time
from datetime import datetime

#  Clipboard 
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    print("[INFO] pip install pyperclip  (clipboard disabled)")

#  Sound 
try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    _n    = int(44100 * 0.04)
    _t    = np.linspace(0, 0.04, _n, False)
    _mono = (np.sin(2 * np.pi * 800 * _t) * 0.4 * 32767).astype(np.int16)
    _mono = (_mono * np.linspace(1.0, 0.0, _n)).astype(np.int16)
    _wave = np.column_stack((_mono, _mono))
    click_sound     = pygame.sndarray.make_sound(_wave)
    SOUND_AVAILABLE = True
except Exception as err:
    SOUND_AVAILABLE = False
    print(f"[INFO] Sound disabled: {err}")

#  Speech 
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("[INFO] pip install SpeechRecognition pyaudio  (voice disabled)")



#  Colors

COL_DARK_PURPLE = (120,   0, 120)
COL_GREEN       = (  0, 200,  50)
COL_RED         = (  0,  40, 220)
COL_CYAN        = (220, 200,   0)
COL_GOLD        = ( 30, 180, 210)
COL_WHITE       = (255, 255, 255)
COL_BLACK       = (  0,   0,   0)
COL_ORANGE      = ( 20, 130, 240)
COL_DARK_BG     = ( 40,   5,  60)
COL_PURPLE      = (200,  40, 200)
COL_TEAL        = (  0, 160, 160)

FRAME_W, FRAME_H = 1280, 720



#  Button

class Button:
    def __init__(self, pos, text, size=None):
        self.pos  = list(pos)
        self.size = list(size) if size else [65, 60]
        self.text = text



#  Layout

ROWS = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["Z","X","C","V","B","N","M"]
]

def build_buttons():
    btns = []
    step = 70
    for i, row in enumerate(ROWS):
        for j, key in enumerate(row):
            x = step * j + 50
            if i == 2: x = step * j + 85
            if i == 3: x = step * j + 155
            btns.append(Button([x, step * i + 30], key))
    btns.append(Button([50,  320], "SPACE", [260, 60]))
    btns.append(Button([325, 320], "BACK",  [125, 60]))
    btns.append(Button([465, 320], "CAPS",  [105, 60]))
    btns.append(Button([585, 320], "COPY",  [105, 60]))
    btns.append(Button([705, 320], "SAVE",  [105, 60]))
    btns.append(Button([825, 320], "CLEAR", [105, 60]))
    btns.append(Button([945, 320], "VOICE", [120, 60]))
    return btns

button_list = build_buttons()



#  MediaPipe  (up to 2 hands)

mp_hands = mp.solutions.hands
hands    = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75
)
mp_draw = mp.solutions.drawing_utils



#  State

final_text      = ""
click_delay     = 0
caps_lock       = False
voice_mode      = False
voice_listening = False
gesture_delay   = 0
status_msg      = ""
status_timer    = 0



#  Helper functions

def point_dist(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def get_finger_states(lm):
    """
    Returns [thumb_up, index_up, middle_up, ring_up, pinky_up].
    Uses Y-axis for all fingers (tip above PIP = extended).
    Thumb uses X-axis relative to index MCP for reliability.
    """
    # Thumb: tip x further from palm center than IP joint
    thumb_up = abs(lm[4][0] - lm[9][0]) > abs(lm[3][0] - lm[9][0])
    fingers  = [thumb_up]
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        fingers.append(lm[tip][1] < lm[pip][1])
    return fingers


def is_thumbs_up(lm, fingers):
    """
    Strict thumbs-up: thumb extended AND all 4 fingers fully curled
    (fingertips must be BELOW their MCP knuckle, not just PIP).
    """
    if not fingers[0]:
        return False
    # All finger tips must be below their MCP (base knuckle) = fully curled
    for tip, mcp in [(8, 5), (12, 9), (16, 13), (20, 17)]:
        if lm[tip][1] < lm[mcp][1] + 15:   
            return False
    return True


def is_peace_sign(lm, fingers):
    """Index + Middle up, Ring + Pinky down, Thumb down."""
    return (fingers[1] and fingers[2]
            and not fingers[3] and not fingers[4]
            and not fingers[0])


def set_status(msg, frames=80):
    global status_msg, status_timer
    status_msg   = msg
    status_timer = frames


def play_click():
    if SOUND_AVAILABLE:
        try:
            click_sound.play()
        except Exception:
            pass


def do_copy():
    if not final_text:
        set_status("Nothing to copy!")
        return
    if not CLIPBOARD_AVAILABLE:
        set_status("Install pyperclip first!")
        return
    pyperclip.copy(final_text)
    set_status("Copied to clipboard!")


def do_save():
    if not final_text:
        set_status("Nothing to save!")
        return
    fname = f"typed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(fname, "w", encoding="utf-8") as fp:
            fp.write(final_text)
        set_status(f"Saved: {fname}")
    except Exception as e:
        set_status(f"Save failed: {str(e)[:28]}")


def handle_key(key):
    global final_text, caps_lock, voice_mode
    play_click()
    if   key == "SPACE": final_text += " "
    elif key == "BACK":  final_text  = final_text[:-1] if final_text else ""
    elif key == "CLEAR": final_text  = ""; set_status("Cleared!")
    elif key == "CAPS":
        caps_lock = not caps_lock
        set_status("CAPS ON" if caps_lock else "caps off")
    elif key == "COPY":  do_copy()
    elif key == "SAVE":  do_save()
    elif key == "VOICE":
        if not voice_mode and not voice_listening:
            voice_mode = True
            threading.Thread(target=listen_voice, daemon=True).start()
    else:
        final_text += key if caps_lock else key.lower()



#  Voice input

def listen_voice():
    global final_text, voice_listening, voice_mode
    if not SPEECH_AVAILABLE:
        set_status("SpeechRecognition not installed!")
        voice_mode = False
        return
    voice_listening = True
    set_status("Listening... speak now", 150)
    rec = sr.Recognizer()
    rec.energy_threshold         = 300
    rec.dynamic_energy_threshold = True
    try:
        with sr.Microphone() as source:
            rec.adjust_for_ambient_noise(source, duration=0.5)
            audio = rec.listen(source, timeout=5, phrase_time_limit=5)
        spoken      = rec.recognize_google(audio)
        word        = spoken.upper() if caps_lock else spoken.lower()
        final_text += word + " "
        set_status(f"Heard: {spoken}")
    except sr.WaitTimeoutError:
        set_status("No speech detected")
    except sr.UnknownValueError:
        set_status("Could not understand")
    except Exception as e:
        set_status(f"Voice error: {str(e)[:35]}")
    finally:
        voice_listening = False
        voice_mode      = False



#  Drawing helpers

def draw_rounded_rect(img, pt1, pt2, color, radius=10,
                      filled=True, border=None, border_thick=2):
    x1, y1 = pt1
    x2, y2 = pt2
    r = max(2, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
    if filled and color:
        cv2.rectangle(img, (x1+r, y1),   (x2-r, y2),   color, -1)
        cv2.rectangle(img, (x1,   y1+r), (x2,   y2-r), color, -1)
        for cx, cy in [(x1+r, y1+r), (x2-r, y1+r),
                       (x1+r, y2-r), (x2-r, y2-r)]:
            cv2.circle(img, (cx, cy), r, color, -1)
    if border:
        cv2.rectangle(img, (x1+r, y1),   (x2-r, y2),   border, border_thick)
        cv2.rectangle(img, (x1,   y1+r), (x2,   y2-r), border, border_thick)
        for (cx, cy), ang in [((x1+r, y1+r), 180), ((x2-r, y1+r), 270),
                               ((x1+r, y2-r),  90), ((x2-r, y2-r),   0)]:
            cv2.ellipse(img, (cx, cy), (r, r), 0,
                        ang, ang + 90, border, border_thick)


def draw_button(img, btn, state="normal"):
    x, y = btn.pos
    w, h = btn.size
    text = btn.text

    if   state == "hover":    color = COL_GREEN
    elif state == "click":    color = COL_RED
    elif state == "voice_on": color = (20, 140, 20)
    elif state == "caps_on":  color = (0, 140, 140)
    elif text in "1234567890": color = (60, 20, 100)
    elif text in ("SPACE", "BACK", "CAPS", "COPY",
                  "SAVE",  "CLEAR", "VOICE"):
                              color = (90, 10, 140)
    else:                     color = COL_DARK_PURPLE

    draw_rounded_rect(img, (x, y), (x+w, y+h), color, radius=10)
    border_col = COL_WHITE if state in ("normal", "caps_on", "voice_on") \
                           else COL_BLACK
    draw_rounded_rect(img, (x, y), (x+w, y+h), None, radius=10,
                      filled=False, border=border_col, border_thick=2)

    # Letter keys show lowercase when caps_lock is off
    label = text
    if len(text) == 1 and text.isalpha():
        label = text if caps_lock else text.lower()

    fs = 1.25 if len(label) == 1 else 0.72
    tw = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, fs, 2)[0][0]
    tx = x + (w - tw) // 2
    ty = y + h // 2 + 8
    cv2.putText(img, label, (tx, ty),
                cv2.FONT_HERSHEY_DUPLEX, fs, COL_WHITE, 2, cv2.LINE_AA)



#  Webcam

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)

print("===========================================")
print("  Virtual Keyboard  Enhanced Edition")
print("===========================================")
print("  Single hand : hover index + pinch thumb")
print("  Two hands   : 1 hand hovers, other pinches")
print("  Thumbs Up   : clear text (hold 1s)")
print("  Peace Sign  : voice input")
print("  Buttons: CAPS  COPY  SAVE  CLEAR  VOICE")
print("  ESC to quit")
print("===========================================")

prev_time = time.time()



#  MAIN LOOP

while True:
    ok, img = cap.read()
    if not ok:
        break

    img = cv2.resize(img, (FRAME_W, FRAME_H))
    img = cv2.flip(img, 1)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    # Collect up to 2 hand landmark lists + labels
    hand_lms    = []   # list of landmark lists
    hand_labels = []   # "Left" or "Right" per hand 

    if res.multi_hand_landmarks and res.multi_handedness:
        for hlm, hnd in zip(res.multi_hand_landmarks,
                             res.multi_handedness):
            H, W, _ = img.shape
            lm = [(int(l.x * W), int(l.y * H)) for l in hlm.landmark]
            hand_lms.append(lm)
            hand_labels.append(hnd.classification[0].label)
            mp_draw.draw_landmarks(
                img, hlm, mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=COL_CYAN,  thickness=2, circle_radius=3),
                mp_draw.DrawingSpec(color=COL_GREEN, thickness=2)
            )

    # Draw keyboard buttons
    for btn in button_list:
        state = ("caps_on"  if btn.text == "CAPS"  and caps_lock  else
                 "voice_on" if btn.text == "VOICE" and voice_mode else
                 "normal")
        draw_button(img, btn, state)

    
    if len(hand_lms) == 2:
        hover_lm = None
        pinch_lm = None
        for lm, label in zip(hand_lms, hand_labels):
            if label == "Right":   
                hover_lm = lm
            else:                  
                pinch_lm = lm

        # Fallback: if both same label just assign by index
        if hover_lm is None or pinch_lm is None:
            hover_lm = hand_lms[0]
            pinch_lm = hand_lms[1]

        hover_ix, hover_iy = hover_lm[8]   # hover index tip
        pinch_ix, pinch_iy = pinch_lm[8]   # pinch index tip
        pinch_tx, pinch_ty = pinch_lm[4]   # pinch thumb tip

        # Draw hover cursor (yellow-cyan) and pinch cursor (cyan)
        cv2.circle(img, (hover_ix, hover_iy), 16, (0, 220, 255), cv2.FILLED)
        cv2.circle(img, (hover_ix, hover_iy), 16, COL_WHITE, 2)
        cv2.circle(img, (pinch_ix, pinch_iy), 12, COL_CYAN,  cv2.FILLED)
        cv2.circle(img, (pinch_ix, pinch_iy), 12, COL_WHITE, 2)

        pinch_d = point_dist((pinch_ix, pinch_iy), (pinch_tx, pinch_ty))

        # Gestures use the PINCH hand
        fp = get_finger_states(pinch_lm)
        if gesture_delay == 0:
            if is_thumbs_up(pinch_lm, fp):
                final_text    = ""
                set_status("Text cleared!")
                gesture_delay = 60
            elif is_peace_sign(pinch_lm, fp) and not voice_mode and not voice_listening:
                voice_mode    = True
                gesture_delay = 60
                threading.Thread(target=listen_voice, daemon=True).start()

        # Key interaction: hover hand selects, pinch hand confirms
        for btn in button_list:
            bx, by = btn.pos
            bw, bh = btn.size
            if bx < hover_ix < bx + bw and by < hover_iy < by + bh:
                st = ("caps_on"  if btn.text == "CAPS"  and caps_lock  else
                      "voice_on" if btn.text == "VOICE" and voice_mode else
                      "hover")
                draw_button(img, btn, st)
                if pinch_d < 38 and click_delay == 0:
                    draw_button(img, btn, "click")
                    handle_key(btn.text)
                    click_delay = 20

    
    #  SINGLE-HAND MODE
    
    elif len(hand_lms) == 1:
        lm = hand_lms[0]
        ix, iy = lm[8]   # index tip
        tx, ty = lm[4]   # thumb tip

        # Draw index tip cursor
        cv2.circle(img, (ix, iy), 14, COL_CYAN,  cv2.FILLED)
        cv2.circle(img, (ix, iy), 14, COL_WHITE, 2)

        pinch_d = point_dist((ix, iy), (tx, ty))

        f = get_finger_states(lm)
        if gesture_delay == 0:
            if is_thumbs_up(lm, f):
                final_text    = ""
                set_status("Text cleared!")
                gesture_delay = 60
            elif is_peace_sign(lm, f) and not voice_mode and not voice_listening:
                voice_mode    = True
                gesture_delay = 60
                threading.Thread(target=listen_voice, daemon=True).start()

        for btn in button_list:
            bx, by = btn.pos
            bw, bh = btn.size
            if bx < ix < bx + bw and by < iy < by + bh:
                st = ("caps_on"  if btn.text == "CAPS"  and caps_lock  else
                      "voice_on" if btn.text == "VOICE" and voice_mode else
                      "hover")
                draw_button(img, btn, st)
                if pinch_d < 38 and click_delay == 0:
                    draw_button(img, btn, "click")
                    handle_key(btn.text)
                    click_delay = 20

    # Cooldowns
    if click_delay   > 0: click_delay   -= 1
    if gesture_delay > 0: gesture_delay -= 1

    
    #  UI PANELS
    

    # Text output box
    draw_rounded_rect(img, (50, 400), (1230, 465), COL_DARK_BG, radius=12)
    draw_rounded_rect(img, (50, 400), (1230, 465), None, radius=12,
                      filled=False, border=COL_PURPLE, border_thick=2)
    cursor  = "_" if int(time.time() * 2) % 2 == 0 else " "
    display = final_text[-52:] if len(final_text) > 52 else final_text
    cv2.putText(img, display + cursor, (65, 445),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, COL_WHITE, 2, cv2.LINE_AA)
    cv2.putText(img, f"{len(final_text)} chars", (1135, 458),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, COL_GOLD, 1, cv2.LINE_AA)

    # Hint bar
    hint = "Pinch=type  |  ThumbsUp=clear  |  PeaceSign=voice"
    cv2.putText(img, hint, (55, 490),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, COL_CYAN, 1, cv2.LINE_AA)

    # Status message
    if status_timer > 0:
        alpha = min(1.0, status_timer / 30.0)
        c = tuple(int(v * alpha) for v in COL_ORANGE)
        cv2.putText(img, status_msg, (55, 518),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, c, 2, cv2.LINE_AA)
        status_timer -= 1

    # Mode badges (top-right corner)
    badges = []
    if caps_lock:             badges.append(("CAPS ON", COL_TEAL))
    if voice_listening:       badges.append(("MIC ON",  COL_GREEN))
    if len(hand_lms) == 2:    badges.append(("2-HAND",  COL_CYAN))
    for k, (label, color) in enumerate(badges):
        cv2.putText(img, label, (1060, 30 + k * 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)

    # FPS
    now       = time.time()
    fps       = 1.0 / (now - prev_time + 1e-9)
    prev_time = now
    cv2.putText(img, f"FPS:{int(fps)}", (1190, 680),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, COL_GOLD, 2, cv2.LINE_AA)

    cv2.imshow("Virtual Keyboard - Enhanced", img)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
print("[INFO] Exited cleanly.")
# 🤖 AI-Powered Virtual Keyboard

> Type with your hands — no physical keyboard required.  
> Powered by **MediaPipe** · **OpenCV** · **Speech Recognition**

---

## ✨ What Makes This Unique

This isn't just another virtual keyboard demo. It combines four cutting-edge technologies into one seamless hands-free typing experience:

| Feature | Description |
|---|---|
| 🔢 **Full Keyboard** | Number row (0–9) + full QWERTY — everything you need |
| 🎙️ **Voice Input** | Speak a word or phrase — it gets typed instantly |
| 🤟 **Hand Gestures** | Thumbs Up to clear · Peace sign to activate voice |

---

## 📸 Demo

> **How it looks:**

```
┌──────────────────────────────────────────────┐
│  1  2  3  4  5  6  7  8  9  0               │
│  Q  W  E  R  T  Y  U  I  O  P               │
│   A  S  D  F  G  H  J  K  L                 │
│      Z  X  C  V  B  N  M                    │
│  [    SPACE    ] [BACK] [CLEAR] [VOICE]      │
├──────────────────────────────────────────────┤
│ > HELLO WORLD_                               │
└──────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

```
OpenCV          →  Webcam capture, rendering, drawing
MediaPipe       →  21-point hand landmark detection
Gemini API      →  Google's free AI for real-time word prediction
SpeechRecognition → Google Speech-to-Text voice input
NumPy           →  Math + array operations
```

---

## 🖐️ How It Works

### Hand Landmark Detection (MediaPipe)

MediaPipe tracks **21 landmarks** on your hand in real-time:

```
Landmark Points Used:
  4  → Thumb Tip
  8  → Index Finger Tip
 12  → Middle Finger Tip
```

### Click Detection

The distance between **Thumb Tip (4)** and **Index Tip (8)** is calculated:

```python
distance = math.hypot(x2 - x1, y2 - y1)

if distance < 38:
    # Key press registered!
```

### Gesture Controls

| Gesture | Action |
|---|---|
| 👍 Thumbs Up | Clear all typed text |
| ✌️ Peace Sign | Activate voice input mode |

Gesture detection works by reading finger tip vs PIP joint Y-positions.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Webcam

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/shubhamawchare/virtual-keyboard-ai.git
cd virtual-keyboard-ai

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate       # Linux/macOS
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# Note: pyaudio can be tricky on Windows. If it fails:
# pip install pipwin && pipwin install pyaudio
```

### Run

```bash
python virtual_keyboard_ai.py
```

---

## 🎮 Usage Guide

### Typing
1. Hold your hand in front of the webcam
2. Move your **index finger** to hover over a key (it turns green)
3. **Pinch** your thumb and index finger together to press

### AI Predictions
- Start typing a word — after 2+ characters, Gemini suggests 3 completions
- Move your index finger over a prediction bubble and pinch to accept it

### Voice Input
- **✌️ Peace sign gesture** OR tap the **VOICE** button
- Speak clearly — your words appear instantly
- Works for full phrases, not just single words

### Gestures
- **👍 Thumbs Up** → Clears the entire text
- **✌️ Peace Sign** → Activates voice listening

---

## 📁 Project Structure

```
virtual-keyboard-ai/
│
├── virtual_keyboard_ai.py   # Main application
├── requirements.txt          # Python dependencies
├── .env.example              # API key template
├── .gitignore
└── README.md
```

---

## 🔮 Future Improvements

- [ ] **Shift / Caps Lock** — switch between upper and lower case
- [ ] **Symbol keyboard** — `!@#$%^&*()` etc.
- [ ] **Emoji keyboard** — 😊🔥🎉
- [ ] **PyAutoGUI integration** — type directly into any app (Notepad, browser, etc.)
- [ ] **Predictive sentence completion** — full sentence suggestions
- [ ] **Multi-language support** — Hindi, Spanish, etc.
- [ ] **Custom gesture mapping** — define your own shortcuts
- [ ] **Dark/Light theme toggle**
- [ ] **Typing speed tracker** — WPM display

---

## 🤝 Contributing

Pull requests are welcome! For major changes, open an issue first.

1. Fork the repo
2. Create your branch: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [Google MediaPipe](https://mediapipe.dev/) — Hand tracking
- [Google Gemini API](https://aistudio.google.com/) — Free AI word prediction
- [OpenCV](https://opencv.org/) — Computer vision
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) — Voice input

---

# ⚡ NEON SNAKE: Commercial-Level Python & Web Arcade

A triple-A visual upgrade of the classic Snake game. It runs a local Python game server and displays high-fidelity, hardware-accelerated neon visuals in your web browser. 

No virtual environments or external `pip` packages required!

---

## 🎮 Game Controls

| Key | Action |
| :--- | :--- |
| **`W` / `▲ Up Arrow`** | Move Up |
| **`S` / `▼ Down Arrow`** | Move Down |
| **`A` / `◀ Left Arrow`** | Move Left |
| **`D` / `▶ Right Arrow`** | Move Right |
| **`Space` / `Enter`** | Start / Redeploy (on Screensaver or Game Over) |

---

## 🚀 Recommended: Zero-Dependency HD Mode (Python + HTML5)

This version runs a lightweight local python server and opens the game directly in your browser. It offers **60 FPS hardware-accelerated rendering**, high-DPI retina sharpness, Web Audio API bleep synthesizer, particles, and screen shake.

### Run in One Command:
Open your terminal and run:
```bash
python3 main.py
```
*(No installations or virtual environments needed!)*

---

## ⚙️ Fallback: Pygame Desktop Mode (Classic Python)

If you prefer to run the game as a native macOS/Windows window, we've provided `snake.py` which uses `pygame`.

### Setup & Run:
1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the desktop application:
   ```bash
   python3 snake.py
   ```

---

## ✨ Features (HD Mode)
- **High-DPI Retina Rendering:** Ultra-sharp graphics on Mac/PC screen resolutions.
- **Synthwave Theme:** Pulsing background grids, glowing gradients, and custom snake eyes.
- **Liquid Physics Simulation:** Body parts taper down and interpolate smoothly between cells.
- **Web Audio API Synth:** Custom-synthesized retro chimes, bleeps, and crashes.
- **Advanced Screensaver AI:** Watch a smart pathfinding AI play in the background on the start screen.
- **Juicy Game Feel:** Screen shake on eat/collision, trail particles, and floating "+100" text.
